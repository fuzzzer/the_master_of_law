"""
Message repository — persistence for chat messages.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MessageRepository:
    """Data access layer for chat messages."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        citations: list[dict] | None = None,
        retrieved_chunk_ids: list[str] | None = None,
        credit_cost: int = 0,
    ) -> Message:
        """Persist a new message."""
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations,
            retrieved_chunk_ids=retrieved_chunk_ids,
            credit_cost=credit_cost,
            created_at=datetime.now(timezone.utc),
        )
        self._db.add(msg)
        await self._db.flush()
        return msg

    async def get_for_conversation(
        self,
        conversation_id: uuid.UUID,
        limit: int = 100,
    ) -> list[Message]:
        """Get all messages for a conversation, ordered chronologically."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.role.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def delete_for_conversation(self, conversation_id: uuid.UUID) -> int:
        """Delete all messages for a conversation. Returns count deleted."""
        stmt = delete(Message).where(Message.conversation_id == conversation_id)
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount
