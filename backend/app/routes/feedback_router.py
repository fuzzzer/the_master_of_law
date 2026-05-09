"""
Feedback router — submit, view, update, and delete feedback on AI-generated analyses.

All feedback endpoints cost 0 credits.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback_schema import (
    CategoryStats,
    FeedbackItem,
    FeedbackListResponse,
    FeedbackSubmitRequest,
    FeedbackSummaryResponse,
    FeedbackUpdateRequest,
    WorstCase,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


def _feedback_to_item(fb) -> FeedbackItem:
    return FeedbackItem(
        id=str(fb.id),
        target_type=fb.target_type,
        target_id=str(fb.target_id),
        reviewer_id=str(fb.reviewer_id) if fb.reviewer_id else None,
        reviewer_type=fb.reviewer_type,
        category=fb.category,
        rating=fb.rating,
        comment=fb.comment,
        specific_section=fb.specific_section,
        created_at=fb.created_at.isoformat() if fb.created_at else "",
        updated_at=fb.updated_at.isoformat() if fb.updated_at else "",
    )


@router.post("", status_code=201)
async def submit_feedback(
    body: FeedbackSubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback on a case file or conversation (0 credits)."""
    user_info = getattr(request.state, "user", None)

    try:
        target_uuid = _uuid.UUID(body.target_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid target_id"})

    if body.comment and len(body.comment.strip()) < 10:
        return JSONResponse(
            status_code=400,
            content={"error": "Comment must be at least 10 characters if provided"},
        )

    reviewer_id = None
    reviewer_type = "anonymous"
    if user_info:
        uid = user_info.get("uid", "")
        if uid:
            from app.repositories.user_repository import UserRepository
            user_repo = UserRepository(db)
            user = await user_repo.get_by_firebase_uid(uid)
            if user:
                reviewer_id = user.id
                reviewer_type = user_info.get("tier", "user").lower()
                if reviewer_type == "admin":
                    reviewer_type = "tester"

    repo = FeedbackRepository(db)
    fb = await repo.create(
        target_type=body.target_type.value,
        target_id=target_uuid,
        reviewer_id=reviewer_id,
        reviewer_type=reviewer_type,
        category=body.category.value,
        rating=body.rating,
        comment=body.comment,
        specific_section=body.specific_section,
    )
    await db.commit()

    logger.info("feedback_submitted", feedback_id=str(fb.id), category=body.category.value)
    return {"id": str(fb.id), "created_at": fb.created_at.isoformat() if fb.created_at else ""}


@router.get("/summary")
async def get_feedback_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Aggregated feedback dashboard (ADMIN only)."""
    user_info = getattr(request.state, "user", {})
    tier = user_info.get("tier", "")
    if tier != "ADMIN":
        return JSONResponse(status_code=403, content={"error": "Admin access required"})

    repo = FeedbackRepository(db)
    total = await repo.total_count()
    category_rows = await repo.average_per_category()
    worst = await repo.worst_targets(limit=10)

    categories = {
        row["category"]: CategoryStats(avg=row["avg"], count=row["count"])
        for row in category_rows
    }

    return FeedbackSummaryResponse(
        total_feedback=total,
        categories=categories,
        worst_cases=[WorstCase(**w) for w in worst],
    )


@router.get("/{target_id}")
async def get_feedback_for_target(
    target_id: str,
    target_type: str = "case_file",
    db: AsyncSession = Depends(get_db),
):
    """Get all feedback for a specific case file or conversation."""
    try:
        target_uuid = _uuid.UUID(target_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid target_id"})

    if target_type not in ("case_file", "conversation"):
        return JSONResponse(status_code=400, content={"error": "target_type must be 'case_file' or 'conversation'"})

    repo = FeedbackRepository(db)
    items = await repo.list_for_target(target_type, target_uuid)
    avg = await repo.average_rating_for_target(target_type, target_uuid)
    count = await repo.count_for_target(target_type, target_uuid)

    return FeedbackListResponse(
        feedback=[_feedback_to_item(fb) for fb in items],
        average_rating=avg,
        count=count,
    )


@router.patch("/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    body: FeedbackUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update feedback (own feedback only, within 24 hours)."""
    user_info = getattr(request.state, "user", None)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    try:
        fb_uuid = _uuid.UUID(feedback_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid feedback ID"})

    repo = FeedbackRepository(db)
    fb = await repo.get_by_id(fb_uuid)
    if not fb:
        return JSONResponse(status_code=404, content={"error": "Feedback not found"})

    # Ownership check
    if fb.reviewer_id:
        uid = user_info.get("uid", "")
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository(db)
        user = await user_repo.get_by_firebase_uid(uid)
        if not user or user.id != fb.reviewer_id:
            if user_info.get("tier") != "ADMIN":
                return JSONResponse(status_code=403, content={"error": "Can only edit your own feedback"})

    # 24-hour edit window
    if fb.created_at:
        age = datetime.now(timezone.utc) - fb.created_at.replace(tzinfo=timezone.utc)
        if age > timedelta(hours=24) and user_info.get("tier") != "ADMIN":
            return JSONResponse(status_code=403, content={"error": "Edit window expired (24 hours)"})

    kwargs = {}
    if body.rating is not None:
        kwargs["rating"] = body.rating
    if body.comment is not None:
        kwargs["comment"] = body.comment

    fb = await repo.update(fb_uuid, **kwargs)
    await db.commit()

    return {"updated": True}


@router.delete("/{feedback_id}", status_code=204)
async def delete_feedback(
    feedback_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete feedback (own feedback or ADMIN)."""
    user_info = getattr(request.state, "user", None)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    try:
        fb_uuid = _uuid.UUID(feedback_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid feedback ID"})

    repo = FeedbackRepository(db)
    fb = await repo.get_by_id(fb_uuid)
    if not fb:
        return JSONResponse(status_code=404, content={"error": "Feedback not found"})

    # Ownership check
    if fb.reviewer_id and user_info.get("tier") != "ADMIN":
        uid = user_info.get("uid", "")
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository(db)
        user = await user_repo.get_by_firebase_uid(uid)
        if not user or user.id != fb.reviewer_id:
            return JSONResponse(status_code=403, content={"error": "Can only delete your own feedback"})

    await repo.delete(fb_uuid)
    await db.commit()
    return None
