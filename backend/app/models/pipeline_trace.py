"""
Pipeline trace model — full step-by-step transparency record of one AI interaction.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.database import Base


class PipelineTrace(Base):
    """Everything that happened while answering one user request.

    ``steps`` is an ordered JSONB list of {seq, step, at_ms, data} entries
    covering the whole flow: request → guardrail → plan → RAG stages →
    LLM prompt/response → tool calls → citation verification → final answer.
    """

    __tablename__ = "pipeline_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String(128), nullable=True, index=True)
    entry_point = Column(String(30), nullable=False)  # "rest_chat" | "ws_chat" | "case_agent"
    status = Column(String(20), nullable=False, default="running")  # completed | blocked | failed
    user_message = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    steps = Column(JSONB, nullable=False, default=list)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
