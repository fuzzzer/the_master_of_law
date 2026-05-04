"""
Batch embedding processor with sequential requests, caching, and checkpointing.

Designed for gemini-embedding-2's constraints:
- 8,192 token context window PER API call (not per chunk!)
- 10,000,000 input tokens per minute (global)
- 40,000 requests per minute (global)

With legal chunks averaging ~500-2000 tokens, we use batches of 5 chunks
to stay safely under the 8K token limit. At 40K RPM we can easily do
10+ requests per second, finishing ~9,500 chunks in ~3 minutes.

Strategy:
- Sequential batch processing (no complex concurrency needed at 40K RPM)
- Small batches (5 chunks) to fit within 8K token window
- Exponential backoff on 429 with 60-second cooldown
- Per-chunk checkpointing for crash-safe resumability
"""

from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from pipeline.config import settings
from pipeline.embedder.embedding_cache import EmbeddingCache
from pipeline.embedder.vertex_embedder import VertexEmbedder
from pipeline.models.legal_chunk import LegalChunk
from pipeline.utils.logger import get_logger
from pipeline.utils.progress_tracker import ProgressTracker

logger = get_logger(__name__)

# ── Batch sizing ─────────────────────────────────────────
# gemini-embedding-2 has 8,192 token context window per API call.
# Legal chunks average ~500-2000 tokens. 5 chunks × ~1500 avg = ~7500 tokens.
# This keeps us safely under the 8K limit while minimizing API calls.
DEFAULT_BATCH_SIZE = 50

# ── Rate limiting ────────────────────────────────────────
# Actual project quota is limited. 5s between batches avoids 429 bouncing.
# At 50 chunks/batch every 5s = 600 chunks/min → ~16 min for 9,450 chunks.
MIN_DELAY = 5.0
RATE_LIMIT_COOLDOWN = 60.0  # Full minute cooldown on 429

MAX_RETRIES = 5
INITIAL_BACKOFF = 2.0
MAX_BACKOFF = 120.0

# Save checkpoint every N successful batches
CHECKPOINT_EVERY = 20


