"""
Tests for the Phase 0 grounding audit fixes:
- 0.1 per-collection vector search quotas
- 0.2 deadline rule present in prompts
- 0.3 domain gate wiring (_threshold_domains helper)
- 0.4 court-case citation duty present in prompts
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config.constants import RAG_VECTOR_TOP_K_PER_COLLECTION
from app.prompts.advocate import compose_advocate_prompt
from app.prompts.chat import CHAT_SYSTEM
from app.services.legal_classifier_service import ClassificationResult
from app.services.rag_retrieval_service import (
    RAGRetrievalService,
    _balance_rerank_pool,
    _threshold_domains,
)


def _chunk(chunk_id: str, distance: float, collection: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "content": "c",
        "metadata": {"_collection": collection},
        "distance": distance,
    }


class TestPerCollectionVectorSearch:
    """0.1: each collection is queried separately with its own top-k quota."""

    @pytest.mark.asyncio
    async def test_each_collection_queried_with_own_quota(self):
        chroma = MagicMock()
        chroma.available_collections = ["georgian_laws", "court_practice", "grand_chamber"]
        chroma.vector_search_async = AsyncMock(return_value=[])
        embedding = MagicMock()
        embedding.embed_queries_async = AsyncMock(return_value=[[0.1] * 768])

        svc = RAGRetrievalService(chroma=chroma, embedding_client=embedding)
        await svc._stage_1_vector_search(["query"])

        calls = chroma.vector_search_async.call_args_list
        assert len(calls) == 3
        queried = {
            call.kwargs["collections"][0]: call.kwargs["top_k"] for call in calls
        }
        assert queried == RAG_VECTOR_TOP_K_PER_COLLECTION

    @pytest.mark.asyncio
    async def test_restricted_collections_respected(self):
        chroma = MagicMock()
        chroma.available_collections = ["georgian_laws", "court_practice", "grand_chamber"]
        chroma.vector_search_async = AsyncMock(return_value=[])
        embedding = MagicMock()
        embedding.embed_queries_async = AsyncMock(return_value=[[0.1] * 768])

        svc = RAGRetrievalService(chroma=chroma, embedding_client=embedding)
        await svc._stage_1_vector_search(["query"], collections=["georgian_laws"])

        calls = chroma.vector_search_async.call_args_list
        assert len(calls) == 1
        assert calls[0].kwargs["collections"] == ["georgian_laws"]
        assert calls[0].kwargs["top_k"] == RAG_VECTOR_TOP_K_PER_COLLECTION["georgian_laws"]


class TestBalancedRerankPool:
    """0.1 (continued): statutes must survive into the rerank candidate pool."""

    def test_laws_survive_closer_court_practice(self):
        """150 court chunks all closer than any statute must not evict statutes."""
        court = [_chunk(f"court_{i}", 0.10 + i * 0.001, "court_practice") for i in range(150)]
        laws = [_chunk(f"law_{i}", 0.30 + i * 0.001, "georgian_laws") for i in range(60)]
        merged = sorted(court + laws, key=lambda x: x["distance"])

        pool = _balance_rerank_pool(merged)

        law_count = sum(1 for c in pool if c["metadata"]["_collection"] == "georgian_laws")
        court_count = sum(1 for c in pool if c["metadata"]["_collection"] == "court_practice")
        assert law_count == 50
        assert court_count == 50  # 40 cap + 10 backfill from spare capacity
        assert len(pool) == 100

    def test_leftover_capacity_backfilled(self):
        """With few laws, spare capacity goes to the closest leftovers."""
        court = [_chunk(f"court_{i}", 0.10 + i * 0.001, "court_practice") for i in range(150)]
        laws = [_chunk(f"law_{i}", 0.30, "georgian_laws") for i in range(5)]
        merged = sorted(court + laws, key=lambda x: x["distance"])

        pool = _balance_rerank_pool(merged)

        assert len(pool) == 100
        assert sum(1 for c in pool if c["metadata"]["_collection"] == "georgian_laws") == 5

    def test_small_pool_passes_through(self):
        merged = [_chunk("a", 0.1, "georgian_laws"), _chunk("b", 0.2, "court_practice")]
        assert _balance_rerank_pool(merged) == merged


class TestThresholdDomainWiring:
    """0.3: classification → allowed domains for the threshold gate."""

    def test_confident_classification_gates(self):
        c = ClassificationResult(
            primary="labor", secondary=["civil"], confidence=0.9, reasoning="kw"
        )
        assert _threshold_domains(c) == ["labor", "civil"]

    def test_fallback_classification_injects_no_thresholds(self):
        """Blind fallback (conf ≤ 0.1) → empty allow-list, NOT None. The gate
        stays active and excludes every domain-specific threshold, so a
        low-signal query (e.g. an election-code question) can't be polluted by
        the noisy matcher. Regression for agent-flow probe A3."""
        c = ClassificationResult(
            primary="civil", secondary=[], confidence=0.1, reasoning="fallback"
        )
        assert _threshold_domains(c) == []


class TestPromptGroundingRules:
    """0.2 / 0.4: deadline and court-case-citation duties are in the prompts."""

    def test_chat_system_has_deadline_rule(self):
        assert "DEADLINES" in CHAT_SYSTEM.template
        assert "ვადა" in CHAT_SYSTEM.template

    def test_chat_system_has_court_practice_citation_rule(self):
        assert "COURT PRACTICE CITATIONS" in CHAT_SYSTEM.template
        assert "ას-1280-2019" in CHAT_SYSTEM.template

    def test_advocate_prompt_has_deadline_rule(self):
        prompt = compose_advocate_prompt()
        assert "DEADLINES" in prompt
        assert "ვადა" in prompt

    def test_advocate_prompt_has_court_practice_citation_rule(self):
        prompt = compose_advocate_prompt()
        assert "COURT PRACTICE CITATIONS" in prompt
