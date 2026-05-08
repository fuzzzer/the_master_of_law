"""
Feedback service — singleton for managing feedback lifecycle.

Handles submission, retrieval, aggregation, and trend analysis.
Credit cost: 0 for all feedback operations.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.feedback_repository import FeedbackRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FeedbackService:
    """Business logic for feedback operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = FeedbackRepository(db)

    async def submit_feedback(
        self,
        target_type: str,
        target_id: str,
        reviewer_type: str,
        category: str,
        rating: int,
        comment: str | None = None,
        specific_section: str | None = None,
        reviewer_id: str | None = None,
    ) -> dict[str, Any]:
        """Submit new feedback for a target entity."""
        try:
            target_uuid = uuid.UUID(target_id)
        except ValueError as exc:
            raise ValueError("Invalid target_id UUID") from exc

        reviewer_uuid = None
        if reviewer_id:
            try:
                reviewer_uuid = uuid.UUID(reviewer_id)
            except ValueError:
                # If reviewer_id is not a UUID, treat it as a string-derived UUID
                # (e.g. Firebase UID). Store as None since the schema expects UUID.
                reviewer_uuid = None

        fb = await self._repo.create(
            target_type=target_type,
            target_id=target_uuid,
            reviewer_id=reviewer_uuid,
            reviewer_type=reviewer_type,
            category=category,
            rating=rating,
            comment=comment,
            specific_section=specific_section,
        )

        logger.info(
            "feedback_submitted",
            feedback_id=str(fb.id),
            target_type=target_type,
            target_id=target_id,
            category=category,
            rating=rating,
        )

        return self._to_dict(fb)

    async def get_feedback(
        self,
        target_id: str,
        target_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get all feedback for a target, including average rating and count."""
        try:
            target_uuid = uuid.UUID(target_id)
        except ValueError as exc:
            raise ValueError("Invalid target_id UUID") from exc

        feedback_list = await self._repo.list_for_target(target_uuid, target_type, limit, offset)
        total = await self._repo.count_for_target(target_uuid, target_type)
        avg = await self._repo.average_rating_for_target(target_uuid, target_type)

        return {
            "feedback": [self._to_dict(fb) for fb in feedback_list],
            "total": total,
            "average_rating": round(avg, 2),
            "count": total,
        }

    async def get_feedback_summary(self) -> dict[str, Any]:
        """Aggregated dashboard stats (ADMIN only at router level)."""
        summary = await self._repo.get_summary()
        logger.info("feedback_summary_fetched", total=summary["total_feedback_count"])
        return summary

    async def get_category_trends(self) -> dict[str, Any]:
        """Average rating per category over time."""
        trends = await self._repo.get_category_trends()
        return {"trends": trends}

    async def update_feedback(
        self,
        feedback_id: str,
        rating: int | None = None,
        comment: str | None = None,
        specific_section: str | None = None,
    ) -> dict[str, Any] | None:
        """Update feedback fields."""
        try:
            fb_uuid = uuid.UUID(feedback_id)
        except ValueError as exc:
            raise ValueError("Invalid feedback_id UUID") from exc

        kwargs: dict[str, Any] = {}
        if rating is not None:
            kwargs["rating"] = rating
        if comment is not None:
            kwargs["comment"] = comment
        if specific_section is not None:
            kwargs["specific_section"] = specific_section

        fb = await self._repo.update(fb_uuid, **kwargs)
        if not fb:
            return None

        logger.info("feedback_updated", feedback_id=feedback_id)
        return self._to_dict(fb)

    async def delete_feedback(self, feedback_id: str) -> bool:
        """Delete a feedback entry."""
        try:
            fb_uuid = uuid.UUID(feedback_id)
        except ValueError as exc:
            raise ValueError("Invalid feedback_id UUID") from exc

        result = await self._repo.delete(fb_uuid)
        logger.info("feedback_deleted", feedback_id=feedback_id, success=result)
        return result

    @staticmethod
    def _to_dict(fb) -> dict[str, Any]:
        """Convert Feedback ORM instance to plain dict."""
        return {
            "id": str(fb.id),
            "target_type": fb.target_type,
            "target_id": str(fb.target_id),
            "reviewer_id": str(fb.reviewer_id) if fb.reviewer_id else None,
            "reviewer_type": fb.reviewer_type,
            "category": fb.category,
            "rating": fb.rating,
            "comment": fb.comment,
            "specific_section": fb.specific_section,
            "created_at": fb.created_at.isoformat() if fb.created_at else "",
            "updated_at": fb.updated_at.isoformat() if fb.updated_at else "",
        }


# Singleton instance storage
_feedback_service_cache: dict[int, FeedbackService] = {}


def get_feedback_service(db: AsyncSession) -> FeedbackService:
    """Return a FeedbackService bound to the given DB session."""
    # Use id(db) as cache key since AsyncSession is not hashable
    key = id(db)
    svc = _feedback_service_cache.get(key)
    if svc is None:
        svc = FeedbackService(db)
        _feedback_service_cache[key] = svc
    return svc
