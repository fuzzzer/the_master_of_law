"""
Chat-related Pydantic schemas.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.rag_schema import RAGCollectionConfig


class ChatSendRequest(BaseModel):
    """Request body for POST /chat/{conversation_id}/send."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    rag_config: RAGCollectionConfig | None = Field(
        default=None,
        description="Optional config to toggle which knowledge sources to search. Default: all enabled.",
    )
    mode: str = Field(
        default="chat",
        description="Chat mode: 'chat' for general Q&A, 'case_intake' for case-building, 'case_agent' for AI-driven case modification.",
    )
    case_context: str | None = Field(
        default=None,
        description="Optional case context summary to give AI awareness of an attached case.",
    )
    case_file_id: str | None = Field(
        default=None,
        description="Required for case_agent mode — the case file to operate on.",
    )


class CitationInfo(BaseModel):
    """A verified law citation."""
    article_number: str
    paragraph: str = ""
    code_name: str
    raw_text: str
    verified: bool
    article_url: str = ""
    source_url: str = ""
    citation_text: str = ""


class RetrievedChunk(BaseModel):
    """A retrieved law chunk from the RAG pipeline."""
    chunk_id: str
    content: str = ""
    code_name: str = ""
    article_number: str = ""
    article_title: str = ""
    citation_text: str = ""
    article_url: str = ""
    distance: float = 0.0


class ToolResultInfo(BaseModel):
    """Result of a single tool execution by the case agent."""
    tool_name: str
    status: str = Field(description="executed | pending_confirmation | error | rejected")
    result: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_id: str | None = None
    description: str | None = None


class ChatSendResponse(BaseModel):
    """Response for POST /chat/{conversation_id}/send."""
    response: str = Field(..., description="AI-generated legal analysis")
    citations: list[CitationInfo] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    credits_remaining: int | None = None
    case_analysis_ready: bool = Field(
        default=False,
        description="True when AI has gathered enough info for full case analysis.",
    )
    suggest_questionnaire: bool = Field(
        default=False,
        description="True when the system suggests generating a structured questionnaire.",
    )
    tool_results: list[ToolResultInfo] = Field(
        default_factory=list,
        description="Results of tool executions in case_agent mode.",
    )


class ToolConfirmRequest(BaseModel):
    """Request body for POST /chat/{conversation_id}/confirm-tool."""
    confirmation_id: str
    confirmed: bool


class ToolConfirmResponse(BaseModel):
    """Response for tool confirmation."""
    status: str
    tool_name: str
    result: dict[str, Any] = Field(default_factory=dict)

