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

import json
from pathlib import Path
from typing import Any

from app.config.constants import (
    RAG_FULLTEXT_SEARCH_TOP_K,
    RAG_QUERY_EXPANSION_COUNT,
    RAG_RERANK_TOP_K,
    RAG_VECTOR_SEARCH_TOP_K,
)
from app.config.settings import settings
from app.integrations.chroma_client import ChromaClient, get_chroma_client
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.integrations.vertex_embedding_client import (
    VertexEmbeddingClient,
    get_embedding_client,
)
from app.prompts.rag_pipeline import QUERY_EXPANSION, RERANK
from app.services.threshold_service import get_threshold_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        """
        logger.info(
            "rag_pipeline_start",
            message_length=len(user_message),
            collections=collections,
        )

        expanded = await self._stage_0_expand_queries(user_message)
        logger.info("rag_stage_0_done", query_count=len(expanded))

        vector_hits = await self._stage_1_vector_search(expanded, collections=collections)
        logger.info("rag_stage_1_done", hit_count=len(vector_hits))

        fulltext_hits = self._stage_2_fulltext_search(expanded)
        logger.info("rag_stage_2_done", hit_count=len(fulltext_hits))

        merged = self._stage_3_merge_and_dedup(vector_hits, fulltext_hits)
        logger.info("rag_stage_3_done", merged_count=len(merged))

        if len(merged) > top_k:
            # We send top_k (which is now larger, e.g. 35) to Gemini for reranking
            reranked = await self._stage_4_rerank(user_message, merged, top_k)
        else:
            reranked = merged

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

        # Step 5: Direct lookup for exact tables (bypassing RAG fuzziness)
        threshold_hits = get_threshold_service().search(user_message)
        if threshold_hits:
            # Add them to the front of the results
            reranked = threshold_hits + [r for r in reranked if r["chunk_id"] not in {t["chunk_id"] for t in threshold_hits}]

        logger.info("rag_pipeline_done", result_count=len(reranked))
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
                model_name=settings.gemini_chat_model,
            )
            if isinstance(queries, list):
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
        """Stage 1: Embed queries and search ChromaDB by vector similarity."""
        all_hits: list[dict] = []
        try:
            embeddings = self.embedding_client.embed_queries(queries)
        except Exception:
            embeddings = []
            for q in queries:
                try:
                    embeddings.append(self.embedding_client.embed_query(q))
                except Exception:
                    pass
        for i, emb in enumerate(embeddings):
            hits = self.chroma.vector_search(
                query_embedding=emb,
                top_k=RAG_VECTOR_SEARCH_TOP_K,
                collections=collections,
            )
            for h in hits:
                h["source"] = "vector"
                h["query_index"] = i
            all_hits.extend(hits)
        return all_hits

    def _stage_2_fulltext_search(self, queries: list[str]) -> list[dict]:
        """Stage 2: Keyword-based full-text search against article index."""
        index = self._load_article_index()
        if not index:
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
                
            # Search articles
            for aid, data in index.items():
                text = json.dumps(data, ensure_ascii=False).lower() if isinstance(data, dict) else str(data).lower()
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

    def _stage_3_merge_and_dedup(
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
                for item in self.chroma.get_by_ids(ft_ids):
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
                "preview": c.get("content", "")[:300],
                "code": c.get("metadata", {}).get("code_name", ""),
                "article": c.get("metadata", {}).get("article_number", ""),
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
                model_name=settings.gemini_chat_model,
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


_rag_service: RAGRetrievalService | None = None

def get_rag_service() -> RAGRetrievalService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGRetrievalService()
    return _rag_service
