"""
Tests for the 3-phase agent pipeline service.

Tests _history_to_contents, _format_law_context, _select_tools,
Phase 1 (planning), Phase 3 (verification), and full run.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai import types

from app.services.agent_pipeline_service import (
    AgentPipelineService,
    PipelinePlan,
    PipelineResult,
    MAX_VERIFY_ITERATIONS,
)
from app.tools.case_tools import ALWAYS_TOOLS, CASE_CREATION_TOOLS, FULL_CASE_TOOLS


# ── _history_to_contents tests ───────────────────────────────

class TestHistoryToContents:
    """Convert DB history dicts to Gemini Content objects."""

    def test_empty(self):
        result = AgentPipelineService._history_to_contents([])
        assert result == []

    def test_consecutive_same_role_merged(self):
        """Consecutive same-role messages should be merged."""
        history = [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
            {"role": "assistant", "content": "response"},
        ]
        result = AgentPipelineService._history_to_contents(history)
        assert len(result) == 2
        assert result[0].role == "user"
        assert "first" in result[0].parts[0].text
        assert "second" in result[0].parts[0].text

    def test_starts_with_model_popped(self):
        """If history starts with model, it should be removed."""
        history = [
            {"role": "assistant", "content": "model first"},
            {"role": "user", "content": "user msg"},
        ]
        result = AgentPipelineService._history_to_contents(history)
        assert len(result) == 1
        assert result[0].role == "user"

    def test_alternating_roles(self):
        """Normal alternating roles should produce Content objects."""
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
            {"role": "user", "content": "question"},
        ]
        result = AgentPipelineService._history_to_contents(history)
        assert len(result) == 3
        assert result[0].role == "user"
        assert result[1].role == "model"
        assert result[2].role == "user"

    def test_respects_limit_20(self):
        """History should be limited to last 20 messages."""
        history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"} for i in range(30)]
        result = AgentPipelineService._history_to_contents(history)
        # Should process at most 20
        assert len(result) <= 20


# ── _format_law_context tests ────────────────────────────────

class TestFormatLawContext:
    """Format retrieved chunks for Gemini context."""

    def test_empty_chunks(self):
        result = AgentPipelineService._format_law_context([])
        assert result == ""

    def test_with_chunks(self, mock_chunks):
        result = AgentPipelineService._format_law_context(mock_chunks)
        assert "[1]" in result
        assert "[2]" in result
        assert "სისხლის სამართლის კოდექსი" in result

    def test_caps_at_30(self):
        """Should cap at 30 chunks."""
        chunks = [
            {"chunk_id": f"c{i}", "content": "text", "metadata": {}}
            for i in range(50)
        ]
        result = AgentPipelineService._format_law_context(chunks)
        assert "[30]" in result
        assert "[31]" not in result


# ── _select_tools tests ──────────────────────────────────────

class TestSelectTools:
    """Tool selection based on context."""

    def test_with_case_file_id(self):
        tools = AgentPipelineService._select_tools(case_file_id="abc", is_case_chat=False)
        assert tools is FULL_CASE_TOOLS

    def test_case_chat(self):
        tools = AgentPipelineService._select_tools(case_file_id=None, is_case_chat=True)
        assert tools is CASE_CREATION_TOOLS

    def test_default(self):
        tools = AgentPipelineService._select_tools(case_file_id=None, is_case_chat=False)
        assert tools is ALWAYS_TOOLS


# ── Phase 1: Planning tests ─────────────────────────────────

class TestPhase1Plan:
    """Phase 1: intent analysis and query planning."""

    @pytest.mark.asyncio
    async def test_legal_question(self, mock_gemini):
        """Legal question should have needs_rag=True."""
        plan_response = json.dumps({
            "needs_rag": True,
            "search_queries": ["query1", "query2"],
            "intent": "legal_question",
        })
        mock_response = MagicMock()
        mock_response.text = plan_response
        mock_chat = MagicMock()
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_gemini.create_chat = AsyncMock(return_value=mock_chat)

        svc = AgentPipelineService(gemini=mock_gemini)
        plan = await svc._phase_1_plan("რა სასჯელი ეკისრება", [])
        assert plan.needs_rag is True
        assert len(plan.search_queries) == 2
        assert plan.intent == "legal_question"

    @pytest.mark.asyncio
    async def test_greeting(self, mock_gemini):
        """Greeting should have direct_response set."""
        plan_response = json.dumps({
            "needs_rag": False,
            "direct_response": "გამარჯობა! რით შემიძლია დაგეხმაროთ?",
            "intent": "greeting",
        })
        mock_response = MagicMock()
        mock_response.text = plan_response
        mock_chat = MagicMock()
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_gemini.create_chat = AsyncMock(return_value=mock_chat)

        svc = AgentPipelineService(gemini=mock_gemini)
        plan = await svc._phase_1_plan("გამარჯობა", [])
        assert plan.direct_response is not None

    @pytest.mark.asyncio
    async def test_flash_failure_fallback(self, mock_gemini):
        """Exception should produce fallback plan."""
        mock_chat = MagicMock()
        mock_chat.send_message = AsyncMock(side_effect=Exception("API error"))
        mock_gemini.create_chat = AsyncMock(return_value=mock_chat)

        svc = AgentPipelineService(gemini=mock_gemini)
        plan = await svc._phase_1_plan("test question", [])
        assert plan.needs_rag is True
        assert plan.search_queries == ["test question"]

    @pytest.mark.asyncio
    async def test_json_in_markdown_block(self, mock_gemini):
        """JSON wrapped in ```json should be parsed correctly."""
        raw = '```json\n{"needs_rag": true, "search_queries": ["q1"]}\n```'
        mock_response = MagicMock()
        mock_response.text = raw
        mock_chat = MagicMock()
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_gemini.create_chat = AsyncMock(return_value=mock_chat)

        svc = AgentPipelineService(gemini=mock_gemini)
        plan = await svc._phase_1_plan("test", [])
        assert plan.needs_rag is True


# ── Phase 3: Verification tests ─────────────────────────────

class TestPhase3Verify:
    """Phase 3: citation verification and correction."""

    @pytest.mark.asyncio
    async def test_all_verified(self, mock_gemini):
        """When all citations are verified, 0 iterations, unchanged text."""
        mock_citation_svc = MagicMock()
        mock_citation_svc.extract_case_citations = MagicMock(return_value=[])
        mock_citation_svc.verify_case_citations = MagicMock(return_value={"verified": [], "not_found": []})
        mock_citation_svc.extract_citations = MagicMock(return_value=[
            {"code_name": "test", "article_number": "მუხლი 1"}
        ])
        mock_citation_svc.verify_against_corpus = MagicMock(return_value={
            "verified": [{"code_name": "test", "article_number": "მუხლი 1"}],
            "not_found": [],
            "corpus_found": [],
        })

        svc = AgentPipelineService(gemini=mock_gemini, citation_svc=mock_citation_svc)
        text, citations, iters = await svc._phase_3_verify("response", [{"chunk_id": "1"}])
        assert text == "response"
        assert iters == 0

    @pytest.mark.asyncio
    async def test_no_text(self, mock_gemini):
        """Empty text should return immediately."""
        mock_citation_svc = MagicMock()
        mock_citation_svc.extract_case_citations = MagicMock(return_value=[])
        mock_citation_svc.verify_case_citations = MagicMock(return_value={"verified": [], "not_found": []})
        mock_citation_svc.extract_citations = MagicMock(return_value=[])
        mock_citation_svc.verify_citations = MagicMock(return_value=[])

        svc = AgentPipelineService(gemini=mock_gemini, citation_svc=mock_citation_svc)
        text, citations, iters = await svc._phase_3_verify("", [])
        assert iters == 0

    @pytest.mark.asyncio
    async def test_hallucination_triggers_correction(self, mock_gemini):
        """Hallucinated citation should trigger Flash correction."""
        mock_citation_svc = MagicMock()
        mock_citation_svc.extract_case_citations = MagicMock(return_value=[])
        mock_citation_svc.verify_case_citations = MagicMock(return_value={"verified": [], "not_found": []})
        mock_citation_svc.extract_citations = MagicMock(return_value=[
            {"code_name": "test", "article_number": "მუხლი 999"}
        ])
        mock_citation_svc.verify_against_corpus = MagicMock(return_value={
            "verified": [],
            "not_found": [{"code_name": "test", "article_number": "მუხლი 999"}],
            "corpus_found": [],
        })
        mock_citation_svc.verify_citations = MagicMock(return_value=[])

        mock_gemini.generate = AsyncMock(return_value="corrected response")
        svc = AgentPipelineService(gemini=mock_gemini, citation_svc=mock_citation_svc)
        text, citations, iters = await svc._phase_3_verify("bad response", [{"chunk_id": "1"}])
        assert iters == MAX_VERIFY_ITERATIONS
        mock_gemini.generate.assert_called()

    @pytest.mark.asyncio
    async def test_no_citations(self, mock_gemini):
        """No citations in text → return immediately."""
        mock_citation_svc = MagicMock()
        mock_citation_svc.extract_case_citations = MagicMock(return_value=[])
        mock_citation_svc.verify_case_citations = MagicMock(return_value={"verified": [], "not_found": []})
        mock_citation_svc.extract_citations = MagicMock(return_value=[])

        svc = AgentPipelineService(gemini=mock_gemini, citation_svc=mock_citation_svc)
        text, citations, iters = await svc._phase_3_verify("no citations here", [{"chunk_id": "1"}])
        assert citations == []
        assert iters == 0


# ── Full run tests ───────────────────────────────────────────

class TestFullRun:
    """Full pipeline run tests."""

    @pytest.mark.asyncio
    async def test_direct_response(self, mock_gemini):
        """Greeting intent should skip RAG and return direct response."""
        plan_json = json.dumps({
            "needs_rag": False,
            "direct_response": "Hello!",
            "intent": "greeting",
        })
        mock_response = MagicMock()
        mock_response.text = plan_json
        mock_chat = MagicMock()
        mock_chat.send_message = AsyncMock(return_value=mock_response)
        mock_gemini.create_chat = AsyncMock(return_value=mock_chat)

        svc = AgentPipelineService(gemini=mock_gemini)
        result = await svc.run(user_message="Hello")
        assert isinstance(result, PipelineResult)
        assert result.response_text == "Hello!"
        assert result.chunks == []

    @pytest.mark.asyncio
    async def test_legal_question_flow(self, mock_gemini, mock_chroma, mock_embedding):
        """Legal question should go through all 3 phases."""
        # Phase 1: plan
        plan_json = json.dumps({
            "needs_rag": True,
            "search_queries": ["query1"],
            "intent": "legal_question",
        })
        mock_plan_response = MagicMock()
        mock_plan_response.text = plan_json
        mock_plan_chat = MagicMock()
        mock_plan_chat.send_message = AsyncMock(return_value=mock_plan_response)

        # Phase 2: execute — response with text, no function calls
        mock_exec_response = MagicMock()
        mock_exec_response.text = "Legal analysis response"
        mock_exec_response.candidates = []
        mock_exec_chat = MagicMock()
        mock_exec_chat.send_message = AsyncMock(return_value=mock_exec_response)

        # Make create_chat return different chats for phase 1 vs 2
        call_count = [0]
        def create_chat_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_plan_chat
            return mock_exec_chat

        mock_gemini.create_chat = AsyncMock(side_effect=create_chat_side_effect)

        # Citation service
        mock_citation_svc = MagicMock()
        mock_citation_svc.extract_case_citations = MagicMock(return_value=[])
        mock_citation_svc.verify_case_citations = MagicMock(return_value={"verified": [], "not_found": []})
        mock_citation_svc.extract_citations = MagicMock(return_value=[])

        # RAG service
        mock_rag = AsyncMock()
        mock_rag.retrieve = AsyncMock(return_value=[
            {"chunk_id": "c1", "content": "law text",
             "metadata": {"_collection": "georgian_laws"}}
        ])

        svc = AgentPipelineService(
            gemini=mock_gemini,
            rag=mock_rag,
            citation_svc=mock_citation_svc,
        )
        result = await svc.run(user_message="რა სასჯელი?")
        assert isinstance(result, PipelineResult)
        assert result.response_text == "Legal analysis response"
        assert len(result.chunks) == 1


# ── _format_verification_results tests ───────────────────────

class TestFormatVerificationResults:
    """Verification result formatting."""

    def test_verified(self):
        verification = {
            "verified": [{"code_name": "test", "article_number": "მუხლი 1"}],
            "not_found": [],
            "corpus_found": [],
        }
        result = AgentPipelineService._format_verification_results(verification)
        assert "VERIFIED" in result
        assert "✅" in result

    def test_not_found(self):
        verification = {
            "verified": [],
            "not_found": [{"code_name": "test", "article_number": "მუხლი 999"}],
            "corpus_found": [],
        }
        result = AgentPipelineService._format_verification_results(verification)
        assert "NOT_FOUND" in result
        assert "❌" in result

    def test_corpus_found(self):
        verification = {
            "verified": [],
            "not_found": [],
            "corpus_found": [{"code_name": "test", "article_number": "მუხლი 1", "corpus_code_name": "real"}],
        }
        result = AgentPipelineService._format_verification_results(verification)
        assert "FOUND_NOT_IN_CONTEXT" in result
