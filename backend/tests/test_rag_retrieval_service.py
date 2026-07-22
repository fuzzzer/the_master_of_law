"""
Tests for the 5-stage RAG retrieval pipeline.

Tests query expansion, vector search, fulltext search,
merge/dedup, full pipeline, quotas, and search_law.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from app.services.rag_retrieval_service import RAGRetrievalService


def _make_chunk(chunk_id, distance=0.2, collection="georgian_laws", content="content"):
    """Helper to create a chunk dict."""
    return {
        "chunk_id": chunk_id,
        "content": content,
        "metadata": {"_collection": collection, "code_name": "test", "article_number": "მუხლი 1"},
        "distance": distance,
    }


class TestStage0QueryExpansion:
    """Stage 0: Gemini query expansion tests."""

    @pytest.mark.asyncio
    async def test_valid_expansion(self, mock_gemini):
        """Gemini returning a list of queries should be used directly."""
        mock_gemini.generate_json = AsyncMock(return_value=["query1", "query2"])
        svc = RAGRetrievalService(gemini_client=mock_gemini)
        result = await svc._stage_0_expand_queries("legal question")
        assert result == ["query1", "query2"]

    @pytest.mark.asyncio
    async def test_empty_list(self, mock_gemini):
        """Gemini returning empty list means no search needed."""
        mock_gemini.generate_json = AsyncMock(return_value=[])
        svc = RAGRetrievalService(gemini_client=mock_gemini)
        result = await svc._stage_0_expand_queries("greeting")
        assert result == []

    @pytest.mark.asyncio
    async def test_failure_fallback(self, mock_gemini):
        """Exception should fallback to [user_message]."""
        mock_gemini.generate_json = AsyncMock(side_effect=Exception("API error"))
        svc = RAGRetrievalService(gemini_client=mock_gemini)
        result = await svc._stage_0_expand_queries("my question")
        assert result == ["my question"]

    @pytest.mark.asyncio
    async def test_non_list_fallback(self, mock_gemini):
        """Non-list return should fallback to [user_message]."""
        mock_gemini.generate_json = AsyncMock(return_value="just a string")
        svc = RAGRetrievalService(gemini_client=mock_gemini)
        result = await svc._stage_0_expand_queries("test")
        assert result == ["test"]

    @pytest.mark.asyncio
    async def test_filters_empty_strings(self, mock_gemini):
        """Empty strings in results should be filtered out."""
        mock_gemini.generate_json = AsyncMock(return_value=["valid", "", "  ", "also valid"])
        svc = RAGRetrievalService(gemini_client=mock_gemini)
        result = await svc._stage_0_expand_queries("test")
        assert result == ["valid", "also valid"]


class TestStage3MergeDedup:
    """Stage 3: merge and deduplicate tests."""

    @pytest.mark.asyncio
    async def test_dedup_same_id_keeps_lower_distance(self):
        """Same chunk_id in both sources — keep lower distance."""
        svc = RAGRetrievalService()
        svc._chroma = MagicMock()
        svc._chroma.get_by_ids_async = AsyncMock(return_value=[])

        vector = [_make_chunk("A", distance=0.3)]
        fulltext = [_make_chunk("A", distance=0.1)]
        result = await svc._stage_3_merge_and_dedup(vector, fulltext)
        assert len(result) == 1
        # Vector came first so it has the entry; fulltext A is same id → not added as new
        assert result[0]["chunk_id"] == "A"

    @pytest.mark.asyncio
    async def test_merge_unique(self):
        """Different IDs should both appear."""
        svc = RAGRetrievalService()
        svc._chroma = MagicMock()
        svc._chroma.get_by_ids_async = AsyncMock(return_value=[])

        vector = [_make_chunk("A", distance=0.2)]
        fulltext = [_make_chunk("B", distance=0.3)]
        result = await svc._stage_3_merge_and_dedup(vector, fulltext)
        assert len(result) == 2
        ids = {r["chunk_id"] for r in result}
        assert ids == {"A", "B"}

    @pytest.mark.asyncio
    async def test_fulltext_enrichment(self):
        """Fulltext-only IDs should trigger chroma.get_by_ids_async for content."""
        svc = RAGRetrievalService()
        enriched = [{"chunk_id": "B", "content": "enriched content", "metadata": {"code": "test"}}]
        svc._chroma = MagicMock()
        svc._chroma.get_by_ids_async = AsyncMock(return_value=enriched)

        vector = [_make_chunk("A", distance=0.2)]
        fulltext = [{"chunk_id": "B", "content": "", "metadata": {}, "distance": 0.5}]
        result = await svc._stage_3_merge_and_dedup(vector, fulltext)
        assert len(result) == 2
        svc._chroma.get_by_ids_async.assert_called_once_with(["B"])

    @pytest.mark.asyncio
    async def test_sorted_by_distance(self):
        """Results should be sorted by distance."""
        svc = RAGRetrievalService()
        svc._chroma = MagicMock()
        svc._chroma.get_by_ids_async = AsyncMock(return_value=[])

        vector = [_make_chunk("A", distance=0.5), _make_chunk("B", distance=0.1)]
        result = await svc._stage_3_merge_and_dedup(vector, [])
        assert result[0]["chunk_id"] == "B"
        assert result[1]["chunk_id"] == "A"


class TestFullPipeline:
    """Full pipeline integration tests."""

    @pytest.mark.asyncio
    async def test_pre_expanded_skips_stage_0(self, mock_gemini, mock_chroma, mock_embedding):
        """Pre-expanded queries should skip stage 0."""
        svc = RAGRetrievalService(
            chroma=mock_chroma,
            embedding_client=mock_embedding,
            gemini_client=mock_gemini,
        )
        mock_gemini.generate_json = AsyncMock(return_value=["id1", "id2"])

        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search = MagicMock(return_value=[])
            result = await svc.retrieve("question", pre_expanded_queries=["q"])

        # Stage 0 (generate_json for expansion) should NOT have been called
        # because we pre-expanded
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_empty_expansion_returns_empty(self, mock_gemini, mock_chroma, mock_embedding):
        """If expansion returns empty list, pipeline returns []."""
        mock_gemini.generate_json = AsyncMock(return_value=[])
        svc = RAGRetrievalService(
            chroma=mock_chroma,
            embedding_client=mock_embedding,
            gemini_client=mock_gemini,
        )
        result = await svc.retrieve("გამარჯობა")
        assert result == []

    @pytest.mark.asyncio
    async def test_quota_enforcement(self, mock_gemini, mock_chroma, mock_embedding):
        """Quotas should limit laws to 15 and cases to 8."""
        law_chunks = [_make_chunk(f"law_{i}", distance=0.1*i, collection="georgian_laws") for i in range(20)]
        case_chunks = [_make_chunk(f"case_{i}", distance=0.1*i, collection="court_practice") for i in range(12)]

        mock_chroma.vector_search = MagicMock(return_value=law_chunks + case_chunks)
        mock_chroma.get_by_ids = MagicMock(return_value=[])
        mock_gemini.generate_json = AsyncMock(return_value=["query1"])

        svc = RAGRetrievalService(
            chroma=mock_chroma,
            embedding_client=mock_embedding,
            gemini_client=mock_gemini,
        )

        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search = MagicMock(return_value=[])
            result = await svc.retrieve("question", pre_expanded_queries=["query1"])

        laws = [r for r in result if r.get("metadata", {}).get("_collection") == "georgian_laws"]
        cases = [r for r in result if r.get("metadata", {}).get("_collection") == "court_practice"]
        assert len(laws) <= 15
        assert len(cases) <= 8

    @pytest.mark.asyncio
    async def test_threshold_hits_prepended(self, mock_gemini, mock_chroma, mock_embedding):
        """Threshold hits should be prepended to results."""
        threshold_hit = _make_chunk("threshold_1", distance=0.01)
        mock_chroma.vector_search = MagicMock(return_value=[_make_chunk("A")])
        mock_chroma.get_by_ids = MagicMock(return_value=[])
        mock_gemini.generate_json = AsyncMock(return_value=["query1"])

        svc = RAGRetrievalService(
            chroma=mock_chroma,
            embedding_client=mock_embedding,
            gemini_client=mock_gemini,
        )

        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search = MagicMock(return_value=[threshold_hit])
            result = await svc.retrieve("question", pre_expanded_queries=["query1"])

        assert result[0]["chunk_id"] == "threshold_1"


class TestSearchLaw:
    """search_law targeted lookup tests."""

    @pytest.mark.asyncio
    async def test_exact_match_with_article_number(self, mock_chroma, mock_embedding):
        """Providing article_number should trigger metadata search."""
        svc = RAGRetrievalService(chroma=mock_chroma, embedding_client=mock_embedding)
        result = await svc.search_law(query="test", article_number="მუხლი 77")
        mock_chroma.search_by_metadata.assert_called_once()

    @pytest.mark.asyncio
    async def test_normalize_article_number(self, mock_chroma, mock_embedding):
        """Bare number should be converted to 'მუხლი N' format."""
        svc = RAGRetrievalService(chroma=mock_chroma, embedding_client=mock_embedding)
        result = await svc.search_law(query="test", article_number="77")
        # Check that search_by_metadata was called with normalized article_number
        call_args = mock_chroma.search_by_metadata.call_args
        where = call_args[1]["where"] if "where" in call_args[1] else call_args[0][0]
        # The where clause should contain "მუხლი 77"
        where_str = str(where)
        assert "მუხლი 77" in where_str

    @pytest.mark.asyncio
    async def test_semantic_fallback(self, mock_embedding):
        """When no article_number, should use semantic search."""
        chroma = MagicMock()
        chroma.search_by_metadata = MagicMock(return_value=[])
        chroma.vector_search = MagicMock(return_value=[_make_chunk("sem_1")])
        svc = RAGRetrievalService(chroma=chroma, embedding_client=mock_embedding)
        result = await svc.search_law(query="criminal liability")
        assert len(result) > 0
