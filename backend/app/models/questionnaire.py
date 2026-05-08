"""
Questionnaire model — stores AI-generated questions and user answers
for a dynamic intake flow per conversation.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.database import Base


class QuestionnaireItem(Base):
    """
    A single questionnaire question (with optional answer) for a conversation.

    Questions are AI-generated per domain and stored here so the state
    survives server restarts.  Answers are filled in as the user responds.
    """

    __tablename__ = "questionnaire_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(String(100), nullable=False)
    question_text_ka = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # text, boolean, choice, date, number
    options = Column(JSONB, nullable=True)  # list of strings for choice questions
    required = Column(Boolean, default=True, nullable=False)
    purpose = Column(Text, nullable=True)
    legal_relevance = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)

    # Answer fields
    answer_value = Column(Text, nullable=True)
    skipped = Column(Boolean, default=False, nullable=False)
    answered_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        """Serialize to a plain dict for API responses."""
        return {
            "id": str(self.id),
            "question_id": self.question_id,
            "question_text_ka": self.question_text_ka,
            "question_type": self.question_type,
            "options": self.options or [],
            "required": self.required,
            "purpose": self.purpose or "",
            "legal_relevance": self.legal_relevance or "",
            "sort_order": self.sort_order,
            "answer_value": self.answer_value,
            "skipped": self.skipped,
            "answered_at": self.answered_at.isoformat() if self.answered_at else "",
        }
