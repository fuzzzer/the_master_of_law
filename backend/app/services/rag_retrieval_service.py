"""
5-Stage RAG Retrieval Service.

Pipeline:
    User Message
      -> [Stage 0] AI Query Expansion
      -> [Stage 1] Multi-Query Vector Search
      -> [Stage 2] Multi-Query Full-Text Search
      -> [Stage 3] Merge and Deduplicate
      -> [Stage 4] Gemini Rerank
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from app.config.constants import (
    RAG_FULLTEXT_SEARCH_TOP_K,
    RAG_QUERY_EXPANSION_COUNT,
    RAG_RERANK_POOL_PER_COLLECTION,
    RAG_RERANK_TOP_K,
    RAG_VECTOR_SEARCH_TOP_K,
    RAG_VECTOR_TOP_K_PER_COLLECTION,
)
from app.config.settings import settings
from app.integrations.chroma_client import ChromaClient, get_chroma_client
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.integrations.vertex_embedding_client import (
    VertexEmbeddingClient,
    get_embedding_client,
)
from app.prompts.rag_pipeline import QUERY_EXPANSION, RERANK
from app.services.legal_classifier_service import ClassificationResult, KeywordClassifier
from app.services.threshold_service import get_threshold_service
from app.services.trace_service import record_step
from app.utils.logger import get_logger
from app.services.model_config_service import cheap_model, strong_model

logger = get_logger(__name__)


def _balance_rerank_pool(merged: list[dict], capacity: int = 100) -> list[dict]:
    """Select the rerank candidate pool with per-collection caps.

    ``merged`` is distance-sorted; each collection keeps its closest chunks up
    to its cap, then any remaining capacity is filled with the closest
    leftovers regardless of collection.
    """
    pools: dict[str, list[dict]] = {}
    for item in merged:
        col = (item.get("metadata") or {}).get("_collection", "")
        pools.setdefault(col, []).append(item)

    selected: list[dict] = []
    leftovers: list[dict] = []
    for col, items in pools.items():
        cap = RAG_RERANK_POOL_PER_COLLECTION.get(col, 10)
        selected.extend(items[:cap])
        leftovers.extend(items[cap:])

    remaining = capacity - len(selected)
    if remaining > 0 and leftovers:
        leftovers.sort(key=lambda x: x.get("distance", 1))
        selected.extend(leftovers[:remaining])

    selected.sort(key=lambda x: x.get("distance", 1))
    return selected[:capacity]


def _threshold_domains(classification: ClassificationResult) -> list[str]:
    """Domains allowed for threshold injection.

    A confidence at or below 0.1 is the classifier's blind fallback
    ("civil" by default) — the domain is effectively unknown. Returning an
    empty list (NOT None) keeps the gate ACTIVE and excludes every
    domain-specific threshold: when we can't tell the domain, injecting a
    domain-scoped numeric threshold can only pollute the prompt (verified: no
    golden question that lands at ≤0.1 has any legitimate threshold hit, and
    the noisy matcher otherwise leaks e.g. criminal monetary thresholds into an
    election-code question). Legitimate threshold questions (speeding fine, drug
    quantities) classify with confidence > 0.1 and keep their thresholds.
    """
    if classification.confidence <= 0.1:
        return []
    return [classification.primary, *classification.secondary]


def _hit_summary(hits: list[dict], limit: int = 200) -> list[dict]:
    """Compact per-hit view for trace steps (full content is traced only for final chunks)."""
    summary = []
    for h in hits[:limit]:
        meta = h.get("metadata") or {}
        distance = h.get("distance")
        summary.append({
            "chunk_id": h.get("chunk_id"),
            "distance": round(float(distance), 4) if distance is not None else None,
            "collection": meta.get("_collection", ""),
            "code_name": meta.get("code_name", ""),
            "article_number": meta.get("article_number", ""),
            "source": h.get("source", ""),
            "query_index": h.get("query_index"),
        })
    return summary


class RAGRetrievalService:
    """Implements the 5-stage RAG retrieval pipeline."""

    def __init__(
        self,
        chroma: ChromaClient | None = None,
        embedding_client: VertexEmbeddingClient | None = None,
        gemini_client: VertexAIClient | None = None,
    ) -> None:
        self._chroma = chroma
        self._embedding_client = embedding_client
        self._gemini = gemini_client
        self._article_index: dict[str, Any] | None = None
        # Cache of pre-stringified, lowercased article text keyed by article id.
        # Built once so the full-text search loop does not run json.dumps on
        # every query (15k entries × up to 8 queries = 120k dumps per request).
        self._article_text_cache: dict[str, str] | None = None

    @property
    def chroma(self) -> ChromaClient:
        if self._chroma is None:
            self._chroma = get_chroma_client()
        return self._chroma

    @property
    def embedding_client(self) -> VertexEmbeddingClient:
        if self._embedding_client is None:
            self._embedding_client = get_embedding_client()
        return self._embedding_client

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def retrieve(
        self,
        user_message: str,
        top_k: int = RAG_RERANK_TOP_K,
        collections: list[str] | None = None,
        pre_expanded_queries: list[str] | None = None,
    ) -> list[dict]:
        """Run the full 5-stage RAG pipeline.

        Parameters
        ----------
        user_message : str
            The user's legal question.
        top_k : int
            Max results after reranking.
        collections : list[str] | None
            Which ChromaDB collections to search. None = all available.
        pre_expanded_queries : list[str] | None
            Pre-planned search queries from the agent pipeline. When provided,
            Stage 0 (query expansion) is skipped to avoid double-expansion.
        """
        logger.info(
            "rag_pipeline_start",
            message_length=len(user_message),
            collections=collections,
        )

        if pre_expanded_queries:
            expanded = pre_expanded_queries
            logger.info("rag_stage_0_skipped", query_count=len(expanded), reason="pre_expanded")
        else:
            expanded = await self._stage_0_expand_queries(user_message)
            logger.info("rag_stage_0_done", query_count=len(expanded))

        record_step(
            "rag_query_expansion",
            input_message=user_message,
            expanded_by="agent_planner" if pre_expanded_queries else "gemini_flash",
            queries=expanded,
        )

        if not expanded:
            logger.info("rag_pipeline_skipped", reason="no_search_needed")
            record_step("rag_skipped", reason="no_search_needed")
            return []

        vector_hits = await self._stage_1_vector_search(expanded, collections=collections)
        logger.info("rag_stage_1_done", hit_count=len(vector_hits))
        per_collection_counts: dict[str, int] = {}
        for h in vector_hits:
            col = (h.get("metadata") or {}).get("_collection", "")
            per_collection_counts[col] = per_collection_counts.get(col, 0) + 1
        record_step(
            "rag_vector_search",
            collections=collections or "all",
            embedding_model=settings.embedding_model,
            hit_count=len(vector_hits),
            per_collection_counts=per_collection_counts,
            hits=_hit_summary(vector_hits),
        )

        fulltext_hits = await self._stage_2_fulltext_search(expanded)
        logger.info("rag_stage_2_done", hit_count=len(fulltext_hits))
        record_step(
            "rag_fulltext_search",
            hit_count=len(fulltext_hits),
            hits=_hit_summary(fulltext_hits),
        )

        merged = await self._stage_3_merge_and_dedup(vector_hits, fulltext_hits)
        logger.info("rag_stage_3_done", merged_count=len(merged))
        record_step(
            "rag_merge_dedup",
            merged_count=len(merged),
            top_chunk_ids=[m.get("chunk_id") for m in merged[:100]],
        )

        if len(merged) > top_k:
            # We send top_k (which is now larger, e.g. 35) to Gemini for reranking.
            # The candidate pool is balanced per collection first — otherwise the
            # global distance sort fills it with court practice before statutes.
            rerank_pool = _balance_rerank_pool(merged)
            pool_counts: dict[str, int] = {}
            for item in rerank_pool:
                col = (item.get("metadata") or {}).get("_collection", "")
                pool_counts[col] = pool_counts.get(col, 0) + 1
            reranked = await self._stage_4_rerank(user_message, rerank_pool, top_k)
            record_step(
                "rag_rerank",
                rerank_model=await cheap_model(),
                candidate_count=len(merged),
                pool_per_collection=pool_counts,
                selected_order=[r.get("chunk_id") for r in reranked],
            )
        else:
            reranked = merged
            record_step("rag_rerank", skipped=True, reason=f"only {len(merged)} candidates (<= top_k {top_k})")

        # Step 4.5: Enforce strict quotas for Laws vs Cases
        from app.config.constants import RAG_LAWS_QUOTA, RAG_CASES_QUOTA
        
        final_laws = []
        final_cases = []
        final_others = []

        for item in reranked:
            # Safely get collection from metadata
            col = item.get("metadata", {}).get("_collection")
            if col == "georgian_laws":
                if len(final_laws) < RAG_LAWS_QUOTA:
                    final_laws.append(item)
            elif col in ("court_practice", "grand_chamber"):
                if len(final_cases) < RAG_CASES_QUOTA:
                    final_cases.append(item)
            else:
                final_others.append(item)
                
        reranked = final_laws + final_cases + final_others

        # Step 5: Direct lookup for exact tables (bypassing RAG fuzziness),
        # gated by the keyword-classified legal domain so e.g. criminal
        # thresholds are never injected into a labor-law prompt.
        domain_result = KeywordClassifier().classify(user_message)
        threshold_hits = get_threshold_service().search(
            user_message, query_domains=_threshold_domains(domain_result)
        )
        if threshold_hits:
            # Add them to the front of the results
            reranked = threshold_hits + [r for r in reranked if r["chunk_id"] not in {t["chunk_id"] for t in threshold_hits}]

        logger.info("rag_pipeline_done", result_count=len(reranked))
        record_step(
            "rag_final_selection",
            result_count=len(reranked),
            threshold_hits=len(threshold_hits) if threshold_hits else 0,
            chunks=[
                {
                    "chunk_id": c.get("chunk_id"),
                    "collection": (c.get("metadata") or {}).get("_collection", ""),
                    "code_name": (c.get("metadata") or {}).get("code_name", ""),
                    "article_number": (c.get("metadata") or {}).get("article_number", ""),
                    "article_title": (c.get("metadata") or {}).get("article_title", ""),
                    "article_url": (c.get("metadata") or {}).get("article_url", ""),
                    "distance": c.get("distance"),
                    "content": c.get("content", ""),
                }
                for c in reranked
            ],
        )
        return reranked

    async def _stage_0_expand_queries(self, user_message: str) -> list[str]:
        """Stage 0: Use Gemini to expand user message into multiple search queries."""
        prompt = QUERY_EXPANSION.render(
            count=RAG_QUERY_EXPANSION_COUNT,
            user_message=user_message,
        )
        try:
            queries = await self.gemini.generate_json(
                prompt=prompt,
                temperature=QUERY_EXPANSION.temperature,
                model_name=await cheap_model(),
            )
            if isinstance(queries, list):
                # If the AI explicitly returned an empty list, it means no search is needed
                if not queries:
                    return []
                return [q for q in queries if isinstance(q, str) and q.strip()]
            return [user_message]
        except Exception as e:
            logger.error("query_expansion_failed", error=str(e))
            return [user_message]

    async def _stage_1_vector_search(
        self,
        queries: list[str],
        collections: list[str] | None = None,
    ) -> list[dict]:
        """Stage 1: Embed queries and search ChromaDB by vector similarity.

        Each collection is queried separately with its own top-k quota
        (RAG_VECTOR_TOP_K_PER_COLLECTION) so that the large court_practice
        collection cannot crowd statutes out of a shared distance-sorted pool.
        """
        all_hits: list[dict] = []
        try:
            embeddings = await self.embedding_client.embed_queries_async(queries)
        except Exception:
            embeddings = []
            for q in queries:
                try:
                    embeddings.append(await self.embedding_client.embed_query_async(q))
                except Exception:
                    pass
        target_collections = collections or self.chroma.available_collections
        for i, emb in enumerate(embeddings):
            for col_name in target_collections:
                per_k = RAG_VECTOR_TOP_K_PER_COLLECTION.get(
                    col_name, RAG_VECTOR_SEARCH_TOP_K
                )
                hits = await self.chroma.vector_search_async(
                    query_embedding=emb,
                    top_k=per_k,
                    collections=[col_name],
                )
                for h in hits:
                    h["source"] = "vector"
                    h["query_index"] = i
                all_hits.extend(hits)
        return all_hits

    async def _stage_2_fulltext_search(self, queries: list[str]) -> list[dict]:
        """Stage 2: Keyword-based full-text search against article index.

        Offloaded to a worker thread because scoring tokenises every cached
        article string per query; running it inline would block the event loop.
        """
        return await asyncio.to_thread(self._sync_fulltext_search, queries)

    def _sync_fulltext_search(self, queries: list[str]) -> list[dict]:
        """Synchronous full-text scoring over the cached article text."""
        text_cache = self._load_article_text_cache()
        if not text_cache:
            return []

        all_hits: list[dict] = []
        for qi, query in enumerate(queries):
            tokens = query.lower().split()
            scored: list[tuple[str, float]] = []

            # Helper to calculate score with basic Georgian stemming
            def get_score(text: str) -> float:
                s = 0.0
                for t in tokens:
                    if len(t) < 3: continue
                    if t in text: s += 1.0
                    elif len(t) >= 5 and t[:4] in text: s += 0.8
                return s

            # Search articles against the pre-stringified, lowercased cache
            for aid, text in text_cache.items():
                score = get_score(text)
                if score > 0:
                    scored.append((aid, score))

            scored.sort(key=lambda x: x[1], reverse=True)
            for aid, score in scored[:RAG_FULLTEXT_SEARCH_TOP_K]:
                all_hits.append({
                    "chunk_id": aid, "content": "", "metadata": {},
                    "distance": 1.0 - score / max(len(tokens), 1),
                    "source": "fulltext", "query_index": qi,
                })
        return all_hits

    def _load_article_text_cache(self) -> dict[str, str]:
        """Build (once) and return the stringified, lowercased article index.

        json.dumps is run a single time per article at first use instead of on
        every query, eliminating the repeated serialisation in the hot path.
        """
        if self._article_text_cache is not None:
            return self._article_text_cache
        index = self._load_article_index()
        self._article_text_cache = {
            aid: (
                json.dumps(data, ensure_ascii=False).lower()
                if isinstance(data, dict)
                else str(data).lower()
            )
            for aid, data in index.items()
        }
        return self._article_text_cache

    def _load_article_index(self) -> dict[str, Any]:
        """Load the pre-built article index from disk."""
        if self._article_index is not None:
            return self._article_index
        path = Path(settings.chroma_persist_dir).parent / "georgian_laws" / "index" / "article_index.json"
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._article_index = json.load(f)
            return self._article_index
        except Exception:
            return {}

    async def _stage_3_merge_and_dedup(
        self,
        vector_hits: list[dict],
        fulltext_hits: list[dict],
    ) -> list[dict]:
        """Stage 3: Merge vector and full-text hits, deduplicate by chunk_id."""
        seen: dict[str, dict] = {}
        for h in vector_hits:
            cid = h["chunk_id"]
            if cid not in seen or h.get("distance", 1) < seen[cid].get("distance", 1):
                seen[cid] = h
        ft_ids: list[str] = []
        for h in fulltext_hits:
            cid = h["chunk_id"]
            if cid not in seen:
                ft_ids.append(cid)
                seen[cid] = h
        if ft_ids:
            try:
                for item in await self.chroma.get_by_ids_async(ft_ids):
                    cid = item["chunk_id"]
                    if cid in seen:
                        seen[cid]["content"] = item.get("content", "")
                        seen[cid]["metadata"] = item.get("metadata", {})
            except Exception:
                pass
        return sorted(seen.values(), key=lambda x: x.get("distance", 1))

    async def _stage_4_rerank(
        self,
        user_message: str,
        candidates: list[dict],
        top_k: int,
    ) -> list[dict]:
        """Stage 4: Use Gemini to select the most relevant chunks."""
        compact = [
            {
                "chunk_id": c["chunk_id"],
                "preview": c.get("content", "")[:500],
                "code": (c.get("metadata") or {}).get("code_name", ""),
                "article": (c.get("metadata") or {}).get("article_number", ""),
                "title": (c.get("metadata") or {}).get("article_title", ""),
            }
            for c in candidates[:100]
        ]
        prompt = RERANK.render(
            top_k=top_k,
            user_message=user_message,
            chunks_json=json.dumps(compact, ensure_ascii=False),
        )
        try:
            ids = await self.gemini.generate_json(
                prompt=prompt,
                temperature=RERANK.temperature,
                model_name=await cheap_model(),
            )
            if isinstance(ids, list):
                lookup = {c["chunk_id"]: c for c in candidates}
                result = [lookup[i] for i in ids if i in lookup]
                if len(result) < top_k:
                    for c in candidates:
                        if c["chunk_id"] not in {r["chunk_id"] for r in result}:
                            result.append(c)
                            if len(result) >= top_k:
                                break
                return result
            return candidates[:top_k]
        except Exception:
            return candidates[:top_k]


    async def search_law(
        self,
        query: str,
        article_number: str | None = None,
        code_name: str | None = None,
    ) -> list[dict]:
        """Targeted law lookup for AI tool use.

        Strategy:
        1. If both code_name and article_number are given → exact metadata match (fast, precise).
        2. If only article_number → metadata match across all codes.
        3. Always supplement with a semantic search on the query for broader coverage.

        Parameters
        ----------
        query : str
            Natural-language description of what law to find (always required for semantic pass).
        article_number : str | None
            e.g. "მუხლი 77" — if provided, attempts direct metadata lookup first.
        code_name : str | None
            e.g. "საქართველოს სისხლის სამართლის საპროცესო კოდექსი"
        """
        results: list[dict] = []
        seen_ids: set[str] = set()

        # ── Pass 1: Exact metadata match ─────────────────────
        if article_number:
            # Normalise: ensure "მუხლი " prefix
            if not article_number.startswith("მუხლი"):
                article_number = f"მუხლი {article_number.strip()}"

            where: dict = {"article_number": {"$eq": article_number}}
            if code_name:
                # Try full name first; if empty, also try normalised (strip prefix)
                full_name = code_name if code_name.startswith("საქართველოს") else f"საქართველოს {code_name}"
                # ChromaDB $and requires a list
                where = {"$and": [
                    {"article_number": {"$eq": article_number}},
                    {"$or": [
                        {"code_name": {"$eq": full_name}},
                        {"code_name": {"$eq": code_name}},
                    ]},
                ]}

            exact = self.chroma.search_by_metadata(
                where=where,
                collections=["georgian_laws"],
                limit=10,
            )
            for hit in exact:
                cid = hit["chunk_id"]
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    results.append(hit)

        # ── Pass 2: Semantic search on query ──────────────────
        # Always run to catch cases where exact match failed or query adds context
        try:
            embedding = self.embedding_client.embed_query(query)
            semantic_hits = self.chroma.vector_search(
                query_embedding=embedding,
                top_k=10,
                collections=["georgian_laws"],
            )
            for hit in semantic_hits:
                cid = hit["chunk_id"]
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    results.append(hit)
        except Exception as e:
            logger.warning("search_law_semantic_failed", error=str(e))

        logger.info("search_law_done", exact=len(results), query=query[:60])
        return results[:15]


_rag_service: RAGRetrievalService | None = None

def get_rag_service() -> RAGRetrievalService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGRetrievalService()
    return _rag_service