class BatchEmbedder:
    """
    Process chunks in small sequential batches with caching and checkpointing.

    Designed for gemini-embedding-2's 8K token window and 40K RPM quota.
    Uses batch_size=5 to fit within token limits, processes sequentially
    at ~8 req/sec, finishing ~9,500 chunks in ~3 minutes.
    """

    def __init__(
        self,
        embedder: VertexEmbedder | None = None,
        cache: EmbeddingCache | None = None,
        batch_size: int | None = None,
        requests_per_minute: int | None = None,
    ) -> None:
        self.embedder = embedder or VertexEmbedder()
        self.cache = cache or EmbeddingCache()
        self.batch_size = batch_size or DEFAULT_BATCH_SIZE
        self.rpm = requests_per_minute or settings.embedding_requests_per_minute
        self._tracker = ProgressTracker("embedder")
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._delay = MIN_DELAY

    async def embed_chunks(self, chunks: list[LegalChunk]) -> list[LegalChunk]:
        """
        Generate embeddings for all chunks, skipping cached ones.

        Returns chunks with their `embedding` field populated.
        """
        total = len(chunks)

        # ── Phase 1: Separate cached from uncached ───────────
        uncached_indices: list[int] = []
        cache_hits = 0

        for idx, chunk in enumerate(chunks):
            cached = self.cache.get(chunk.chunk_id, chunk.content_hash or "")
            if cached:
                chunk.embedding = cached
                cache_hits += 1
                self._tracker.mark_completed(chunk.chunk_id)
                continue
            if self._tracker.is_completed(chunk.chunk_id):
                cached = self.cache.get(chunk.chunk_id, chunk.content_hash or "")
                if cached:
                    chunk.embedding = cached
                    cache_hits += 1
                    continue
            uncached_indices.append(idx)

        logger.info(
            "Embedding plan: %d total, %d cached, %d to embed",
            total, cache_hits, len(uncached_indices),
        )

        if not uncached_indices:
            logger.info("All chunks already embedded — nothing to do")
            return chunks

        # ── Phase 2: Create batches ──────────────────────────
        batches: list[list[int]] = []
        for i in range(0, len(uncached_indices), self.batch_size):
            batches.append(uncached_indices[i : i + self.batch_size])

        total_batches = len(batches)
        logger.info(
            "Processing %d chunks in %d batches (size=%d, ~%.0f req/sec)",
            len(uncached_indices), total_batches, self.batch_size,
            1.0 / self._delay,
        )

        # ── Phase 3: Process batches sequentially ────────────
        embedded_count = 0
        failed_count = 0
        start_time = time.monotonic()
        batches_since_checkpoint = 0

        for batch_idx, batch_indices in enumerate(batches):
            texts = [chunks[i].content for i in batch_indices]

            embeddings = await self._embed_with_retry(
                texts, batch_idx + 1, total_batches,
            )

            if embeddings is not None and len(embeddings) == len(batch_indices):
                for idx, emb in zip(batch_indices, embeddings):
                    chunk = chunks[idx]
                    chunk.embedding = emb
                    self.cache.put(chunk.chunk_id, chunk.content_hash or "", emb)
                    self._tracker.mark_completed(chunk.chunk_id)
                    embedded_count += 1
            elif embeddings is not None and len(embeddings) != len(batch_indices):
                logger.error(
                    "Batch %d/%d: got %d embeddings for %d chunks — skipping",
                    batch_idx + 1, total_batches,
                    len(embeddings), len(batch_indices),
                )
                failed_count += len(batch_indices)
            else:
                failed_count += len(batch_indices)

            batches_since_checkpoint += 1

            # Periodic checkpoint & progress
            if batches_since_checkpoint >= CHECKPOINT_EVERY:
                self._tracker.save()
                self.cache.flush()
                batches_since_checkpoint = 0

            if (batch_idx + 1) % 50 == 0 or batch_idx == total_batches - 1:
                elapsed = time.monotonic() - start_time
                rate = embedded_count / elapsed if elapsed > 0 else 0
                logger.info(
                    "Progress: %d/%d batches, %d embedded (%.1f chunks/s), %d failed",
                    batch_idx + 1, total_batches, embedded_count, rate, failed_count,
                )

            # Rate limiting delay between requests
            await asyncio.sleep(self._delay)

        # Final save
        self._tracker.save()
        self.cache.flush()

        elapsed = time.monotonic() - start_time
        rate = embedded_count / elapsed if elapsed > 0 else 0
        logger.info(
            "Embedding complete: %d new (%.1f/s), %d cached, %d failed in %.1fs",
            embedded_count, rate, cache_hits, failed_count, elapsed,
        )
        return chunks

    async def _embed_with_retry(
        self,
        texts: list[str],
        batch_num: int,
        total_batches: int,
    ) -> list[list[float]] | None:
        """
        Embed a batch of texts with retry on transient errors.

        On 429: waits a full minute then retries (quota resets per minute).
        On other errors: exponential backoff.
        """
        backoff = INITIAL_BACKOFF

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                loop = asyncio.get_event_loop()
                embeddings = await loop.run_in_executor(
                    self._executor,
                    lambda t=texts: self.embedder.embed_texts(t),
                )
                # Reset delay on success
                self._delay = MIN_DELAY
                return embeddings

            except Exception as exc:
                error_str = str(exc)
                is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str

                if is_rate_limit:
                    if attempt < MAX_RETRIES:
                        logger.warning(
                            "Batch %d/%d: 429 rate limit (attempt %d/%d), "
                            "cooling down %.0fs...",
                            batch_num, total_batches, attempt, MAX_RETRIES,
                            RATE_LIMIT_COOLDOWN,
                        )
                        await asyncio.sleep(RATE_LIMIT_COOLDOWN)
                        continue
                    else:
                        logger.error(
                            "Batch %d/%d: rate limit exhausted all %d retries",
                            batch_num, total_batches, MAX_RETRIES,
                        )
                        return None

                # Non-rate-limit error
                if attempt < MAX_RETRIES:
                    logger.warning(
                        "Batch %d/%d failed (attempt %d/%d): %s — "
                        "retrying in %.1fs...",
                        batch_num, total_batches, attempt, MAX_RETRIES,
                        error_str[:200], backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF)
                else:
                    logger.error(
                        "Batch %d/%d: all %d attempts failed: %s",
                        batch_num, total_batches, MAX_RETRIES,
                        error_str[:300],
                    )
                    return None

        return None
