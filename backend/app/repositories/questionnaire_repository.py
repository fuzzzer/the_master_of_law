"""
Questionnaire repository — CRUD for questionnaire_questions and questionnaire_answers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.questionnaire import QuestionnaireAnswer, QuestionnaireQuestion
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuestionnaireRepository:
    """Data access layer for questionnaire questions and answers."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Questions ─────────────────────────────────────────

    async def save_questions(
        self,
        conversation_id: uuid.UUID,
        questions: list[dict],
    ) -> list[QuestionnaireQuestion]:
        """Persist AI-generated questions for a conversation."""
        rows = []
        for i, q in enumerate(questions):
            row = QuestionnaireQuestion(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                question_id=q["question_id"],
                question_text=q["question_text"],
                question_type=q.get("question_type", "text"),
                options=q.get("options"),
                required=q.get("required", True),
                purpose=q.get("purpose"),
                legal_relevance=q.get("legal_relevance"),
                sort_order=i,
            )
            self._db.add(row)
            rows.append(row)
        await self._db.flush()
        logger.info(
            "questionnaire_questions_saved",
            conversation_id=str(conversation_id),
            count=len(rows),
        )
        return rows

    async def get_questions(
        self, conversation_id: uuid.UUID
    ) -> list[QuestionnaireQuestion]:
        """Get all questions for a conversation, ordered by sort_order."""
        stmt = (
            select(QuestionnaireQuestion)
            .where(QuestionnaireQuestion.conversation_id == conversation_id)
            .order_by(QuestionnaireQuestion.sort_order)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def delete_questions(self, conversation_id: uuid.UUID) -> int:
        """Delete all questions for a conversation (used for regeneration)."""
        stmt = delete(QuestionnaireQuestion).where(
            QuestionnaireQuestion.conversation_id == conversation_id
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount

    # ── Answers ──────────────────────────────────────────

    async def save_answer(
        self,
        conversation_id: uuid.UUID,
        question_id: str,
        question_text: str,
        answer_value: str | None,
        answer_type: str,
        skipped: bool = False,
    ) -> QuestionnaireAnswer:
        """Save or update an answer for a question."""
        # Check if answer already exists (allow editing)
        existing = await self._get_answer(conversation_id, question_id)
        if existing:
            existing.answer_value = answer_value
            existing.answer_type = answer_type
            existing.skipped = skipped
            existing.answered_at = datetime.now(timezone.utc)
            await self._db.flush()
            return existing

        row = QuestionnaireAnswer(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            question_id=question_id,
            question_text=question_text,
            answer_value=answer_value,
            answer_type=answer_type,
            skipped=skipped,
        )
        self._db.add(row)
        await self._db.flush()
        return row

    async def get_answers(
        self, conversation_id: uuid.UUID
    ) -> list[QuestionnaireAnswer]:
        """Get all answers for a conversation."""
        stmt = (
            select(QuestionnaireAnswer)
            .where(QuestionnaireAnswer.conversation_id == conversation_id)
            .order_by(QuestionnaireAnswer.answered_at)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def skip_remaining(
        self,
        conversation_id: uuid.UUID,
    ) -> int:
        """Mark all unanswered optional questions as skipped."""
        questions = await self.get_questions(conversation_id)
        answers = await self.get_answers(conversation_id)
        answered_ids = {a.question_id for a in answers}

        skipped_count = 0
        for q in questions:
            if q.question_id in answered_ids:
                continue
            if q.required:
                continue
            await self.save_answer(
                conversation_id=conversation_id,
                question_id=q.question_id,
                question_text=q.question_text,
                answer_value=None,
                answer_type=q.question_type,
                skipped=True,
            )
            skipped_count += 1

        return skipped_count

    async def _get_answer(
        self, conversation_id: uuid.UUID, question_id: str
    ) -> QuestionnaireAnswer | None:
        stmt = select(QuestionnaireAnswer).where(
            QuestionnaireAnswer.conversation_id == conversation_id,
            QuestionnaireAnswer.question_id == question_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
