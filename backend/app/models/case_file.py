"""
Case file model — structured defense case documents.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.database import Base


class CaseFile(Base):
    """A structured defense case file generated from a conversation."""

    __tablename__ = "case_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(128), nullable=False, index=True)  # Firebase UID
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)

    # Structured sections (JSONB for flexibility)
    facts = Column(JSONB, nullable=True)               # Section 1: situation facts
    evidence = Column(JSONB, nullable=True)             # Section 2: evidence inventory
    applicable_laws = Column(JSONB, nullable=True)      # Section 3: laws for/against/neutral
    defense_strategies = Column(JSONB, nullable=True)   # Section 4: ranked strategies
    prosecution_args = Column(JSONB, nullable=True)     # Section 5: counter-arguments
    action_checklist = Column(JSONB, nullable=True)     # Section 6: todo items with deadlines
    lawyer_brief = Column(JSONB, nullable=True)         # Section 7: lawyer summary
    citations = Column(JSONB, nullable=True)            # Section 8: full law citations

    # Full rendered text (for display and export)
    rendered_text = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="draft")  # draft, active, resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # User annotations
    user_notes = Column(Text, nullable=True)
