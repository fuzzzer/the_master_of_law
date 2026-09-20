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
    # A turn is running for this conversation right now: its result will
    # appear as the next message. The client waits and polls rather than
    # treating the missing answer as final.
    turn_in_progress: bool = False


class ConversationListResponse(BaseModel):
    """Response for GET /conversations."""
    conversations: list[ConversationSummary]
    total: int
