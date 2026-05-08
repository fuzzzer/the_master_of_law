"""
Feedback repository — CRUD + aggregation queries for feedback table.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackRepository:
    """Data access layer for feedback entries."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs) -> Feedback:
        """Create a new feedback entry."""
        fb = Feedback(**kwargs)
        self._db.add(fb)
        await self._db.flush()
        logger.info("feedback_created", id=str(fb.id), target_type=fb.target_type, target_id=str(fb.target_id))
        return fb

    async def get_by_id(self, feedback_id: uuid.UUID) -> Feedback | None:
        stmt = select(Feedback).where(Feedback.id == feedback_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_target(
        self,
        target_id: uuid.UUID,
        target_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Feedback]:
        stmt = (
            select(Feedback)
            .where(Feedback.target_id == target_id, Feedback.target_type == target_type)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_for_target(self, target_id: uuid.UUID, target_type: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Feedback)
            .where(Feedback.target_id == target_id, Feedback.target_type == target_type)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def average_rating_for_target(self, target_id: uuid.UUID, target_type: str) -> float:
        stmt = (
            select(func.avg(Feedback.rating))
            .where(Feedback.target_id == target_id, Feedback.target_type == target_type)
        )
        result = await self._db.execute(stmt)
        avg = result.scalar_one()
        return float(avg) if avg is not None else 0.0

    async def update(self, feedback_id: uuid.UUID, **kwargs) -> Feedback | None:
        fb = await self.get_by_id(feedback_id)
        if not fb:
            return None
        for k, v in kwargs.items():
            if hasattr(fb, k) and v is not None:
                setattr(fb, k, v)
        fb.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return fb

    async def delete(self, feedback_id: uuid.UUID) -> bool:
        stmt = delete(Feedback).where(Feedback.id == feedback_id)
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount > 0

    async def get_summary(self) -> dict[str, Any]:
        """Aggregated stats across all feedback."""
        total_stmt = select(func.count(), func.avg(Feedback.rating)).select_from(Feedback)
        result = await self._db.execute(total_stmt)
        total_count, overall_avg = result.one()

        category_stmt = (
            select(Feedback.category, func.count(), func.avg(Feedback.rating))
            .group_by(Feedback.category)
            .order_by(func.avg(Feedback.rating).asc())
        )
        cat_result = await self._db.execute(category_stmt)
        by_category = [
            {
                "category": row[0],
                "total_count": row[1],
                "average_rating": float(row[2]) if row[2] is not None else 0.0,
            }
            for row in cat_result.all()
        ]

        reviewer_stmt = (
            select(Feedback.reviewer_type, func.count())
            .group_by(Feedback.reviewer_type)
        )
        rev_result = await self._db.execute(reviewer_stmt)
        by_reviewer = {row[0]: row[1] for row in rev_result.all()}

        return {
            "overall_average": float(overall_avg) if overall_avg is not None else 0.0,
            "total_feedback_count": total_count or 0,
            "by_category": by_category,
            "by_reviewer_type": by_reviewer,
        }

    async def get_category_trends(self) -> dict[str, list[dict[str, Any]]]:
        """Average rating per category grouped by month."""
        stmt = (
            select(
                Feedback.category,
                func.to_char(Feedback.created_at, "YYYY-MM").label("period"),
                func.count().label("count"),
                func.avg(Feedback.rating).label("avg_rating"),
            )
            .group_by(Feedback.category, func.to_char(Feedback.created_at, "YYYY-MM"))
            .order_by("period")
        )
        result = await self._db.execute(stmt)
        trends: dict[str, list[dict[str, Any]]] = {}
        for row in result.all():
            cat, period, count, avg_rating = row
            trends.setdefault(cat, []).append(
                {
                    "period": period,
                    "count": count,
                    "average_rating": float(avg_rating) if avg_rating is not None else 0.0,
                }
            )
        return trends
