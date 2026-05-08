"""
Coverage expansion tests — targeting <80% coverage areas.

Covers:
- RAG pipeline edge cases (empty results, single collection, all disabled)
- Credit system edge cases (zero credits, concurrent deductions)
- Conversation state machine transition tests (invalid transitions)
- Citation extraction tests (malformed references)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sys

sys.path.insert(0, ".")

from app.config.constants import ConversationPhase, CreditAction, UserTier
from app.repositories.credit_repository import CreditRepository
from app.services.citation_service import CitationService
from app.services.conversation_service import ConversationService
from app.services.rag_retrieval_service import RAGRetrievalService


# ── RAG Pipeline Edge Cases ────────────────────────────────────

class TestRAGRetrievalEdgeCases:
    """Tests for RAGRetrievalService edge cases."""

    def setup_method(self):
        self.svc = RAGRetrievalService(
            chroma=MagicMock(),
            embedding_client=MagicMock(),
            gemini_client=MagicMock(),
        )

    @pytest.mark.asyncio
    async def test_retrieve_empty_results_all_stages(self):
        """When all stages return empty, the pipeline should return []."""
        self.svc._stage_0_expand_queries = AsyncMock(return_value=["query"])
        self.svc._stage_1_vector_search = AsyncMock(return_value=[])
        self.svc._stage_2_fulltext_search = AsyncMock(return_value=[])

        result = await self.svc.retrieve("some question")
        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_single_collection_only(self):
        """Restricting to a single collection should still work."""
        self.svc._stage_0_expand_queries = AsyncMock(return_value=["q"])
        self.svc._stage_1_vector_search = AsyncMock(return_value=[
            {"chunk_id": "c1", "content": "test", "metadata": {}, "distance": 0.1, "source": "vector"}
        ])
        self.svc._stage_2_fulltext_search = AsyncMock(return_value=[])

        result = await self.svc.retrieve("question", collections=["criminal_code"])
        self.svc._stage_1_vector_search.assert_awaited_once()
        call_args = self.svc._stage_1_vector_search.call_args
        assert call_args[1]["collections"] == ["criminal_code"]
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_retrieve_no_rerank_when_below_top_k(self):
        """If merged results are <= top_k, skip rerank stage."""
        self.svc._stage_0_expand_queries = AsyncMock(return_value=["q"])
        self.svc._stage_1_vector_search = AsyncMock(return_value=[
            {"chunk_id": "c1", "content": "a", "metadata": {}, "distance": 0.1, "source": "vector"},
        ])
        self.svc._stage_2_fulltext_search = AsyncMock(return_value=[])
        self.svc._stage_4_rerank = AsyncMock()  # should NOT be called

        result = await self.svc.retrieve("question", top_k=5)
        self.svc._stage_4_rerank.assert_not_awaited()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_retrieve_rerank_triggered_when_above_top_k(self):
        """If merged results exceed top_k, rerank should be called."""
        hits = [
            {"chunk_id": f"c{i}", "content": "x", "metadata": {}, "distance": 0.1 * i, "source": "vector"}
            for i in range(25)
        ]
        self.svc._stage_0_expand_queries = AsyncMock(return_value=["q"])
        self.svc._stage_1_vector_search = AsyncMock(return_value=hits)
        self.svc._stage_2_fulltext_search = AsyncMock(return_value=[])
        self.svc._stage_4_rerank = AsyncMock(return_value=hits[:5])

        result = await self.svc.retrieve("question", top_k=5)
        self.svc._stage_4_rerank.assert_awaited_once()
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_stage_0_fallback_on_exception(self):
        """If query expansion fails, fallback to original message."""
        self.svc.gemini.generate_json = AsyncMock(side_effect=Exception("Gemini down"))
        result = await self.svc._stage_0_expand_queries("original")
        assert result == ["original"]

    def test_stage_2_empty_index(self):
        """Fulltext search with empty article index returns []."""
        self.svc._article_index = {}
        result = self.svc._stage_2_fulltext_search(["query"])
        assert result == []

    def test_stage_3_merge_dedup_prefers_better_distance(self):
        """Dedup keeps the hit with lowest distance."""
        vector = [{"chunk_id": "a", "distance": 0.1}]
        fulltext = [{"chunk_id": "a", "distance": 0.9}]
        result = self.svc._stage_3_merge_and_dedup(vector, fulltext)
        assert len(result) == 1
        assert result[0]["distance"] == 0.1

    @pytest.mark.asyncio
    async def test_stage_4_rerank_exception_fallback(self):
        """If rerank fails, return top_k candidates."""
        candidates = [{"chunk_id": f"c{i}"} for i in range(10)]
        self.svc.gemini.generate_json = AsyncMock(side_effect=Exception("fail"))
        result = await self.svc._stage_4_rerank("q", candidates, 3)
        assert len(result) == 3
        assert result[0]["chunk_id"] == "c0"


# ── Credit System Edge Cases ───────────────────────────────────

class TestCreditEdgeCases:
    """Tests for credit system edge cases."""

    def setup_method(self):
        self.repo = CreditRepository(db=MagicMock())

    def test_zero_credits_pro_tier(self):
        """PRO tier with 0 balance should not have sufficient credits."""
        credits = MagicMock()
        credits.tier = "PRO"
        credits.credit_balance = 0
        credits.daily_credits_used = 0
        assert self.repo.has_sufficient_credits(credits, 1) is False

    def test_zero_cost_action(self):
        """Actions with 0 cost should always pass."""
        credits = MagicMock()
        credits.tier = "FREE"
        credits.daily_credits_used = 5
        assert self.repo.has_sufficient_credits(credits, 0) is True

    def test_concurrent_deduction_simulation(self):
        """Simulate rapid successive deductions to check balance consistency."""
        # This tests the logic in isolation; real concurrency needs DB transactions
        credits = MagicMock()
        credits.tier = "PRO"
        credits.credit_balance = 3
        credits.daily_credits_used = 0

        # First deduction of 2 should succeed
        assert self.repo.has_sufficient_credits(credits, 2) is True
        # Simulate balance update
        credits.credit_balance = 1
        # Second deduction of 2 should now fail
        assert self.repo.has_sufficient_credits(credits, 2) is False

    def test_negative_balance(self):
        """Negative balance should be treated as insufficient."""
        credits = MagicMock()
        credits.tier = "PRO"
        credits.credit_balance = -1
        assert self.repo.has_sufficient_credits(credits, 1) is False

    def test_free_tier_exactly_at_limit(self):
        """FREE tier with daily_credits_used == 5 cannot afford any positive cost."""
        credits = MagicMock()
        credits.tier = "FREE"
        credits.daily_credits_used = 5
        assert self.repo.has_sufficient_credits(credits, 1) is False

    def test_admin_unlimited(self):
        """ADMIN tier should always pass regardless of balance."""
        credits = MagicMock()
        credits.tier = "ADMIN"
        credits.credit_balance = -999
        assert self.repo.has_sufficient_credits(credits, 1000) is True

    def test_get_remaining_negative_balance(self):
        """Remaining credits should never be negative."""
        credits = MagicMock()
        credits.tier = "PRO"
        credits.credit_balance = -5
        assert self.repo.get_remaining_credits(credits) == 0


# ── Conversation State Machine ─────────────────────────────────

class TestConversationStateMachine:
    """Tests for conversation phase transition edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_transition_allowed(self):
        """Invalid transitions are logged but allowed to prevent deadlocks."""
        mock_db = MagicMock()
        conv_repo = AsyncMock()
        msg_repo = AsyncMock()

        conv_repo.get_by_id = AsyncMock(return_value=MagicMock(phase="ADVICE"))
        conv_repo.update_phase = AsyncMock(return_value=None)

        svc = ConversationService(mock_db)
        svc._conv_repo = conv_repo
        svc._msg_repo = msg_repo

        # ADVICE -> GREETING is invalid per state machine
        result = await svc.transition_phase(str(uuid.uuid4()), ConversationPhase.GREETING)
        assert result is True  # still allowed
        conv_repo.update_phase.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_transition_with_corrupt_phase(self):
        """Corrupt phase value should default to GREETING."""
        mock_db = MagicMock()
        conv_repo = AsyncMock()
        msg_repo = AsyncMock()

        conv_repo.get_by_id = AsyncMock(return_value=MagicMock(phase="UNKNOWN_PHASE"))
        conv_repo.update_phase = AsyncMock(return_value=None)

        svc = ConversationService(mock_db)
        svc._conv_repo = conv_repo
        svc._msg_repo = msg_repo

        result = await svc.transition_phase(str(uuid.uuid4()), ConversationPhase.INTAKE)
        assert result is True

    @pytest.mark.asyncio
    async def test_transition_nonexistent_conversation(self):
        """Transition on missing conversation should return False."""
        mock_db = MagicMock()
        conv_repo = AsyncMock()
        msg_repo = AsyncMock()

        conv_repo.get_by_id = AsyncMock(return_value=None)

        svc = ConversationService(mock_db)
        svc._conv_repo = conv_repo
        svc._msg_repo = msg_repo

        result = await svc.transition_phase(str(uuid.uuid4()), ConversationPhase.INTAKE)
        assert result is False

    @pytest.mark.asyncio
    async def test_determine_next_phase_greeting_to_intake(self):
        """First message should move from GREETING to INTAKE."""
        mock_db = MagicMock()
        conv_repo = AsyncMock()
        msg_repo = AsyncMock()

        conv_repo.get_by_id = AsyncMock(return_value=MagicMock(phase="GREETING"))

        svc = ConversationService(mock_db)
        svc._conv_repo = conv_repo
        svc._msg_repo = msg_repo

        phase = await svc.determine_next_phase(str(uuid.uuid4()), message_count=1)
        assert phase == ConversationPhase.INTAKE

    @pytest.mark.asyncio
    async def test_determine_next_phase_intake_to_analysis(self):
        """After 3 messages, INTAKE should move to ANALYSIS."""
        mock_db = MagicMock()
        conv_repo = AsyncMock()
        msg_repo = AsyncMock()

        conv_repo.get_by_id = AsyncMock(return_value=MagicMock(phase="INTAKE"))

        svc = ConversationService(mock_db)
        svc._conv_repo = conv_repo
        svc._msg_repo = msg_repo

        phase = await svc.determine_next_phase(str(uuid.uuid4()), message_count=3)
        assert phase == ConversationPhase.ANALYSIS

    @pytest.mark.asyncio
    async def test_determine_next_phase_invalid_uuid(self):
        """Invalid conversation ID should default to GREETING."""
        svc = ConversationService(MagicMock())
        phase = await svc.determine_next_phase("bad-uuid", message_count=5)
        assert phase == ConversationPhase.GREETING

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self):
        """Empty conversation list should return ([], 0)."""
        mock_db = MagicMock()
        conv_repo = AsyncMock()
        msg_repo = AsyncMock()

        conv_repo.list_for_user = AsyncMock(return_value=[])
        conv_repo.count_for_user = AsyncMock(return_value=0)

        svc = ConversationService(mock_db)
        svc._conv_repo = conv_repo
        svc._msg_repo = msg_repo

        convs, total = await svc.list_conversations("user-123")
        assert convs == []
        assert total == 0


