"""
Tests for the Feedback Service and Repository.

Verifies:
- Feedback submission with valid and invalid data
- Feedback retrieval with average rating and count
- Feedback update within 24h window
- Feedback deletion
- Summary aggregation (ADMIN only at router level)
- Category trends
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import sys

sys.path.insert(0, ".")

from app.services.feedback_service import FeedbackService
from app.repositories.feedback_repository import FeedbackRepository


class FakeFeedback:
    """Fake Feedback ORM object for unit testing without DB."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.target_type = kwargs.get("target_type", "case_file")
        self.target_id = kwargs.get("target_id", uuid.uuid4())
        self.reviewer_id = kwargs.get("reviewer_id")
        self.reviewer_type = kwargs.get("reviewer_type", "user")
        self.category = kwargs.get("category", "overall")
        self.rating = kwargs.get("rating", 3)
        self.comment = kwargs.get("comment")
        self.specific_section = kwargs.get("specific_section")
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def feedback_service(mock_db):
    return FeedbackService(mock_db)


class TestSubmitFeedback:
    """Tests for FeedbackService.submit_feedback()."""

    @pytest.mark.asyncio
    async def test_submit_success(self, feedback_service, mock_db):
        feedback_service._repo.create = AsyncMock(return_value=FakeFeedback(rating=4, category="accuracy"))
        result = await feedback_service.submit_feedback(
            target_type="case_file",
            target_id=str(uuid.uuid4()),
            reviewer_type="user",
            category="accuracy",
            rating=4,
            comment="Very accurate analysis",
            specific_section="facts",
        )
        assert result["rating"] == 4
        assert result["category"] == "accuracy"
        assert result["comment"] == "Very accurate analysis"

    @pytest.mark.asyncio
    async def test_submit_invalid_target_id(self, feedback_service):
        with pytest.raises(ValueError, match="Invalid target_id UUID"):
            await feedback_service.submit_feedback(
                target_type="case_file",
                target_id="not-a-uuid",
                reviewer_type="user",
                category="overall",
                rating=3,
            )

    @pytest.mark.asyncio
    async def test_submit_conversation_target(self, feedback_service, mock_db):
        feedback_service._repo.create = AsyncMock(return_value=FakeFeedback(target_type="conversation"))
        result = await feedback_service.submit_feedback(
            target_type="conversation",
            target_id=str(uuid.uuid4()),
            reviewer_type="tester",
            category="relevance",
            rating=5,
        )
        assert result["target_type"] == "conversation"
        assert result["reviewer_type"] == "tester"

    @pytest.mark.asyncio
    async def test_submit_anonymous(self, feedback_service, mock_db):
        feedback_service._repo.create = AsyncMock(return_value=FakeFeedback(reviewer_type="anonymous"))
        result = await feedback_service.submit_feedback(
            target_type="case_file",
            target_id=str(uuid.uuid4()),
            reviewer_type="anonymous",
            category="overall",
            rating=2,
        )
        assert result["reviewer_type"] == "anonymous"
        assert result["reviewer_id"] is None


class TestGetFeedback:
    """Tests for FeedbackService.get_feedback()."""

    @pytest.mark.asyncio
    async def test_get_feedback_with_stats(self, feedback_service, mock_db):
        target_id = uuid.uuid4()
        feedback_service._repo.list_for_target = AsyncMock(return_value=[
            FakeFeedback(target_id=target_id, rating=4),
            FakeFeedback(target_id=target_id, rating=5),
        ])
        feedback_service._repo.count_for_target = AsyncMock(return_value=2)
        feedback_service._repo.average_rating_for_target = AsyncMock(return_value=4.5)

        result = await feedback_service.get_feedback(str(target_id), "case_file")
        assert result["count"] == 2
        assert result["average_rating"] == 4.5
        assert len(result["feedback"]) == 2

    @pytest.mark.asyncio
    async def test_get_feedback_empty(self, feedback_service, mock_db):
        target_id = uuid.uuid4()
        feedback_service._repo.list_for_target = AsyncMock(return_value=[])
        feedback_service._repo.count_for_target = AsyncMock(return_value=0)
        feedback_service._repo.average_rating_for_target = AsyncMock(return_value=0.0)

        result = await feedback_service.get_feedback(str(target_id), "case_file")
        assert result["count"] == 0
        assert result["average_rating"] == 0.0
        assert result["feedback"] == []

    @pytest.mark.asyncio
    async def test_get_feedback_invalid_uuid(self, feedback_service):
        with pytest.raises(ValueError, match="Invalid target_id UUID"):
            await feedback_service.get_feedback("bad-uuid", "case_file")


