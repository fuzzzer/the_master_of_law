"""
Batch embedding processor with rate limiting, caching, and checkpointing.
"""

from __future__ import annotations

import asyncio
import time

from pipeline.config import settings
from pipeline.embedder.embedding_cache import EmbeddingCache
from pipeline.embedder.vertex_embedder import VertexEmbedder
from pipeline.models.legal_chunk import LegalChunk
from pipeline.utils.logger import get_logger
from pipeline.utils.progress_tracker import ProgressTracker

logger = get_logger(__name__)


class BatchEmbedder:
    """
    Process chunks in batches with rate limiting and checkpoint support.

    - Batch size: configurable (default 100, Vertex AI max 250)
    - Rate limit: max N requests/minute
    - Caching: skip chunks whose content hasn't changed
    - Checkpointing: save progress every batch
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
        self.batch_size = batch_size or settings.embedding_batch_size
        self.rpm = requests_per_minute or settings.embedding_requests_per_minute
        self._tracker = ProgressTracker("embedder")
        self._request_times: list[float] = []

    async def embed_chunks(self, chunks: list[LegalChunk]) -> list[LegalChunk]:
        """
        Generate embeddings for all chunks, using cache and checkpoints.

        Returns the chunks with their `embedding` field populated.
        """
        total = len(chunks)
        embedded_count = 0
        cache_hits = 0

        for i in range(0, total, self.batch_size):
            batch = chunks[i : i + self.batch_size]
            texts_to_embed: list[str] = []
            indices_to_embed: list[int] = []

            for j, chunk in enumerate(batch):
                # Check checkpoint
                if self._tracker.is_completed(chunk.chunk_id):
                    # Try to load from cache
                    cached = self.cache.get(
                        chunk.chunk_id, chunk.content_hash or "",
                    )
                    if cached:
                        chunk.embedding = cached
                        cache_hits += 1
                        continue

                # Check cache
                cached = self.cache.get(
                    chunk.chunk_id, chunk.content_hash or "",
                )
                if cached:
                    chunk.embedding = cached
                    cache_hits += 1
                    self._tracker.mark_completed(chunk.chunk_id)
                    continue

                texts_to_embed.append(chunk.content)
                indices_to_embed.append(i + j)

            # Embed the uncached texts
            if texts_to_embed:
                await self._rate_limit()
                try:
                    embeddings = self.embedder.embed_texts(
                        texts_to_embed,
                        task_type="RETRIEVAL_DOCUMENT",
                    )
                    for idx, emb in zip(indices_to_embed, embeddings):
                        chunk = chunks[idx]
                        chunk.embedding = emb
                        self.cache.put(
                            chunk.chunk_id,
                            chunk.content_hash or "",
                            emb,
                        )
                        self._tracker.mark_completed(chunk.chunk_id)
                        embedded_count += 1
                except Exception as exc:
                    for idx in indices_to_embed:
                        self._tracker.mark_failed(
                            chunks[idx].chunk_id, str(exc),
                        )
                    logger.error(
                        "Batch %d-%d failed: %s", i, i + len(batch), exc,
                    )

            # Checkpoint every batch
            self._tracker.save()
            self.cache.flush()

            logger.info(
                "Embedding progress: %d/%d (cache hits: %d)",
                i + len(batch), total, cache_hits,
            )

        logger.info(
            "Embedding complete: %d new, %d cached, %d failed",
            embedded_count, cache_hits, self._tracker.failed_count,
        )
        return chunks

    async def _rate_limit(self) -> None:
        """Enforce the requests-per-minute limit."""
        now = time.monotonic()
        # Remove requests older than 60 seconds
        self._request_times = [
            t for t in self._request_times if now - t < 60
        ]
        if len(self._request_times) >= self.rpm:
            wait = 60 - (now - self._request_times[0])
            if wait > 0:
                logger.debug("Rate limit: sleeping %.1fs", wait)
                await asyncio.sleep(wait)
        self._request_times.append(time.monotonic())
