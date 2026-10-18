"""
Trace router — pipeline transparency and debugging (ADMIN only).

GET /api/v1/traces                                  — list traces (filterable)
GET /api/v1/traces/sessions                         — traces grouped per conversation
GET /api/v1/traces/dashboard                        — HTML debugging dashboard
GET /api/v1/traces/{trace_id}                       — full step-by-step trace
GET /api/v1/traces/{trace_id}/export                — export one trace (json | markdown | text)
GET /api/v1/traces/conversation/{conversation_id}/export — export a whole session
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.repositories.trace_repository import TraceRepository
from app.services.trace_service import (
    format_session_markdown,
    format_trace_markdown,
    trace_to_dict,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])

_DASHBOARD_PATH = Path(__file__).resolve().parents[1] / "static" / "trace_dashboard.html"

_EXPORT_MEDIA = {
    "json": ("application/json", "json"),
    "markdown": ("text/markdown; charset=utf-8", "md"),
    "text": ("text/plain; charset=utf-8", "txt"),
}


def require_admin(request: Request) -> None:
    """Trace data may contain any user's messages — admins only."""
    user = getattr(request.state, "user", None)
    if not user or user.get("tier") not in ("ADMIN", "SUPERADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/dashboard")
async def trace_dashboard():
    """Serve the self-contained HTML debugging dashboard.

    The page itself holds no data; every fetch it makes goes through the
    admin-guarded endpoints below (X-API-Key header in production).
    """
    if not _DASHBOARD_PATH.exists():
        raise HTTPException(status_code=404, detail="Dashboard file missing")
    return FileResponse(_DASHBOARD_PATH, media_type="text/html")


@router.get("", dependencies=[Depends(require_admin)])
async def list_traces(
    conversation_id: str | None = None,
    user_id: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List trace summaries, newest first."""
    traces = await TraceRepository(db).list_traces(
        conversation_id=conversation_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return {
        "traces": [
            {
                "id": str(t.id),
                "conversation_id": t.conversation_id,
                "user_id": t.user_id,
                "entry_point": t.entry_point,
                "status": t.status,
                "user_message": (t.user_message or "")[:200],
                "response_preview": (t.response_text or "")[:200],
                "step_count": len(t.steps or []),
                "duration_ms": t.duration_ms,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in traces
        ]
    }


@router.get("/sessions", dependencies=[Depends(require_admin)])
async def list_sessions(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Traces grouped per conversation — one row per debugging session."""
    return {"sessions": await TraceRepository(db).list_sessions(limit=limit)}


@router.get("/metrics/grounding", dependencies=[Depends(require_admin)])
async def grounding_metrics(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=500, le=2000),
    db: AsyncSession = Depends(get_db),
):
    """Grounding health rates over recent traces (plan 4.1) — dashboard panel data."""
    from app.services.grounding_metrics_service import compute_grounding_metrics

    traces = await TraceRepository(db).list_recent(days=days, limit=limit)
    return {"days": days, **compute_grounding_metrics(traces)}


@router.get("/{trace_id}", dependencies=[Depends(require_admin)])
async def get_trace(
    trace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Full trace with every recorded pipeline step."""
    trace = await TraceRepository(db).get_by_id(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace_to_dict(trace)


@router.get("/{trace_id}/export", dependencies=[Depends(require_admin)])
async def export_trace(
    trace_id: uuid.UUID,
    format: str = Query(default="markdown", pattern="^(json|markdown|text)$"),
    db: AsyncSession = Depends(get_db),
):
    """Export one interaction as a downloadable file for AI/manual review."""
    trace = await TraceRepository(db).get_by_id(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    data = trace_to_dict(trace)
    media_type, ext = _EXPORT_MEDIA[format]
    filename = f"trace_{trace_id}.{ext}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    if format == "json":
        return JSONResponse(content=data, headers=headers)
    return PlainTextResponse(format_trace_markdown(data), media_type=media_type, headers=headers)


@router.get("/conversation/{conversation_id}/export", dependencies=[Depends(require_admin)])
async def export_session(
    conversation_id: str,
    format: str = Query(default="markdown", pattern="^(json|markdown|text)$"),
    db: AsyncSession = Depends(get_db),
):
    """Export every interaction of a conversation as one chronological report."""
    traces = await TraceRepository(db).list_for_conversation(conversation_id)
    if not traces:
        raise HTTPException(status_code=404, detail="No traces for this conversation")

    data = [trace_to_dict(t) for t in traces]
    media_type, ext = _EXPORT_MEDIA[format]
    filename = f"session_{conversation_id}.{ext}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    if format == "json":
        return JSONResponse(
            content={"conversation_id": conversation_id, "traces": data},
            headers=headers,
        )
    return PlainTextResponse(
        format_session_markdown(conversation_id, data),
        media_type=media_type,
        headers=headers,
    )
