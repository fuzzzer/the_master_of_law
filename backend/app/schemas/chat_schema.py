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
        description="Chat mode: 'chat' for general Q&A, 'case_intake' for case-building with intake questions.",
    )
    case_context: str | None = Field(
        default=None,
        description="Optional case context summary to give AI awareness of an attached case.",
    )


class CitationInfo(BaseModel):
    """A verified law citation."""
    article_number: str
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
