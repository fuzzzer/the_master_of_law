"""
Feedback schemas — request/response models for the feedback system.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class FeedbackCategory:
    """Allowed feedback categories."""

    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    FORMATTING = "formatting"
    CITATION_QUALITY = "citation_quality"
    LEGAL_REASONING = "legal_reasoning"
    OVERALL = "overall"


class ReviewerType:
    """Allowed reviewer types."""

    TESTER = "tester"
    LEGAL_EXPERT = "legal_expert"
    USER = "user"
    ANONYMOUS = "anonymous"


class TargetType:
    """Allowed target types."""

    CASE_FILE = "case_file"
    CONVERSATION = "conversation"


class FeedbackCreateRequest(BaseModel):
    """Request for POST /feedback."""

    target_type: str = Field(..., description="Type of target: case_file or conversation")
    target_id: str = Field(..., description="UUID of the target entity")
    reviewer_type: str = Field(default="user", description="Type of reviewer")
    category: str = Field(..., description="Feedback category")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(default=None, max_length=2000, description="Optional comment")
    specific_section: str | None = Field(
        default=None, max_length=100, description="Optional specific section"
    )

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, v: str) -> str:
        if v not in {TargetType.CASE_FILE, TargetType.CONVERSATION}:
            raise ValueError("target_type must be 'case_file' or 'conversation'")
        return v

    @field_validator("reviewer_type")
    @classmethod
    def validate_reviewer_type(cls, v: str) -> str:
        allowed = {ReviewerType.TESTER, ReviewerType.LEGAL_EXPERT, ReviewerType.USER, ReviewerType.ANONYMOUS}
        if v not in allowed:
            raise ValueError(f"reviewer_type must be one of {allowed}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {
            FeedbackCategory.ACCURACY,
            FeedbackCategory.COMPLETENESS,
            FeedbackCategory.RELEVANCE,
            FeedbackCategory.FORMATTING,
            FeedbackCategory.CITATION_QUALITY,
            FeedbackCategory.LEGAL_REASONING,
            FeedbackCategory.OVERALL,
        }
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) < 10:
            raise ValueError("comment must be at least 10 characters if provided")
        return v


class FeedbackUpdateRequest(BaseModel):
    """Request for PATCH /feedback/{id}."""

    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    specific_section: str | None = Field(default=None, max_length=100)

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) < 10:
            raise ValueError("comment must be at least 10 characters if provided")
        return v


class FeedbackItem(BaseModel):
    """Single feedback response."""

    id: str
    target_type: str
    target_id: str
    reviewer_id: str | None
    reviewer_type: str
    category: str
    rating: int
    comment: str | None
    specific_section: str | None
    created_at: str
    updated_at: str


class FeedbackListResponse(BaseModel):
    """Response for GET /feedback/{target_id}."""

    feedback: list[FeedbackItem]
    total: int
    average_rating: float
    count: int


class FeedbackSummaryItem(BaseModel):
    """Aggregated feedback per category."""

    category: str
    total_count: int
    average_rating: float


class FeedbackSummaryResponse(BaseModel):
    """Response for GET /feedback/summary."""

    overall_average: float
    total_feedback_count: int
    by_category: list[FeedbackSummaryItem]
    by_reviewer_type: dict[str, int]


class CategoryTrendPoint(BaseModel):
    """Single point in a category trend."""

    period: str  # e.g. "2024-01"
    average_rating: float
    count: int


class CategoryTrendsResponse(BaseModel):
    """Response for GET /feedback/trends."""

    trends: dict[str, list[CategoryTrendPoint]]
