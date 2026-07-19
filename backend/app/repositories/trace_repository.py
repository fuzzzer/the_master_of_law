"""
Trace repository — persistence for pipeline transparency traces.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline_trace import PipelineTrace
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TraceRepository:
    """Data access layer for pipeline traces."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        trace_id: uuid.UUID,
        entry_point: str,
        status: str,
        user_message: str,
        steps: list[dict],
        conversation_id: str | None = None,
        user_id: str | None = None,
        response_text: str | None = None,
        error: str | None = None,
        duration_ms: int | None = None,
    ) -> PipelineTrace:
        """Persist a finished trace."""
        trace = PipelineTrace(
            id=trace_id,
            conversation_id=conversation_id,
            user_id=user_id,
            entry_point=entry_point,
            status=status,
            user_message=user_message,
            response_text=response_text,
            error=error,
            steps=steps,
            duration_ms=duration_ms,
        )
        self._db.add(trace)
        await self._db.flush()
        return trace

    async def get_by_id(self, trace_id: uuid.UUID) -> PipelineTrace | None:
        """Get one trace with all its steps."""
        result = await self._db.execute(
            select(PipelineTrace).where(PipelineTrace.id == trace_id)
        )
        return result.scalar_one_or_none()

    async def list_traces(
        self,
        conversation_id: str | None = None,
        user_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PipelineTrace]:
        """List traces, newest first, optionally filtered."""
        stmt = select(PipelineTrace).order_by(PipelineTrace.created_at.desc())
        if conversation_id:
            stmt = stmt.where(PipelineTrace.conversation_id == conversation_id)
        if user_id:
            stmt = stmt.where(PipelineTrace.user_id == user_id)
        result = await self._db.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def list_for_conversation(self, conversation_id: str) -> list[PipelineTrace]:
        """All traces of one conversation, chronological — the full session."""
        result = await self._db.execute(
            select(PipelineTrace)
            .where(PipelineTrace.conversation_id == conversation_id)
            .order_by(PipelineTrace.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_recent(self, days: int = 7, limit: int = 500) -> list[PipelineTrace]:
        """Completed traces of the last N days, newest first (metrics window)."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self._db.execute(
            select(PipelineTrace)
            .where(PipelineTrace.created_at >= cutoff)
            .where(PipelineTrace.status == "completed")
            .order_by(PipelineTrace.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_sessions(self, limit: int = 50) -> list[dict]:
        """Traces grouped per conversation: count, last activity, last user."""
        stmt = (
            select(
                PipelineTrace.conversation_id,
                func.count(PipelineTrace.id).label("trace_count"),
                func.max(PipelineTrace.created_at).label("last_activity"),
                func.max(PipelineTrace.user_id).label("user_id"),
            )
            .group_by(PipelineTrace.conversation_id)
            .order_by(func.max(PipelineTrace.created_at).desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return [
            {
                "conversation_id": row.conversation_id,
                "trace_count": row.trace_count,
                "last_activity": row.last_activity.isoformat() if row.last_activity else None,
                "user_id": row.user_id,
            }
            for row in result.all()
        ]
