"""
Feedback repository — CRUD + aggregation for the feedback table.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackRepository:
    """Data access layer for feedback records."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs) -> Feedback:
        fb = Feedback(id=uuid.uuid4(), **kwargs)
        self._db.add(fb)
        await self._db.flush()
        logger.info("feedback_created", id=str(fb.id))
        return fb

    async def get_by_id(self, feedback_id: uuid.UUID) -> Feedback | None:
        stmt = select(Feedback).where(Feedback.id == feedback_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_target(
        self, target_type: str, target_id: uuid.UUID, limit: int = 100
    ) -> list[Feedback]:
        stmt = (
            select(Feedback)
            .where(Feedback.target_type == target_type, Feedback.target_id == target_id)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def average_rating_for_target(
        self, target_type: str, target_id: uuid.UUID
    ) -> float:
        stmt = select(func.avg(Feedback.rating)).where(
            Feedback.target_type == target_type, Feedback.target_id == target_id
        )
        result = await self._db.execute(stmt)
        avg = result.scalar_one_or_none()
        return round(float(avg), 2) if avg else 0.0

    async def count_for_target(self, target_type: str, target_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Feedback)
            .where(Feedback.target_type == target_type, Feedback.target_id == target_id)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def total_count(self) -> int:
        stmt = select(func.count()).select_from(Feedback)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def average_per_category(self) -> list[dict]:
        """Returns [{category, avg, count}, ...] across all feedback."""
        stmt = (
            select(
                Feedback.category,
                func.avg(Feedback.rating).label("avg"),
                func.count().label("count"),
            )
            .group_by(Feedback.category)
        )
        result = await self._db.execute(stmt)
        return [
            {"category": row.category, "avg": round(float(row.avg), 2), "count": row.count}
            for row in result.all()
        ]

    async def worst_targets(self, limit: int = 10) -> list[dict]:
        """Returns targets with the lowest average rating."""
        stmt = (
            select(
                Feedback.target_id,
                Feedback.target_type,
                func.avg(Feedback.rating).label("avg_rating"),
                func.count().label("feedback_count"),
            )
            .group_by(Feedback.target_id, Feedback.target_type)
            .having(func.count() >= 2)
            .order_by(func.avg(Feedback.rating).asc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return [
            {
                "target_id": str(row.target_id),
                "target_type": row.target_type,
                "avg_rating": round(float(row.avg_rating), 2),
                "feedback_count": row.feedback_count,
            }
            for row in result.all()
        ]

    async def update(self, feedback_id: uuid.UUID, **kwargs) -> Feedback | None:
        fb = await self.get_by_id(feedback_id)
        if not fb:
            return None
        for k, v in kwargs.items():
            if hasattr(fb, k) and v is not None:
                setattr(fb, k, v)
        await self._db.flush()
        return fb

    async def delete(self, feedback_id: uuid.UUID) -> bool:
        stmt = delete(Feedback).where(Feedback.id == feedback_id)
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount > 0
