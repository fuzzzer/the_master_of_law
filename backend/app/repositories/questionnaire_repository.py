"""
Questionnaire repository — CRUD for questionnaire items.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.questionnaire import QuestionnaireItem


class QuestionnaireRepository:
    """Async repository for questionnaire item operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_items(
        self,
        conversation_id: uuid.UUID,
        questions: list[dict[str, Any]],
    ) -> list[QuestionnaireItem]:
        """Bulk-insert generated questions for a conversation."""
        items = []
        for idx, q in enumerate(questions):
            item = QuestionnaireItem(
                conversation_id=conversation_id,
                question_id=q["question_id"],
                question_text_ka=q["question_text_ka"],
                question_type=q["question_type"],
                options=q.get("options"),
                required=q.get("required", True),
                purpose=q.get("purpose"),
                legal_relevance=q.get("legal_relevance"),
                sort_order=idx,
            )
            self._db.add(item)
            items.append(item)
        await self._db.flush()
        return items

    async def get_items_for_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> list[QuestionnaireItem]:
        """Get all questionnaire items for a conversation, ordered."""
        result = await self._db.execute(
            select(QuestionnaireItem)
            .where(QuestionnaireItem.conversation_id == conversation_id)
            .order_by(QuestionnaireItem.sort_order)
        )
        return list(result.scalars().all())

    async def get_item_by_question_id(
        self,
        conversation_id: uuid.UUID,
        question_id: str,
    ) -> QuestionnaireItem | None:
        """Get a specific questionnaire item by its question_id."""
        result = await self._db.execute(
            select(QuestionnaireItem).where(
                QuestionnaireItem.conversation_id == conversation_id,
                QuestionnaireItem.question_id == question_id,
            )
        )
        return result.scalar_one_or_none()

    async def save_answer(
        self,
        conversation_id: uuid.UUID,
        question_id: str,
        answer_value: str,
    ) -> QuestionnaireItem | None:
        """Save an answer to a question."""
        result = await self._db.execute(
            update(QuestionnaireItem)
            .where(
                QuestionnaireItem.conversation_id == conversation_id,
                QuestionnaireItem.question_id == question_id,
            )
            .values(
                answer_value=answer_value,
                skipped=False,
                answered_at=func.now(),
            )
            .returning(QuestionnaireItem)
        )
        return result.scalar_one_or_none()

    async def skip_question(
        self,
        conversation_id: uuid.UUID,
        question_id: str,
    ) -> QuestionnaireItem | None:
        """Mark a question as skipped."""
        result = await self._db.execute(
            update(QuestionnaireItem)
            .where(
                QuestionnaireItem.conversation_id == conversation_id,
                QuestionnaireItem.question_id == question_id,
            )
            .values(
                skipped=True,
                answer_value=None,
                answered_at=func.now(),
            )
            .returning(QuestionnaireItem)
        )
        return result.scalar_one_or_none()

    async def delete_items_for_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> int:
        """Delete all questionnaire items for a conversation (e.g., on regenerate)."""
        result = await self._db.execute(
            QuestionnaireItem.__table__.delete().where(
                QuestionnaireItem.conversation_id == conversation_id
            )
        )
        return result.rowcount or 0

    async def count_answered(
        self,
        conversation_id: uuid.UUID,
    ) -> tuple[int, int]:
        """Return (answered_count, total_count) for a conversation."""
        items = await self.get_items_for_conversation(conversation_id)
        total = len(items)
        answered = sum(1 for i in items if i.answer_value is not None or i.skipped)
        return answered, total
