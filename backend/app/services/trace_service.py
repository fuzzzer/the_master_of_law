"""
Trace Service — full-transparency recording of the AI pipeline.

A TraceRecorder is started per user request (REST chat, WS chat, case agent)
and propagated implicitly through a contextvar, so any service in the
pipeline can call record_step(...) without new parameters. When the request
finishes, save_current_trace persists the recorder to the pipeline_traces
table in its own DB session so tracing never interferes with the request's
transaction.

Usage:
    start_trace(entry_point="rest_chat", user_message="...", ...)
    record_step("rag_vector_search", hit_count=42, hits=[...])
    await save_current_trace(status="completed", response_text="...")
"""

from __future__ import annotations

import json
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.config.settings import settings
from app.models.database import get_session_factory
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Hard cap per string value inside step data — keeps rows bounded while
# preserving full prompts/responses (law chunks and prompts stay well below it).
MAX_VALUE_CHARS = 30_000

_current_trace: ContextVar[TraceRecorder | None] = ContextVar("current_trace", default=None)


def _jsonable(value: Any, depth: int = 0) -> Any:
    """Convert arbitrary step data into JSON-safe, size-bounded structures."""
    if depth > 8:
        return str(value)[:MAX_VALUE_CHARS]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if len(value) > MAX_VALUE_CHARS:
            return value[:MAX_VALUE_CHARS] + f"… [clipped, {len(value)} chars total]"
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v, depth + 1) for v in value]
    return str(value)[:MAX_VALUE_CHARS]


class TraceRecorder:
    """Collects the ordered pipeline steps of one user request."""

    def __init__(
        self,
        entry_point: str,
        user_message: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.entry_point = entry_point
        self.user_message = user_message
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.started_at = datetime.now(timezone.utc)
        self.steps: list[dict] = []
        self.status = "running"
        self.response_text: str | None = None
        self.error: str | None = None
        self._started_monotonic = time.monotonic()

    def add_step(self, name: str, data: dict[str, Any]) -> None:
        """Append one pipeline step with elapsed time since request start."""
        self.steps.append({
            "seq": len(self.steps) + 1,
            "step": name,
            "at_ms": int((time.monotonic() - self._started_monotonic) * 1000),
            "data": _jsonable(data),
        })

    def finish(self, status: str, response_text: str | None = None, error: str | None = None) -> None:
        """Mark the trace as done."""
        self.status = status
        self.response_text = response_text
        self.error = error

    @property
    def duration_ms(self) -> int:
        return int((time.monotonic() - self._started_monotonic) * 1000)


def start_trace(
    entry_point: str,
    user_message: str,
    user_id: str | None = None,
    conversation_id: str | None = None,
) -> TraceRecorder | None:
    """Begin recording a new trace for the current request context."""
    if not settings.trace_enabled:
        _current_trace.set(None)
        return None
    recorder = TraceRecorder(
        entry_point=entry_point,
        user_message=user_message,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    _current_trace.set(recorder)
    return recorder


def get_current_trace() -> TraceRecorder | None:
    """Return the active trace recorder, if any."""
    return _current_trace.get()


def record_step(name: str, **data: Any) -> None:
    """Record a pipeline step on the active trace. No-op when tracing is off."""
    trace = _current_trace.get()
    if trace is None:
        return
    try:
        trace.add_step(name, data)
    except Exception as e:
        logger.warning("trace_step_failed", step=name, error=str(e))


async def save_current_trace(
    status: str,
    response_text: str | None = None,
    error: str | None = None,
) -> None:
    """Finish and persist the active trace in its own DB session, then clear it.

    Persistence failures are logged and swallowed — tracing must never break
    the user-facing request.
    """
    trace = _current_trace.get()
    _current_trace.set(None)
    if trace is None:
        return
    trace.finish(status=status, response_text=response_text, error=error)
    try:
        from app.repositories.trace_repository import TraceRepository

        async with get_session_factory()() as db:
            await TraceRepository(db).create(
                trace_id=trace.id,
                entry_point=trace.entry_point,
                status=trace.status,
                user_message=trace.user_message,
                steps=trace.steps,
                conversation_id=trace.conversation_id,
                user_id=trace.user_id,
                response_text=trace.response_text,
                error=trace.error,
                duration_ms=trace.duration_ms,
            )
            await db.commit()
        logger.info(
            "trace_saved",
            trace_id=str(trace.id),
            status=status,
            steps=len(trace.steps),
            duration_ms=trace.duration_ms,
        )
    except Exception as e:
        logger.error("trace_persist_failed", trace_id=str(trace.id), error=str(e))


# ── Export formatting ────────────────────────────────────────

def trace_to_dict(trace: Any) -> dict:
    """Convert a PipelineTrace ORM row to a plain dict for API/export."""
    return {
        "id": str(trace.id),
        "conversation_id": trace.conversation_id,
        "user_id": trace.user_id,
        "entry_point": trace.entry_point,
        "status": trace.status,
        "user_message": trace.user_message,
        "response_text": trace.response_text,
        "error": trace.error,
        "steps": trace.steps or [],
        "duration_ms": trace.duration_ms,
        "created_at": trace.created_at.isoformat() if trace.created_at else None,
    }


def format_trace_markdown(trace: dict) -> str:
    """Render one trace as a human/AI-readable markdown report.

    The output is self-contained: a verification agent can follow every
    exchange (prompt → RAG → LLM → citations → answer) without DB access.
    """
    lines = [
        f"# Pipeline Trace {trace['id']}",
        "",
        f"- **Created:** {trace.get('created_at')}",
        f"- **Entry point:** {trace.get('entry_point')}",
        f"- **Conversation:** {trace.get('conversation_id')}",
        f"- **User:** {trace.get('user_id')}",
        f"- **Status:** {trace.get('status')}",
        f"- **Duration:** {trace.get('duration_ms')} ms",
        "",
        "## User Request",
        "",
        trace.get("user_message") or "(empty)",
        "",
    ]
    if trace.get("error"):
        lines += ["## Error", "", str(trace["error"]), ""]

    lines += ["## Pipeline Steps", ""]
    for step in trace.get("steps", []):
        lines.append(f"### Step {step.get('seq')} — {step.get('step')} (+{step.get('at_ms')} ms)")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(step.get("data", {}), ensure_ascii=False, indent=2, default=str))
        lines.append("```")
        lines.append("")

    lines += ["## Final Response", "", trace.get("response_text") or "(none)", ""]
    return "\n".join(lines)


def format_session_markdown(conversation_id: str, traces: list[dict]) -> str:
    """Render every trace of a conversation as one chronological session report."""
    lines = [
        f"# Session Export — Conversation {conversation_id}",
        "",
        f"- **Interactions:** {len(traces)}",
        f"- **Exported:** {datetime.now(timezone.utc).isoformat()}",
        "",
    ]
    for i, trace in enumerate(traces, 1):
        lines.append(f"\n---\n\n# Interaction {i} of {len(traces)}\n")
        lines.append(format_trace_markdown(trace))
    return "\n".join(lines)
