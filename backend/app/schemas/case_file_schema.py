"""
Case file schemas — request/response models for the case builder.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.rag_schema import RAGCollectionConfig


class CaseFileBuildRequest(BaseModel):
    """Request for POST /case-files/build."""
    conversation_id: str = Field(..., description="Conversation to build the case file from")
    rag_config: RAGCollectionConfig | None = Field(
        default=None,
        description="Optional config to toggle which knowledge sources to use. Default: all enabled.",
    )


class CaseFileUpdateRequest(BaseModel):
    """Request for PATCH /case-files/{id}."""
    user_notes: str | None = None
    status: str | None = None  # draft, active, resolved


class CaseFileSummary(BaseModel):
    """Summary for list views."""
    id: str
    title: str
    status: str = "draft"
    conversation_id: str | None = None
    created_at: str = ""
    updated_at: str = ""


class CaseFileDetail(BaseModel):
    """Full case file with all sections."""
    id: str
    title: str
    conversation_id: str | None = None
    facts: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    applicable_laws: dict[str, Any] | None = None
    defense_strategies: dict[str, Any] | None = None
    prosecution_args: dict[str, Any] | None = None
    action_checklist: dict[str, Any] | None = None
    lawyer_brief: dict[str, Any] | None = None
    citations: dict[str, Any] | None = None
    rendered_text: str = ""
    status: str = "draft"
    user_notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class CaseFileListResponse(BaseModel):
    """Response for GET /case-files."""
    case_files: list[CaseFileSummary]
    total: int
