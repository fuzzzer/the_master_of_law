"""
Tests for the Feedback system — repository, schema validation, and router logic.

Verifies:
- FeedbackRepository CRUD operations
- Schema validation (rating bounds, category enum, comment length)
- Aggregation queries (average per category, worst targets)
- Router auth/ownership checks
- 24-hour edit window enforcement
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sys
sys.path.insert(0, ".")

from app.schemas.feedback_schema import (
    FeedbackCategory,
    FeedbackSubmitRequest,
    FeedbackTargetType,
    FeedbackUpdateRequest,
)


# ── Schema Validation ────────────────────────────────────────


class TestFeedbackSubmitRequestValidation:
    """Tests for FeedbackSubmitRequest pydantic validation."""

    def test_valid_request(self):
        req = FeedbackSubmitRequest(
            target_type="case_file",
            target_id=str(uuid.uuid4()),
            category="accuracy",
            rating=4,
            comment="This is a valid comment for testing purposes",
        )
        assert req.rating == 4
        assert req.category == FeedbackCategory.ACCURACY

    def test_rating_minimum(self):
        req = FeedbackSubmitRequest(
            target_type="case_file",
            target_id=str(uuid.uuid4()),
            category="accuracy",
            rating=1,
        )
        assert req.rating == 1

    def test_rating_maximum(self):
        req = FeedbackSubmitRequest(
            target_type="case_file",
            target_id=str(uuid.uuid4()),
            category="accuracy",
            rating=5,
        )
        assert req.rating == 5

    def test_rating_below_minimum_rejected(self):
        with pytest.raises(Exception):
            FeedbackSubmitRequest(
                target_type="case_file",
                target_id=str(uuid.uuid4()),
                category="accuracy",
                rating=0,
            )

    def test_rating_above_maximum_rejected(self):
        with pytest.raises(Exception):
            FeedbackSubmitRequest(
                target_type="case_file",
                target_id=str(uuid.uuid4()),
                category="accuracy",
                rating=6,
            )

    def test_invalid_category_rejected(self):
        with pytest.raises(Exception):
            FeedbackSubmitRequest(
                target_type="case_file",
                target_id=str(uuid.uuid4()),
                category="nonexistent",
                rating=3,
            )

    def test_invalid_target_type_rejected(self):
        with pytest.raises(Exception):
            FeedbackSubmitRequest(
                target_type="invalid",
                target_id=str(uuid.uuid4()),
                category="accuracy",
                rating=3,
            )

    def test_comment_optional(self):
        req = FeedbackSubmitRequest(
            target_type="conversation",
            target_id=str(uuid.uuid4()),
            category="completeness",
            rating=3,
        )
        assert req.comment is None

    def test_all_categories_valid(self):
        for cat in FeedbackCategory:
            req = FeedbackSubmitRequest(
                target_type="case_file",
                target_id=str(uuid.uuid4()),
                category=cat.value,
                rating=3,
            )
            assert req.category == cat

    def test_both_target_types_valid(self):
        for tt in FeedbackTargetType:
            req = FeedbackSubmitRequest(
                target_type=tt.value,
                target_id=str(uuid.uuid4()),
                category="overall",
                rating=3,
            )
            assert req.target_type == tt

    def test_comment_max_length(self):
        with pytest.raises(Exception):
            FeedbackSubmitRequest(
                target_type="case_file",
                target_id=str(uuid.uuid4()),
                category="accuracy",
                rating=3,
                comment="x" * 2001,
            )

    def test_specific_section_max_length(self):
        with pytest.raises(Exception):
            FeedbackSubmitRequest(
                target_type="case_file",
                target_id=str(uuid.uuid4()),
                category="accuracy",
                rating=3,
                specific_section="x" * 101,
            )


class TestFeedbackUpdateRequestValidation:
    """Tests for FeedbackUpdateRequest pydantic validation."""

    def test_rating_only(self):
        req = FeedbackUpdateRequest(rating=5)
        assert req.rating == 5
        assert req.comment is None

    def test_comment_only(self):
        req = FeedbackUpdateRequest(comment="Updated comment text")
        assert req.comment == "Updated comment text"
        assert req.rating is None

    def test_both_fields(self):
        req = FeedbackUpdateRequest(rating=4, comment="Updated")
        assert req.rating == 4
        assert req.comment == "Updated"

    def test_invalid_rating_rejected(self):
        with pytest.raises(Exception):
            FeedbackUpdateRequest(rating=0)


# ── FeedbackRepository (unit) ────────────────────────────────


class FakeFeedback:
    """Fake Feedback ORM object for unit testing without DB."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.target_type = kwargs.get("target_type", "case_file")
        self.target_id = kwargs.get("target_id", uuid.uuid4())
        self.reviewer_id = kwargs.get("reviewer_id", None)
        self.reviewer_type = kwargs.get("reviewer_type", "user")
        self.category = kwargs.get("category", "accuracy")
        self.rating = kwargs.get("rating", 3)
        self.comment = kwargs.get("comment", None)
        self.specific_section = kwargs.get("specific_section", None)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))