# ── Citation Extraction Edge Cases ─────────────────────────────

class TestCitationExtractionEdgeCases:
    """Tests for CitationService edge cases and malformed input."""

    def setup_method(self):
        self.svc = CitationService(chroma=None)

    def test_malformed_article_reference(self):
        """Text with malformed article refs should be handled gracefully."""
        text = "მუხლი ასდ არ არსებობს"
        citations = self.svc.extract_citations(text)
        # Should not crash; may extract nothing or partial refs
        assert isinstance(citations, list)

    def test_article_without_preceding_code(self):
        """Article without a known code name should have Unknown code."""
        text = "მუხლი 42 ძალიან მნიშვნელოვანია"
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["code_name"] == "Unknown"

    def test_multiple_articles_same_code(self):
        """Multiple articles from the same code should all be extracted."""
        text = "სისხლის სამართლის კოდექსი, მუხლი 11, მუხლი 12 და მუხლი 13"
        citations = self.svc.extract_citations(text)
        articles = {c["article_number"] for c in citations}
        assert "მუხლი 11" in articles
        assert "მუხლი 12" in articles
        assert "მუხლი 13" in articles

    def test_code_name_far_from_article(self):
        """If code name is too far, it may not match — that's acceptable."""
        text = "სისხლის სამართლის კოდექსი. ახლა ბევრი სხვა ტექსტია შუაში. მუხლი 99"
        citations = self.svc.extract_citations(text)
        # It may still match because it searches backwards
        assert len(citations) >= 1

    def test_empty_string(self):
        """Empty string should return empty citations."""
        citations = self.svc.extract_citations("")
        assert citations == []

    def test_verify_malformed_citation(self):
        """Verifying a citation with missing fields should not crash."""
        citations = [{"article_number": "", "code_name": "", "raw_text": ""}]
        verified = self.svc.verify_citations(citations, [])
        assert len(verified) == 1
        assert verified[0]["verified"] is False

    def test_verify_with_duplicate_chunks(self):
        """Duplicate chunks in retrieved list should not cause issues."""
        chunks = [
            {
                "chunk_id": "c1",
                "metadata": {"code_name": "კოდექსი", "article_number": "მუხლი 1"},
            },
            {
                "chunk_id": "c1",
                "metadata": {"code_name": "კოდექსი", "article_number": "მუხლი 1"},
            },
        ]
        citations = [{"article_number": "მუხლი 1", "code_name": "კოდექსი", "raw_text": "t"}]
        verified = self.svc.verify_citations(citations, chunks)
        assert len(verified) == 1
        assert verified[0]["verified"] is True
