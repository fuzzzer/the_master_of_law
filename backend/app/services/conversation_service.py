"""
Conversation orchestrator service — state machine for conversation lifecycle.

Manages the 6-phase conversation flow:
  GREETING → INTAKE → CLARIFICATION → ANALYSIS → ADVICE → FOLLOW_UP

This is the central coordinator: it decides what to do with each user message
based on the current conversation phase.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import ConversationPhase, CreditAction
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Valid phase transitions
_VALID_TRANSITIONS: dict[ConversationPhase, list[ConversationPhase]] = {
    ConversationPhase.GREETING: [ConversationPhase.INTAKE],
    ConversationPhase.INTAKE: [ConversationPhase.QUESTIONNAIRE, ConversationPhase.CLARIFICATION, ConversationPhase.ANALYSIS],
    ConversationPhase.QUESTIONNAIRE: [ConversationPhase.CLARIFICATION, ConversationPhase.ANALYSIS],
    ConversationPhase.CLARIFICATION: [ConversationPhase.ANALYSIS, ConversationPhase.INTAKE],
    ConversationPhase.ANALYSIS: [ConversationPhase.ADVICE],
    ConversationPhase.ADVICE: [ConversationPhase.FOLLOW_UP, ConversationPhase.ANALYSIS],
    ConversationPhase.FOLLOW_UP: [ConversationPhase.ANALYSIS, ConversationPhase.QUESTIONNAIRE, ConversationPhase.FOLLOW_UP],
}


class ConversationService:
    """
    Orchestrates the conversation lifecycle.

    Called by the chat router after RAG retrieval and analysis
    to decide phase transitions and manage conversation state.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._conv_repo = ConversationRepository(db)
        self._msg_repo = MessageRepository(db)

    async def create_conversation(
        self,
        user_id: str,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Start a new conversation in GREETING phase."""
        conv = await self._conv_repo.create(
            user_id=user_id,
            title=title,
            phase=ConversationPhase.GREETING.value,
        )
        return self._conv_to_dict(conv)

    async def update_title(self, conversation_id: str, title: str) -> None:
        """Update the title of a conversation."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return
        await self._conv_repo.update_title(conv_uuid, title)

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation with messages."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return None

        conv = await self._conv_repo.get_by_id(conv_uuid)
        if not conv:
            return None

        messages = await self._msg_repo.get_for_conversation(conv_uuid)
        result = self._conv_to_dict(conv)
        result["messages"] = [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "citations": m.citations,
                "credit_cost": m.credit_cost,
                "created_at": m.created_at.isoformat() if m.created_at else "",
            }
            for m in messages
        ]
        return result

    async def list_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List conversations for a user."""
        convs = await self._conv_repo.list_for_user(user_id, limit, offset)
        total = await self._conv_repo.count_for_user(user_id)
        return [self._conv_to_dict(c) for c in convs], total

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its messages."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return False

        # Delete messages first (FK constraint)
        await self._msg_repo.delete_for_conversation(conv_uuid)
        return await self._conv_repo.delete(conv_uuid)

    async def save_user_message(
        self,
        conversation_id: str,
        content: str,
    ) -> dict[str, Any] | None:
        """Persist a user's message."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return None

        msg = await self._msg_repo.create(
            conversation_id=conv_uuid,
            role="user",
            content=content,
        )
        return {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else "",
        }

    async def save_assistant_message(
        self,
        conversation_id: str,
        content: str,
        citations: list[dict] | None = None,
        retrieved_chunk_ids: list[str] | None = None,
        credit_cost: int = 1,
    ) -> dict[str, Any] | None:
        """Persist the AI assistant's response."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return None

        msg = await self._msg_repo.create(
            conversation_id=conv_uuid,
            role="assistant",
            content=content,
            citations=citations,
            retrieved_chunk_ids=retrieved_chunk_ids,
            credit_cost=credit_cost,
        )
        return {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "citations": msg.citations,
            "credit_cost": msg.credit_cost,
            "created_at": msg.created_at.isoformat() if msg.created_at else "",
        }

    async def get_conversation_history(
        self,
        conversation_id: str,
        max_messages: int = 20,
    ) -> list[dict[str, str]]:
        """
        Get conversation history formatted for Gemini context.

        Returns list of {"role": "user"|"assistant", "content": "..."}.
        """
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return []

        messages = await self._msg_repo.get_for_conversation(conv_uuid, limit=max_messages)
        return [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

    async def transition_phase(
        self,
        conversation_id: str,
        new_phase: ConversationPhase,
    ) -> bool:
        """
        Transition the conversation to a new phase.

        Validates that the transition is allowed by the state machine.
        """
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return False

        conv = await self._conv_repo.get_by_id(conv_uuid)
        if not conv:
            return False

        try:
            current_phase = ConversationPhase(conv.phase)
        except ValueError:
            current_phase = ConversationPhase.GREETING

        valid_next = _VALID_TRANSITIONS.get(current_phase, [])
        if new_phase not in valid_next:
            logger.warning(
                "invalid_phase_transition",
                conv_id=conversation_id,
                current=current_phase.value,
                requested=new_phase.value,
            )
            # Allow the transition anyway — the state machine is a guide, not a gate
            # This prevents edge-case deadlocks

        await self._conv_repo.update_phase(conv_uuid, new_phase.value)
        return True

    async def mark_case_ready(self, conversation_id: str) -> None:
        """Flag a conversation as ready for case file generation."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return
        conv = await self._conv_repo.get_by_id(conv_uuid)
        if conv:
            conv.case_ready = True
            await self._db.flush()

    async def determine_next_phase(
        self,
        conversation_id: str,
        message_count: int,
    ) -> ConversationPhase:
        """
        Determine what phase the conversation should be in.

        Simple heuristic for now — can be made smarter with Gemini.
        """
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return ConversationPhase.GREETING

        conv = await self._conv_repo.get_by_id(conv_uuid)
        if not conv:
            return ConversationPhase.GREETING

        current = conv.phase

        # First message → move from GREETING to INTAKE
        if current == ConversationPhase.GREETING.value and message_count >= 1:
            return ConversationPhase.INTAKE

        # INTAKE stays as INTAKE — user explicitly chooses when to proceed
        # (via questionnaire, free-text extract, or skip-to-analysis)

        # After questionnaire → move to ANALYSIS
        if current == ConversationPhase.QUESTIONNAIRE.value:
            return ConversationPhase.ANALYSIS

        # After analysis → ADVICE
        if current == ConversationPhase.ANALYSIS.value:
            return ConversationPhase.ADVICE

        # After advice → FOLLOW_UP
        if current == ConversationPhase.ADVICE.value:
            return ConversationPhase.FOLLOW_UP

        try:
            return ConversationPhase(current)
        except ValueError:
            return ConversationPhase.GREETING

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _parse_uuid(value: str) -> uuid.UUID | None:
        """Parse a string UUID, returning None if invalid."""
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _conv_to_dict(conv) -> dict[str, Any]:
        """Convert a Conversation ORM instance to a plain dict."""
        return {
            "id": str(conv.id),
            "user_id": conv.user_id,
            "title": conv.title or "",
            "phase": conv.phase,
            "legal_domain": conv.legal_domain or "",
            "case_ready": conv.case_ready if conv.case_ready is not None else False,
            "created_at": conv.created_at.isoformat() if conv.created_at else "",
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else "",
        }