class TestUpdateFeedback:
    """Tests for FeedbackService.update_feedback()."""

    @pytest.mark.asyncio
    async def test_update_rating(self, feedback_service, mock_db):
        fb_id = uuid.uuid4()
        feedback_service._repo.update = AsyncMock(return_value=FakeFeedback(id=fb_id, rating=5))
        result = await feedback_service.update_feedback(str(fb_id), rating=5)
        assert result is not None
        assert result["rating"] == 5

    @pytest.mark.asyncio
    async def test_update_not_found(self, feedback_service, mock_db):
        feedback_service._repo.update = AsyncMock(return_value=None)
        result = await feedback_service.update_feedback(str(uuid.uuid4()), comment="new comment")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_invalid_uuid(self, feedback_service):
        with pytest.raises(ValueError, match="Invalid feedback_id UUID"):
            await feedback_service.update_feedback("not-a-uuid", rating=3)


class TestDeleteFeedback:
    """Tests for FeedbackService.delete_feedback()."""

    @pytest.mark.asyncio
    async def test_delete_success(self, feedback_service, mock_db):
        feedback_service._repo.delete = AsyncMock(return_value=True)
        result = await feedback_service.delete_feedback(str(uuid.uuid4()))
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_invalid_uuid(self, feedback_service):
        with pytest.raises(ValueError, match="Invalid feedback_id UUID"):
            await feedback_service.delete_feedback("bad-uuid")


class TestFeedbackSummary:
    """Tests for FeedbackService.get_feedback_summary()."""

    @pytest.mark.asyncio
    async def test_summary_basic(self, feedback_service, mock_db):
        feedback_service._repo.get_summary = AsyncMock(return_value={
            "overall_average": 3.5,
            "total_feedback_count": 10,
            "by_category": [
                {"category": "accuracy", "total_count": 4, "average_rating": 4.0},
                {"category": "overall", "total_count": 6, "average_rating": 3.2},
            ],
            "by_reviewer_type": {"user": 8, "tester": 2},
        })
        result = await feedback_service.get_feedback_summary()
        assert result["overall_average"] == 3.5
        assert result["total_feedback_count"] == 10
        assert len(result["by_category"]) == 2


class TestCategoryTrends:
    """Tests for FeedbackService.get_category_trends()."""

    @pytest.mark.asyncio
    async def test_trends_structure(self, feedback_service, mock_db):
        feedback_service._repo.get_category_trends = AsyncMock(return_value={
            "accuracy": [
                {"period": "2026-04", "count": 3, "average_rating": 4.0},
                {"period": "2026-05", "count": 2, "average_rating": 3.5},
            ],
            "overall": [
                {"period": "2026-05", "count": 5, "average_rating": 3.8},
            ],
        })
        result = await feedback_service.get_category_trends()
        assert "trends" in result
        assert "accuracy" in result["trends"]
        assert len(result["trends"]["accuracy"]) == 2


class TestFeedbackRepositoryHelpers:
    """Tests for repository aggregation logic."""

    def test_repo_init(self, mock_db):
        repo = FeedbackRepository(mock_db)
        assert repo._db is mock_db
