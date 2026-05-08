"""
Feedback model — case review and conversation feedback.

Tracks structured feedback from testers, legal experts, and users
to drive quality improvement.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.models.database import Base


class Feedback(Base):
    """A single feedback entry for a case file or conversation."""

    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_type = Column(String(20), nullable=False)  # case_file | conversation
    target_id = Column(UUID(as_uuid=True), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    reviewer_type = Column(
        String(20), nullable=False, default="user"
    )  # tester | legal_expert | user | anonymous
    category = Column(
        String(30), nullable=False
    )  # accuracy | completeness | relevance | formatting | citation_quality | legal_reasoning | overall
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    specific_section = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_feedback_target", "target_type", "target_id"),
        Index("ix_feedback_category", "category"),
    )
