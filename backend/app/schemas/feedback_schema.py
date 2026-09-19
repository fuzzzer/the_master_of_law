"""
Feedback schemas — request/response models for the feedback system.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FeedbackCategory(str, Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    FORMATTING = "formatting"
    CITATION_QUALITY = "citation_quality"
    LEGAL_REASONING = "legal_reasoning"
    OVERALL = "overall"


class FeedbackTargetType(str, Enum):
    CASE_FILE = "case_file"
    CONVERSATION = "conversation"


class FeedbackSubmitRequest(BaseModel):
    """Request for POST /feedback."""
    target_type: FeedbackTargetType
    target_id: str
    category: FeedbackCategory
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    specific_section: str | None = Field(default=None, max_length=100)


class FeedbackUpdateRequest(BaseModel):
    """Request for PATCH /feedback/{id}."""
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackItem(BaseModel):
    """Single feedback entry."""
    id: str
    target_type: str
    target_id: str
    reviewer_id: str | None = None
    reviewer_type: str = "user"
    category: str
    rating: int
    comment: str | None = None
    specific_section: str | None = None
    created_at: str = ""
    updated_at: str = ""


class FeedbackListResponse(BaseModel):
    """Response for GET /feedback/{target_id}."""
    feedback: list[FeedbackItem]
    average_rating: float
    count: int


class CategoryStats(BaseModel):
    """Aggregated stats for a single feedback category."""
    avg: float
    count: int


class WorstCase(BaseModel):
    """A low-scoring target for the admin summary."""
    target_id: str
    target_type: str
    avg_rating: float
    feedback_count: int


class FeedbackSummaryResponse(BaseModel):
    """Response for GET /feedback/summary (ADMIN only)."""
    total_feedback: int
    categories: dict[str, CategoryStats]
    worst_cases: list[WorstCase]
