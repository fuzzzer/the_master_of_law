"""
Calls per question — a free key must answer more than 1–3 questions a day.

Production, 2026-10-01: one labour question made 15–20 model calls, all on
the one model whose free limit is 20 requests a day. Owner's decision
(2026-10-02): mechanical work runs on the lite model by default, a tool law
search makes no model calls, and the model is told the injected code is
complete so it does not search it again.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.config.settings import Settings
from app.services.agent_pipeline_service import AgentPipelineService
from app.services.rag_retrieval_service import RAGRetrievalService


def test_mechanical_work_is_on_a_different_daily_bucket_than_the_answer(monkeypatch):
    for var in ("GEMINI_STRONG_MODEL", "GEMINI_MODEL", "GEMINI_CHEAP_MODEL", "GEMINI_CHAT_MODEL"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.gemini_cheap_model == "gemini-3.5-flash-lite"
    assert s.gemini_cheap_model != s.gemini_strong_model


@pytest.mark.asyncio
async def test_a_tool_law_search_makes_no_model_call():
    """It used to re-run query expansion and a ~28k-token rerank — two model
    calls — to return one article."""
    rag = AsyncMock()
    rag.retrieve = AsyncMock(return_value=[{"content": "t", "metadata": {"article_number": "48"}}])
    svc = AgentPipelineService(gemini=AsyncMock(), rag=rag)

    result = await svc._handle_search_law({"query": "გათავისუფლების ვადა"}, [])

    assert result["found"]
    kwargs = rag.retrieve.await_args.kwargs
    assert kwargs["pre_expanded_queries"] == ["გათავისუფლების ვადა"], "no expansion call"
    assert kwargs["rerank"] is False, "no rerank call"


@pytest.mark.asyncio
async def test_retrieval_without_rerank_calls_no_model(mock_gemini):
    svc = RAGRetrievalService(gemini_client=mock_gemini)
    hits = [{"chunk_id": f"c{i}", "content": "x", "distance": i / 100,
             "metadata": {"_collection": "georgian_laws"}} for i in range(60)]
    svc._stage_1_vector_search = AsyncMock(return_value=hits)
    svc._stage_2_fulltext_search = AsyncMock(return_value=[])
    svc._stage_4_rerank = AsyncMock(side_effect=AssertionError("rerank must not run"))

    out = await svc.retrieve("q", collections=["georgian_laws"], pre_expanded_queries=["q"], rerank=False)

    assert out and out[0]["chunk_id"] == "c0", "best match first"
    mock_gemini.generate.assert_not_called()
    mock_gemini.generate_json.assert_not_called()


def test_the_injected_code_is_declared_complete_and_not_to_be_searched():
    from app.tools.case_tools import SEARCH_LAW_DECLARATION

    header = AgentPipelineService._full_code_header()
    assert "complete" in header and "do not search" in header
    assert "NOT already" in SEARCH_LAW_DECLARATION.description
