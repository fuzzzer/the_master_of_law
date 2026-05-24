"""
RAG pipeline edge-case tests.

Tests actual logic branches in the retrieval pipeline:
- Quota enforcement at exact boundaries
- Merge/dedup distance preservation
- Threshold prepend deduplication
- search_law article number normalization
- Graceful degradation when stages fail

These are unit tests — all external dependencies (Gemini, ChromaDB, embeddings)
are mocked. The point is testing the *logic*, not the infrastructure.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.rag_retrieval_service import RAGRetrievalService


# ── Test Data Builders ───────────────────────────────────────

def _law_chunk(chunk_id: str, distance: float = 0.5, content: str = "law text") -> dict:
    """Build a law chunk with georgian_laws metadata."""
    return {
        "chunk_id": chunk_id,
        "content": content,
        "metadata": {
            "_collection": "georgian_laws",
            "code_name": "საქართველოს სისხლის სამართლის კოდექსი",
            "article_number": f"მუხლი {chunk_id.split('_')[-1]}",
        },
        "distance": distance,
        "source": "vector",
    }


def _case_chunk(chunk_id: str, distance: float = 0.3, collection: str = "court_practice") -> dict:
    """Build a court case chunk."""
    return {
        "chunk_id": chunk_id,
        "content": "court ruling text",
        "metadata": {
            "_collection": collection,
            "case_id": chunk_id,
            "category": "criminal",
        },
        "distance": distance,
        "source": "vector",
    }


def _gc_chunk(chunk_id: str, distance: float = 0.2) -> dict:
    """Build a grand chamber chunk."""
    return _case_chunk(chunk_id, distance, collection="grand_chamber")


# ── Quota Enforcement ────────────────────────────────────────

class TestQuotaEnforcement:
    """Test that RAG_LAWS_QUOTA=15 and RAG_CASES_QUOTA=8 are enforced."""

    def _make_service(self):
        svc = RAGRetrievalService(
            chroma=MagicMock(),
            embedding_client=MagicMock(),
            gemini_client=MagicMock(),
        )
        return svc

    @pytest.mark.asyncio
    async def test_exactly_15_laws_all_kept(self):
        """15 law chunks → all 15 kept."""
        svc = self._make_service()
        laws = [_law_chunk(f"law_{i}", distance=i * 0.01) for i in range(15)]

        # Mock pipeline stages to return our test data
        svc._stage_0_expand_queries = AsyncMock(return_value=["test query"])
        svc._stage_1_vector_search = AsyncMock(return_value=laws)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=laws)
        # Skip rerank (len <= top_k)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("ქურდობა", top_k=50)

        result_laws = [r for r in result if r["metadata"].get("_collection") == "georgian_laws"]
        assert len(result_laws) == 15

    @pytest.mark.asyncio
    async def test_16th_law_dropped(self):
        """16 law chunks → only 15 kept."""
        svc = self._make_service()
        laws = [_law_chunk(f"law_{i}", distance=i * 0.01) for i in range(16)]

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=laws)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=laws)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("ქურდობა", top_k=50)

        result_laws = [r for r in result if r["metadata"].get("_collection") == "georgian_laws"]
        assert len(result_laws) == 15, f"Expected 15, got {len(result_laws)}"

    @pytest.mark.asyncio
    async def test_exactly_8_cases_all_kept(self):
        """8 court case chunks → all 8 kept."""
        svc = self._make_service()
        cases = [_case_chunk(f"case_{i}", distance=i * 0.01) for i in range(8)]

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=cases)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=cases)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("test", top_k=50)

        result_cases = [r for r in result if r["metadata"].get("_collection") in ("court_practice", "grand_chamber")]
        assert len(result_cases) == 8

    @pytest.mark.asyncio
    async def test_9th_case_dropped(self):
        """9 court case chunks → only 8 kept."""
        svc = self._make_service()
        cases = [_case_chunk(f"case_{i}", distance=i * 0.01) for i in range(9)]

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=cases)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=cases)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("test", top_k=50)

        result_cases = [r for r in result if r["metadata"].get("_collection") in ("court_practice", "grand_chamber")]
        assert len(result_cases) == 8, f"Expected 8, got {len(result_cases)}"

    @pytest.mark.asyncio
    async def test_grand_chamber_counts_toward_cases_quota(self):
        """5 court_practice + 5 grand_chamber → only 8 total kept (cases quota)."""
        svc = self._make_service()
        mixed = [_case_chunk(f"court_{i}") for i in range(5)]
        mixed += [_gc_chunk(f"gc_{i}") for i in range(5)]

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=mixed)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=mixed)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("test", top_k=50)

        result_cases = [r for r in result if r["metadata"].get("_collection") in ("court_practice", "grand_chamber")]
        assert len(result_cases) == 8

    @pytest.mark.asyncio
    async def test_mixed_laws_and_cases_both_quotas(self):
        """20 laws + 10 cases → 15 laws + 8 cases = 23 total."""
        svc = self._make_service()
        mixed = [_law_chunk(f"law_{i}", distance=i * 0.01) for i in range(20)]
        mixed += [_case_chunk(f"case_{i}", distance=i * 0.01) for i in range(10)]

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=mixed)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=mixed)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("test", top_k=50)

        laws = [r for r in result if r["metadata"].get("_collection") == "georgian_laws"]
        cases = [r for r in result if r["metadata"].get("_collection") in ("court_practice", "grand_chamber")]
        assert len(laws) == 15
        assert len(cases) == 8


# ── Merge & Dedup ────────────────────────────────────────────

class TestMergeAndDedup:
    """Test Stage 3 merge logic — the actual deduplication behavior."""

    def _make_service(self):
        chroma = MagicMock()
        chroma.get_by_ids = MagicMock(return_value=[])
        return RAGRetrievalService(chroma=chroma, embedding_client=MagicMock(), gemini_client=MagicMock())

    def test_duplicate_keeps_lower_distance(self):
        """Same chunk_id in vector (0.5) and vector (0.1) → keeps 0.1."""
        svc = self._make_service()
        vector_hits = [
            {"chunk_id": "A", "content": "first", "metadata": {}, "distance": 0.5, "source": "vector"},
            {"chunk_id": "A", "content": "second", "metadata": {}, "distance": 0.1, "source": "vector"},
        ]
        result = svc._stage_3_merge_and_dedup(vector_hits, [])
        assert len(result) == 1
        assert result[0]["distance"] == 0.1, f"Expected 0.1, got {result[0]['distance']}"

    def test_vector_preferred_over_fulltext_same_id(self):
        """Vector hit and fulltext hit with same ID → vector kept (it has content)."""
        svc = self._make_service()
        vector = [{"chunk_id": "A", "content": "real content", "metadata": {"code_name": "test"}, "distance": 0.3, "source": "vector"}]
        fulltext = [{"chunk_id": "A", "content": "", "metadata": {}, "distance": 0.7, "source": "fulltext"}]
        result = svc._stage_3_merge_and_dedup(vector, fulltext)
        assert len(result) == 1
        assert result[0]["content"] == "real content"

    def test_fulltext_only_gets_enriched(self):
        """Fulltext hit with empty content → ChromaDB get_by_ids fills it."""
        svc = self._make_service()
        svc._chroma.get_by_ids = MagicMock(return_value=[{
            "chunk_id": "FT1",
            "content": "enriched content from chroma",
            "metadata": {"code_name": "test", "article_number": "მუხლი 1"},
        }])
        fulltext = [{"chunk_id": "FT1", "content": "", "metadata": {}, "distance": 0.5, "source": "fulltext"}]
        result = svc._stage_3_merge_and_dedup([], fulltext)
        assert len(result) == 1
        assert result[0]["content"] == "enriched content from chroma"
        assert result[0]["metadata"]["code_name"] == "test"

    def test_sorted_by_distance(self):
        """Results are sorted by distance (best first)."""
        svc = self._make_service()
        hits = [
            {"chunk_id": "C", "content": "", "metadata": {}, "distance": 0.9, "source": "vector"},
            {"chunk_id": "A", "content": "", "metadata": {}, "distance": 0.1, "source": "vector"},
            {"chunk_id": "B", "content": "", "metadata": {}, "distance": 0.5, "source": "vector"},
        ]
        result = svc._stage_3_merge_and_dedup(hits, [])
        distances = [r["distance"] for r in result]
        assert distances == sorted(distances), f"Not sorted: {distances}"

    def test_no_hits_returns_empty(self):
        """Empty input → empty output."""
        svc = self._make_service()
        result = svc._stage_3_merge_and_dedup([], [])
        assert result == []


# ── Threshold Prepend ────────────────────────────────────────

class TestThresholdPrepend:
    """Test that threshold hits are prepended without duplicating RAG hits."""

    @pytest.mark.asyncio
    async def test_threshold_prepended_to_results(self):
        """Threshold hits should appear before RAG results."""
        svc = RAGRetrievalService(chroma=MagicMock(), embedding_client=MagicMock(), gemini_client=MagicMock())
        rag_chunks = [_law_chunk("law_1", distance=0.1)]
        threshold_hit = {"chunk_id": "threshold_drug_92", "content": "მარიხუანა 140გ", "metadata": {"_collection": "georgian_laws"}, "distance": 0.0, "source": "lookup"}

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=rag_chunks)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=rag_chunks)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = [threshold_hit]
            result = await svc.retrieve("მარიხუანა ოდენობა", top_k=50)

        assert result[0]["chunk_id"] == "threshold_drug_92", "Threshold should be first"
        assert len(result) == 2  # threshold + 1 law chunk

    @pytest.mark.asyncio
    async def test_threshold_deduplicates_with_rag(self):
        """If threshold chunk_id matches a RAG hit, RAG duplicate is removed."""
        svc = RAGRetrievalService(chroma=MagicMock(), embedding_client=MagicMock(), gemini_client=MagicMock())
        rag_chunks = [
            {"chunk_id": "threshold_drug_92", "content": "from rag", "metadata": {"_collection": "georgian_laws"}, "distance": 0.5, "source": "vector"},
            _law_chunk("law_1", distance=0.3),
        ]
        threshold_hit = {"chunk_id": "threshold_drug_92", "content": "from threshold", "metadata": {}, "distance": 0.0, "source": "lookup"}

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=rag_chunks)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=rag_chunks)
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = [threshold_hit]
            result = await svc.retrieve("test", top_k=50)

        ids = [r["chunk_id"] for r in result]
        assert ids.count("threshold_drug_92") == 1, f"Duplicate! IDs: {ids}"


# ── Search Law Normalization ─────────────────────────────────

class TestSearchLawNormalization:
    """Test search_law article number normalization edge cases."""

    def _make_service(self):
        chroma = MagicMock()
        chroma.search_by_metadata = MagicMock(return_value=[{
            "chunk_id": "found",
            "content": "law text",
            "metadata": {"code_name": "test", "article_number": "მუხლი 77"},
        }])
        embedding = MagicMock()
        embedding.embed_query = MagicMock(return_value=[0.1] * 768)
        chroma.vector_search = MagicMock(return_value=[])
        return RAGRetrievalService(chroma=chroma, embedding_client=embedding, gemini_client=MagicMock())

    @pytest.mark.asyncio
    async def test_plain_number_gets_prefix(self):
        """'77' → 'მუხლი 77'."""
        svc = self._make_service()
        await svc.search_law(query="test", article_number="77")
        call_args = svc._chroma.search_by_metadata.call_args
        where = call_args[1]["where"] if "where" in call_args[1] else call_args[0][0]
        # The where clause should contain "მუხლი 77"
        where_str = str(where)
        assert "მუხლი 77" in where_str

    @pytest.mark.asyncio
    async def test_already_prefixed_not_doubled(self):
        """'მუხლი 77' should not become 'მუხლი მუხლი 77'."""
        svc = self._make_service()
        await svc.search_law(query="test", article_number="მუხლი 77")
        where_str = str(svc._chroma.search_by_metadata.call_args)
        assert "მუხლი მუხლი" not in where_str

    @pytest.mark.asyncio
    async def test_with_whitespace(self):
        """' 77 ' → 'მუხლი 77'."""
        svc = self._make_service()
        await svc.search_law(query="test", article_number=" 77 ")
        where_str = str(svc._chroma.search_by_metadata.call_args)
        assert "მუხლი 77" in where_str

    @pytest.mark.asyncio
    async def test_code_name_normalization_adds_prefix(self):
        """Short code name should get საქართველოს prefix in search."""
        svc = self._make_service()
        await svc.search_law(
            query="test",
            article_number="მუხლი 177",
            code_name="სისხლის სამართლის კოდექსი",
        )
        where_str = str(svc._chroma.search_by_metadata.call_args)
        assert "საქართველოს სისხლის სამართლის კოდექსი" in where_str


# ── Pipeline Graceful Degradation ────────────────────────────

class TestPipelineDegradation:
    """Test that the pipeline doesn't crash when individual stages fail."""

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self):
        """Empty expanded queries → returns [] immediately."""
        svc = RAGRetrievalService(chroma=MagicMock(), embedding_client=MagicMock(), gemini_client=MagicMock())
        svc._stage_0_expand_queries = AsyncMock(return_value=[])
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("")
        assert result == []

    @pytest.mark.asyncio
    async def test_vector_search_empty_fulltext_has_results(self):
        """Vector search returns nothing but fulltext finds articles → still works."""
        svc = RAGRetrievalService(chroma=MagicMock(), embedding_client=MagicMock(), gemini_client=MagicMock())
        ft_hit = {"chunk_id": "ft_1", "content": "", "metadata": {}, "distance": 0.3, "source": "fulltext"}
        svc._chroma.get_by_ids = MagicMock(return_value=[{
            "chunk_id": "ft_1",
            "content": "found via fulltext",
            "metadata": {"_collection": "georgian_laws", "code_name": "test"},
        }])

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=[])
        svc._stage_2_fulltext_search = MagicMock(return_value=[ft_hit])
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("test", top_k=50)

        assert len(result) >= 1
        assert result[0]["content"] == "found via fulltext"

    @pytest.mark.asyncio
    async def test_rerank_failure_falls_back_to_candidates(self):
        """If rerank raises an exception → returns candidates[:top_k]."""
        svc = RAGRetrievalService(chroma=MagicMock(), embedding_client=MagicMock(), gemini_client=MagicMock())
        candidates = [_law_chunk(f"law_{i}", distance=i * 0.1) for i in range(40)]

        svc._stage_0_expand_queries = AsyncMock(return_value=["test"])
        svc._stage_1_vector_search = AsyncMock(return_value=candidates)
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=candidates)
        # Make rerank fail
        svc._gemini.generate_json = AsyncMock(side_effect=Exception("API error"))
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("test", top_k=35)

        # Should still get results (quota-enforced from fallback)
        assert len(result) > 0
        laws = [r for r in result if r["metadata"].get("_collection") == "georgian_laws"]
        assert len(laws) <= 15  # Quota still applies

    @pytest.mark.asyncio
    async def test_query_expansion_failure_uses_raw_message(self):
        """If Gemini query expansion fails → uses original message as single query."""
        svc = RAGRetrievalService(chroma=MagicMock(), embedding_client=MagicMock(), gemini_client=MagicMock())
        svc._gemini.generate_json = AsyncMock(side_effect=Exception("API timeout"))
        svc._stage_1_vector_search = AsyncMock(return_value=[_law_chunk("law_1")])
        svc._stage_2_fulltext_search = MagicMock(return_value=[])
        svc._stage_3_merge_and_dedup = MagicMock(return_value=[_law_chunk("law_1")])
        with patch("app.services.rag_retrieval_service.get_threshold_service") as mock_ts:
            mock_ts.return_value.search.return_value = []
            result = await svc.retrieve("ქურდობის სასჯელი", top_k=50)

        # Should have called vector search with the raw message as fallback
        assert svc._stage_1_vector_search.called
        assert len(result) > 0
