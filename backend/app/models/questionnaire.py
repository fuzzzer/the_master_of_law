"""
Questionnaire models — questions and answers for pre-analysis intake.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.database import Base


class QuestionnaireQuestion(Base):
    """An AI-generated question for a conversation's questionnaire."""

    __tablename__ = "questionnaire_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(String(64), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # text, boolean, choice, date, number
    options = Column(JSONB, nullable=True)  # for choice type
    required = Column(Boolean, nullable=False, default=True)
    purpose = Column(Text, nullable=True)
    legal_relevance = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuestionnaireAnswer(Base):
    """A user's answer to a questionnaire question."""

    __tablename__ = "questionnaire_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(String(64), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_value = Column(Text, nullable=True)
    answer_type = Column(String(20), nullable=False)  # text, boolean, choice, date, number
    skipped = Column(Boolean, nullable=False, default=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