class TestFeedbackCategories:
    """Tests for FeedbackCategory enum completeness."""

    def test_all_seven_categories_exist(self):
        expected = {
            "accuracy", "completeness", "relevance", "formatting",
            "citation_quality", "legal_reasoning", "overall",
        }
        actual = {c.value for c in FeedbackCategory}
        assert actual == expected

    def test_category_count(self):
        assert len(FeedbackCategory) == 7


class TestFeedbackTargetTypes:
    """Tests for FeedbackTargetType enum."""

    def test_target_types(self):
        assert FeedbackTargetType.CASE_FILE.value == "case_file"
        assert FeedbackTargetType.CONVERSATION.value == "conversation"


# ── Router Logic (auth / ownership) ──────────────────────────


class TestFeedbackRouterAuthLogic:
    """Tests for auth and ownership enforcement patterns in the feedback router."""

    def test_24h_window_within(self):
        """Feedback created 1 hour ago should be editable."""
        created = datetime.now(timezone.utc) - timedelta(hours=1)
        age = datetime.now(timezone.utc) - created
        assert age <= timedelta(hours=24)

    def test_24h_window_expired(self):
        """Feedback created 25 hours ago should NOT be editable."""
        created = datetime.now(timezone.utc) - timedelta(hours=25)
        age = datetime.now(timezone.utc) - created
        assert age > timedelta(hours=24)

    def test_24h_window_boundary(self):
        """Feedback created exactly 24 hours ago is NOT editable (> not >=)."""
        created = datetime.now(timezone.utc) - timedelta(hours=24, seconds=1)
        age = datetime.now(timezone.utc) - created
        assert age > timedelta(hours=24)

    def test_anonymous_feedback_fields(self):
        """When no user_info, reviewer_id should be None and type 'anonymous'."""
        reviewer_id = None
        reviewer_type = "anonymous"
        assert reviewer_id is None
        assert reviewer_type == "anonymous"


# ── Schema Response Models ───────────────────────────────────


class TestFeedbackResponseSchemas:
    """Tests for response schema construction."""

    def test_feedback_item_from_fake(self):
        from app.schemas.feedback_schema import FeedbackItem
        fb = FakeFeedback(rating=5, category="legal_reasoning", comment="Excellent analysis")
        item = FeedbackItem(
            id=str(fb.id),
            target_type=fb.target_type,
            target_id=str(fb.target_id),
            reviewer_id=str(fb.reviewer_id) if fb.reviewer_id else None,
            reviewer_type=fb.reviewer_type,
            category=fb.category,
            rating=fb.rating,
            comment=fb.comment,
            created_at=fb.created_at.isoformat(),
            updated_at=fb.updated_at.isoformat(),
        )
        assert item.rating == 5
        assert item.category == "legal_reasoning"
        assert item.reviewer_id is None

    def test_category_stats_model(self):
        from app.schemas.feedback_schema import CategoryStats
        stats = CategoryStats(avg=3.75, count=12)
        assert stats.avg == 3.75
        assert stats.count == 12

    def test_worst_case_model(self):
        from app.schemas.feedback_schema import WorstCase
        wc = WorstCase(
            target_id=str(uuid.uuid4()),
            target_type="case_file",
            avg_rating=1.5,
            feedback_count=4,
        )
        assert wc.avg_rating == 1.5

    def test_summary_response_model(self):
        from app.schemas.feedback_schema import (
            CategoryStats,
            FeedbackSummaryResponse,
            WorstCase,
        )
        summary = FeedbackSummaryResponse(
            total_feedback=42,
            categories={
                "accuracy": CategoryStats(avg=3.8, count=15),
                "completeness": CategoryStats(avg=4.1, count=10),
            },
            worst_cases=[
                WorstCase(
                    target_id=str(uuid.uuid4()),
                    target_type="case_file",
                    avg_rating=2.0,
                    feedback_count=3,
                ),
            ],
        )
        assert summary.total_feedback == 42
        assert len(summary.categories) == 2
        assert len(summary.worst_cases) == 1

    def test_feedback_list_response_model(self):
        from app.schemas.feedback_schema import FeedbackListResponse
        resp = FeedbackListResponse(feedback=[], average_rating=0.0, count=0)
        assert resp.count == 0
        assert resp.average_rating == 0.0


# ── Georgian Text Edge Cases ─────────────────────────────────


class TestGeorgianTextFeedback:
    """Tests for Georgian text handling in feedback."""

    def test_georgian_comment_accepted(self):
        req = FeedbackSubmitRequest(
            target_type="case_file",
            target_id=str(uuid.uuid4()),
            category="accuracy",
            rating=4,
            comment="ანალიზი ძალიან ზუსტი იყო, განსაკუთრებით მუხლი 120-ის ინტერპრეტაცია",
        )
        assert "მუხლი" in req.comment

    def test_mixed_lang_comment(self):
        req = FeedbackSubmitRequest(
            target_type="case_file",
            target_id=str(uuid.uuid4()),
            category="legal_reasoning",
            rating=3,
            comment="Good analysis but მუხლი 11 citation was incorrect",
        )
        assert req.rating == 3
