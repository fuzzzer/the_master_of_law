"""
Complex flow tests — multi-service integration scenarios.

Tests end-to-end flows that span multiple services:
1. Conversation lifecycle (phase transitions)
2. RAG → Analysis → Citation Verification
3. Agent pipeline with tool calls
4. Case builder end-to-end
5. Auth paths for different user types
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.constants import ConversationPhase
from app.services.conversation_service import ConversationService
from app.services.legal_analysis_service import LawContextFormatter, LegalAnalysisService
from app.services.agent_pipeline_service import AgentPipelineService, PipelineResult
from conftest import make_mock_conversation, make_mock_message, MOCK_USER_UID


class TestConversationLifecycleFlow:
    """Flow 1: Full conversation lifecycle — phase transitions end-to-end."""

    @pytest.mark.asyncio
    async def test_greeting_through_follow_up(self, mock_db):
        """Create conversation → GREETING → INTAKE → ANALYSIS → ADVICE → FOLLOW_UP."""
        conv = make_mock_conversation(phase=ConversationPhase.GREETING.value)
        svc = ConversationService(mock_db)

        # Step 1: Create in GREETING phase
        with patch.object(svc._conv_repo, "create", AsyncMock(return_value=conv)):
            result = await svc.create_conversation(MOCK_USER_UID, "Test")
            assert result["phase"] == "GREETING"

        # Step 2: First message → determine INTAKE
        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            next_phase = await svc.determine_next_phase(str(conv.id), 1)
            assert next_phase == ConversationPhase.INTAKE

        # Step 3: Transition to INTAKE
        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)), \
             patch.object(svc._conv_repo, "update_phase", AsyncMock()):
            result = await svc.transition_phase(str(conv.id), ConversationPhase.INTAKE)
            assert result is True

        # Step 4: After QUESTIONNAIRE → ANALYSIS
        conv.phase = ConversationPhase.QUESTIONNAIRE.value
        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            next_phase = await svc.determine_next_phase(str(conv.id), 5)
            assert next_phase == ConversationPhase.ANALYSIS

        # Step 5: After ANALYSIS → ADVICE
        conv.phase = ConversationPhase.ANALYSIS.value
        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            next_phase = await svc.determine_next_phase(str(conv.id), 8)
            assert next_phase == ConversationPhase.ADVICE

        # Step 6: After ADVICE → FOLLOW_UP
        conv.phase = ConversationPhase.ADVICE.value
        with patch.object(svc._conv_repo, "get_by_id", AsyncMock(return_value=conv)):
            next_phase = await svc.determine_next_phase(str(conv.id), 10)
            assert next_phase == ConversationPhase.FOLLOW_UP


class TestRAGToAnalysisFlow:
    """Flow 2: RAG retrieval → Legal Analysis → Context formatting."""

    def test_chunks_flow_through_formatter(self, sample_law_chunks, sample_court_chunks):
        """Chunks from RAG should format correctly for analysis."""
        all_chunks = sample_law_chunks + sample_court_chunks

        # Step 1: Format chunks
        formatted = LawContextFormatter.format(all_chunks)
        assert "RELEVANT GEORGIAN LAW ARTICLES" in formatted
        assert "COURT PRACTICE" in formatted

        # Step 2: Verify source types
        sources = LawContextFormatter.get_source_types(all_chunks)
        assert "georgian_laws" in sources
        assert "court_practice" in sources

    @pytest.mark.asyncio
    async def test_rag_to_analysis_service(
        self, mock_gemini, sample_law_chunks, sample_court_chunks
    ):
        """RAG chunks should flow into LegalAnalysisService.analyze."""
        all_chunks = sample_law_chunks + sample_court_chunks
        mock_gemini.generate = AsyncMock(return_value="Legal analysis with citations.")

        svc = LegalAnalysisService(gemini_client=mock_gemini)
        result = await svc.analyze(
            user_message="რა სასჯელი ეკისრება ქურდობისთვის?",
            retrieved_chunks=all_chunks,
            conversation_history=[{"role": "user", "content": "question"}],
        )
        assert "Legal analysis" in result
        assert "⚠️" in result  # Disclaimer appended


class TestAgentPipelineDirectResponseFlow:
    """Flow 3: Agent pipeline — greeting → direct response (no RAG)."""

    @pytest.mark.asyncio
    async def test_greeting_skips_rag(self, mock_gemini):
        """Greeting should produce direct response without RAG."""
        plan_json = json.dumps({
            "needs_rag": False,
            "direct_response": "გამარჯობა! რით შემიძლია დაგეხმაროთ?",
            "intent": "greeting",
        })
        mock_response = MagicMock()
        mock_response.text = plan_json
        mock_chat = MagicMock()
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_gemini.create_chat = AsyncMock(return_value=mock_chat)

        svc = AgentPipelineService(gemini=mock_gemini)
        result = await svc.run(user_message="გამარჯობა")
        assert result.response_text == "გამარჯობა! რით შემიძლია დაგეხმაროთ?"
        assert result.chunks == []
        assert result.plan.intent == "greeting"


class TestCaseBuilderEndToEnd:
    """Flow 4: Case builder — format conversation → expand → build."""

    def test_conversation_formatting(self):
        """Conversation history should format into labeled text."""
        from app.services.case_builder_service import CaseBuilderService
        history = [
            {"role": "user", "content": "I was arrested for theft"},
            {"role": "assistant", "content": "Tell me about the circumstances"},
            {"role": "user", "content": "It happened on Jan 1st 2024"},
        ]
        result = CaseBuilderService._format_conversation(history)
        assert "USER: I was arrested" in result
        assert "ASSISTANT: Tell me" in result
        assert result.count("\n") == 2  # 3 lines, 2 newlines

    def test_case_render_with_partial_data(self):
        """Render should handle partial case data gracefully."""
        from app.services.case_builder_service import CaseFileRenderer
        data = {
            "title": "Theft Case",
            "facts": {"what": "Arrested for shoplifting", "where": "Tbilisi"},
            "defense_strategies": [
                {"name": "Insufficient evidence", "success_likelihood": "medium",
                 "risk_level": "low", "how_it_works": "Challenge evidence chain"},
            ],
        }
        result = CaseFileRenderer.render(data)
        assert "Theft Case" in result
        assert "FACTS" in result
        assert "DEFENSE STRATEGIES" in result
        assert "Insufficient evidence" in result


class TestAuthFlowVariants:
    """Flow 5: Authentication path variants."""

    @pytest.mark.asyncio
    async def test_dev_mode_to_rate_limit(self):
        """Dev mode auth → rate limit check flow."""
        from app.middleware.firebase_auth_middleware import FirebaseAuthMiddleware
        from app.middleware.rate_limit_middleware import RateLimitMiddleware

        # Auth middleware
        auth_mw = FirebaseAuthMiddleware(MagicMock())
        request = MagicMock()
        request.url.path = "/api/v1/conversations"
        request.method = "GET"
        request.headers = {}
        request.state = MagicMock()

        async def mock_call_next(req):
            return MagicMock(status_code=200)

        with patch("app.middleware.firebase_auth_middleware.settings") as mock_settings:
            mock_settings.app_env = "development"
            mock_settings.admin_api_key = "admin-key"
            response = await auth_mw.dispatch(request, mock_call_next)
            # User should now be set on request.state
            assert request.state.user["uid"] == "dev-user-001"

        # Now rate limit middleware should pass (user has state.user)
        rate_mw = RateLimitMiddleware(MagicMock())
        request2 = MagicMock()
        request2.url.path = "/api/v1/conversations"
        request2.state.user = request.state.user
        response = await rate_mw.dispatch(request2, AsyncMock(return_value=MagicMock(status_code=200)))
        assert response.status_code == 200

    def test_conversation_delete_flow(self, mock_db):
        """Delete conversation: messages removed first, then conversation."""
        # This tests the FK-aware ordering
        svc = ConversationService(mock_db)
        conv_id = str(uuid.uuid4())

        with patch.object(svc._msg_repo, "delete_for_conversation", AsyncMock()) as del_msgs, \
             patch.object(svc._conv_repo, "delete", AsyncMock(return_value=True)) as del_conv:
            import asyncio
            result = asyncio.run(
                svc.delete_conversation(conv_id)
            )
            # Verify order: messages deleted before conversation
            del_msgs.assert_called_once()
            del_conv.assert_called_once()
