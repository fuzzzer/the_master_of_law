"""
Conversation schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Request for POST /conversations."""
    title: str | None = None


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""
    id: str
    title: str = ""
    phase: str = "GREETING"
    legal_domain: str = ""
    created_at: str = ""
    updated_at: str = ""


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    id: str
    title: str = ""
    phase: str = "GREETING"
    legal_domain: str = ""
    case_ready: bool = False
    messages: list[dict] = Field(default_factory=list)
    created_at: str = ""


class ConversationListResponse(BaseModel):
    """Response for GET /conversations."""
    conversations: list[ConversationSummary]
    total: int
