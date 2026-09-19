"""
Conversation model.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.database import Base


class Conversation(Base):
    """A conversation session between a user and the AI."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(128), nullable=False, index=True)  # Firebase UID
    title = Column(String(500), nullable=True)
    phase = Column(String(20), nullable=False, default="GREETING")
    legal_domain = Column(String(100), nullable=True)
    case_ready = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship: cascade delete messages when conversation is deleted
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
