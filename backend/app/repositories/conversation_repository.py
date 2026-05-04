"""
Conversation repository — CRUD for the conversations table.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationRepository:
    """Data access layer for conversation records."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        user_id: str,
        title: str | None = None,
        phase: str = "GREETING",
    ) -> Conversation:
        """Create a new conversation."""
        conv = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title or "New Conversation",
            phase=phase,
        )
        self._db.add(conv)
        await self._db.flush()
        logger.info("conversation_created", id=str(conv.id), user_id=user_id)
        return conv

    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Fetch a conversation by ID."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """List conversations for a user, most recent first."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: str) -> int:
        """Count total conversations for a user."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Conversation).where(
            Conversation.user_id == user_id
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def update_phase(
        self,
        conversation_id: uuid.UUID,
        phase: str,
    ) -> Conversation | None:
        """Update the conversation phase."""
        conv = await self.get_by_id(conversation_id)
        if conv:
            conv.phase = phase
            conv.updated_at = datetime.now(timezone.utc)
            await self._db.flush()
            logger.info("conversation_phase_updated", id=str(conversation_id), phase=phase)
        return conv

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        title: str,
    ) -> Conversation | None:
        """Update the conversation title."""
        conv = await self.get_by_id(conversation_id)
        if conv:
            conv.title = title
            conv.updated_at = datetime.now(timezone.utc)
            await self._db.flush()
        return conv

    async def update_legal_domain(
        self,
        conversation_id: uuid.UUID,
        legal_domain: str,
    ) -> Conversation | None:
        """Update the detected legal domain."""
        conv = await self.get_by_id(conversation_id)
        if conv:
            conv.legal_domain = legal_domain
            conv.updated_at = datetime.now(timezone.utc)
            await self._db.flush()
        return conv

    async def delete(self, conversation_id: uuid.UUID) -> bool:
        """Delete a conversation (cascades to messages via FK)."""
        stmt = delete(Conversation).where(Conversation.id == conversation_id)
        result = await self._db.execute(stmt)
        await self._db.flush()
        deleted = result.rowcount > 0
        if deleted:
            logger.info("conversation_deleted", id=str(conversation_id))
        return deleted
