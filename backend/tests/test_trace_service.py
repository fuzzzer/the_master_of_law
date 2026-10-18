"""
Tests for the pipeline trace transparency system (trace_service).
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import trace_service
from app.services.trace_service import (
    MAX_VALUE_CHARS,
    TraceRecorder,
    _jsonable,
    format_session_markdown,
    format_trace_markdown,
    get_current_trace,
    record_step,
    save_current_trace,
    start_trace,
)


@pytest.fixture(autouse=True)
def clean_trace_context():
    """Ensure no trace leaks between tests."""
    trace_service._current_trace.set(None)
    yield
    trace_service._current_trace.set(None)


# ── TraceRecorder ────────────────────────────────────────────

def test_recorder_records_steps_in_order():
    recorder = TraceRecorder(entry_point="rest_chat", user_message="hello")
    recorder.add_step("first", {"a": 1})
    recorder.add_step("second", {"b": 2})

    assert [s["seq"] for s in recorder.steps] == [1, 2]
    assert [s["step"] for s in recorder.steps] == ["first", "second"]
    assert recorder.steps[0]["data"] == {"a": 1}
    assert recorder.steps[0]["at_ms"] >= 0


def test_recorder_finish_sets_status_and_response():
    recorder = TraceRecorder(entry_point="ws_chat", user_message="q")
    recorder.finish(status="completed", response_text="answer")

    assert recorder.status == "completed"
    assert recorder.response_text == "answer"
    assert recorder.duration_ms >= 0


# ── Contextvar API ───────────────────────────────────────────

def test_record_step_is_noop_without_active_trace():
    record_step("orphan_step", data="ignored")  # must not raise
    assert get_current_trace() is None


def test_start_trace_then_record_step_appends():
    recorder = start_trace(entry_point="rest_chat", user_message="q", user_id="u1", conversation_id="c1")

    record_step("rag_vector_search", hit_count=3)

    assert recorder is get_current_trace()
    assert recorder.conversation_id == "c1"
    assert len(recorder.steps) == 1
    assert recorder.steps[0]["step"] == "rag_vector_search"
    assert recorder.steps[0]["data"]["hit_count"] == 3


def test_start_trace_disabled_returns_none():
    with patch.object(trace_service.settings, "trace_enabled", False):
        recorder = start_trace(entry_point="rest_chat", user_message="q")

    assert recorder is None
    record_step("anything", x=1)  # no-op, must not raise
    assert get_current_trace() is None


@pytest.mark.asyncio
async def test_trace_survives_into_asyncio_task():
    """The WS router runs the pipeline in asyncio.create_task — the contextvar
    is copied into the task, so steps recorded there land on the same recorder."""
    recorder = start_trace(entry_point="ws_chat", user_message="q")

    async def pipeline_stage():
        record_step("inside_task", ok=True)

    await asyncio.create_task(pipeline_stage())

    assert len(recorder.steps) == 1
    assert recorder.steps[0]["step"] == "inside_task"


# ── _jsonable ────────────────────────────────────────────────

def test_jsonable_clips_long_strings():
    long = "x" * (MAX_VALUE_CHARS + 500)
    result = _jsonable(long)
    assert len(result) < len(long)
    assert "[clipped" in result


def test_jsonable_converts_non_serializable_objects():
    class Weird:
        def __str__(self):
            return "weird-object"

    result = _jsonable({"obj": Weird(), "nested": [{"n": Weird()}], "num": 4})
    assert result["obj"] == "weird-object"
    assert result["nested"][0]["n"] == "weird-object"
    assert result["num"] == 4


# ── Persistence ──────────────────────────────────────────────

def _mock_session_factory(mock_db):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_db)
    cm.__aexit__ = AsyncMock(return_value=False)
    factory = MagicMock(return_value=cm)
    return MagicMock(return_value=factory)


@pytest.mark.asyncio
async def test_save_current_trace_persists_and_clears():
    recorder = start_trace(entry_point="rest_chat", user_message="q", conversation_id="c1")
    record_step("step_one", a=1)

    mock_db = AsyncMock()
    with patch.object(trace_service, "get_session_factory", _mock_session_factory(mock_db)), \
         patch("app.repositories.trace_repository.TraceRepository") as repo_cls:
        repo_cls.return_value.create = AsyncMock()
        await save_current_trace(status="completed", response_text="answer")

        create_kwargs = repo_cls.return_value.create.call_args.kwargs
        assert create_kwargs["trace_id"] == recorder.id
        assert create_kwargs["status"] == "completed"
        assert create_kwargs["response_text"] == "answer"
        assert create_kwargs["conversation_id"] == "c1"
        assert len(create_kwargs["steps"]) == 1
        mock_db.commit.assert_awaited_once()

    assert get_current_trace() is None


@pytest.mark.asyncio
async def test_save_current_trace_without_active_trace_is_noop():
    with patch.object(trace_service, "get_session_factory") as factory:
        await save_current_trace(status="completed")
        factory.assert_not_called()


@pytest.mark.asyncio
async def test_save_current_trace_swallows_persistence_errors():
    start_trace(entry_point="rest_chat", user_message="q")
    with patch.object(trace_service, "get_session_factory", side_effect=RuntimeError("db down")):
        await save_current_trace(status="failed", error="boom")  # must not raise
    assert get_current_trace() is None


# ── Export formatting ────────────────────────────────────────

def _sample_trace_dict() -> dict:
    return {
        "id": "11111111-1111-1111-1111-111111111111",
        "conversation_id": "conv-1",
        "user_id": "user-1",
        "entry_point": "ws_chat",
        "status": "completed",
        "user_message": "რა ჯარიმაა სწრაფი მართვისთვის?",
        "response_text": "ადმინისტრაციული ჯარიმა...",
        "error": None,
        "steps": [
            {"seq": 1, "step": "request_received", "at_ms": 0, "data": {"message": "q"}},
            {"seq": 2, "step": "rag_final_selection", "at_ms": 900, "data": {"result_count": 5}},
        ],
        "duration_ms": 4200,
        "created_at": "2026-07-19T10:00:00+00:00",
    }


def test_format_trace_markdown_contains_all_sections():
    md = format_trace_markdown(_sample_trace_dict())

    assert "# Pipeline Trace 11111111" in md
    assert "რა ჯარიმაა სწრაფი მართვისთვის?" in md
    assert "request_received" in md
    assert "rag_final_selection" in md
    assert "ადმინისტრაციული ჯარიმა..." in md
    assert "4200 ms" in md


def test_format_session_markdown_concatenates_traces():
    traces = [_sample_trace_dict(), _sample_trace_dict()]
    md = format_session_markdown("conv-1", traces)

    assert "Session Export — Conversation conv-1" in md
    assert "Interaction 1 of 2" in md
    assert "Interaction 2 of 2" in md
