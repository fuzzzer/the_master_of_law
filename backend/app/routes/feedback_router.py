"""
Feedback router — submit, view, update, and delete feedback.

All endpoints cost 0 credits.
Auth: optional for submission (allows anonymous feedback),
      required for edit/delete within 24h ownership window.
      ADMIN tier required for summary/trends.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.feedback import (
    FeedbackCreateRequest,
    FeedbackListResponse,
    FeedbackSummaryResponse,
    FeedbackUpdateRequest,
    CategoryTrendsResponse,
    FeedbackItem,
    FeedbackSummaryItem,
    CategoryTrendPoint,
)
from app.services.feedback_service import get_feedback_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

# Window for editing own feedback
_EDIT_WINDOW_HOURS = 24


def _get_user_info(request: Request) -> dict | None:
    """Extract user info from request state (set by auth middleware)."""
    return getattr(request.state, "user", None)


def _is_admin(user_info: dict | None) -> bool:
    return user_info is not None and user_info.get("tier") == "ADMIN"


def _can_edit(fb_dict: dict, user_info: dict | None) -> bool:
    """Check if the requesting user can edit this feedback."""
    if user_info is None:
        return False
    # Admin can edit anything
    if _is_admin(user_info):
        return True
    # Otherwise must be the original reviewer (match by UID)
    # reviewer_id is UUID; we compare string forms
    reviewer_id = fb_dict.get("reviewer_id")
    if reviewer_id is None:
        return False
    return str(reviewer_id) == user_info.get("uid")


def _within_edit_window(fb_dict: dict) -> bool:
    """Check if feedback is still within the editable time window."""
    created_str = fb_dict.get("created_at", "")
    if not created_str:
        return False
    try:
        created = datetime.fromisoformat(created_str)
        return datetime.now(timezone.utc) - created < timedelta(hours=_EDIT_WINDOW_HOURS)
    except Exception:
        return False


@router.post("", response_model=FeedbackItem, status_code=201)
async def submit_feedback(
    body: FeedbackCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback for a case file or conversation (auth optional)."""
    user_info = _get_user_info(request)
    reviewer_id = user_info.get("uid") if user_info else None

    svc = get_feedback_service(db)
    try:
        result = await svc.submit_feedback(
            target_type=body.target_type,
            target_id=body.target_id,
            reviewer_type=body.reviewer_type,
            category=body.category,
            rating=body.rating,
            comment=body.comment,
            specific_section=body.specific_section,
            reviewer_id=reviewer_id,
        )
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    await db.commit()
    logger.info("feedback_submitted_api", feedback_id=result["id"])
    return FeedbackItem(**result)


@router.get("/{target_id}", response_model=FeedbackListResponse)
async def get_feedback(
    target_id: str,
    target_type: str = Query(..., description="case_file or conversation"),
    db: AsyncSession = Depends(get_db),
):
    """Get all feedback for a specific target."""
    svc = get_feedback_service(db)
    try:
        result = await svc.get_feedback(target_id, target_type)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return FeedbackListResponse(
        feedback=[FeedbackItem(**item) for item in result["feedback"]],
        total=result["total"],
        average_rating=result["average_rating"],
        count=result["count"],
    )


@router.get("/summary", response_model=FeedbackSummaryResponse)
async def get_feedback_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Aggregated feedback dashboard — ADMIN only."""
    user_info = _get_user_info(request)
    if not _is_admin(user_info):
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden", "message": "ADMIN tier required"},
        )

    svc = get_feedback_service(db)
    summary = await svc.get_feedback_summary()

    return FeedbackSummaryResponse(
        overall_average=round(summary["overall_average"], 2),
        total_feedback_count=summary["total_feedback_count"],
        by_category=[
            FeedbackSummaryItem(**item) for item in summary["by_category"]
        ],
        by_reviewer_type=summary["by_reviewer_type"],
    )


@router.get("/trends", response_model=CategoryTrendsResponse)
async def get_category_trends(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Category trends over time — ADMIN only."""
    user_info = _get_user_info(request)
    if not _is_admin(user_info):
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden", "message": "ADMIN tier required"},
        )

    svc = get_feedback_service(db)
    trends_data = await svc.get_category_trends()

    trends = {
        cat: [CategoryTrendPoint(**point) for point in points]
        for cat, points in trends_data["trends"].items()
    }
    return CategoryTrendsResponse(trends=trends)


@router.patch("/{feedback_id}", response_model=FeedbackItem)
async def update_feedback(
    feedback_id: str,
    body: FeedbackUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Edit own feedback within 24 hours of creation."""
    user_info = _get_user_info(request)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    svc = get_feedback_service(db)

    # Fetch existing feedback
    import uuid as _uuid
    try:
        fb_uuid = _uuid.UUID(feedback_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid feedback ID"})

    existing = await svc._repo.get_by_id(fb_uuid)
    if not existing:
        return JSONResponse(status_code=404, content={"error": "Feedback not found"})

    fb_dict = svc._to_dict(existing)
    if not _can_edit(fb_dict, user_info):
        return JSONResponse(status_code=403, content={"error": "Cannot edit feedback from another user"})
    if not _within_edit_window(fb_dict):
        return JSONResponse(
            status_code=403,
            content={"error": "Edit window expired", "message": "Feedback can only be edited within 24 hours"},
        )

    try:
        result = await svc.update_feedback(
            feedback_id=feedback_id,
            rating=body.rating,
            comment=body.comment,
            specific_section=body.specific_section,
        )
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    if not result:
        return JSONResponse(status_code=404, content={"error": "Feedback not found"})

    await db.commit()
    return FeedbackItem(**result)


@router.delete("/{feedback_id}", status_code=204)
async def delete_feedback(
    feedback_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete own feedback."""
    user_info = _get_user_info(request)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    svc = get_feedback_service(db)

    import uuid as _uuid
    try:
        fb_uuid = _uuid.UUID(feedback_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid feedback ID"})

    existing = await svc._repo.get_by_id(fb_uuid)
    if not existing:
        return JSONResponse(status_code=404, content={"error": "Feedback not found"})

    fb_dict = svc._to_dict(existing)
    if not _can_edit(fb_dict, user_info):
        return JSONResponse(status_code=403, content={"error": "Cannot delete feedback from another user"})

    success = await svc.delete_feedback(feedback_id)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Feedback not found"})

    await db.commit()
    return None
