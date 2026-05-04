"""
Law browser Pydantic schemas.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LawCodeSummary(BaseModel):
    """Summary info for a legal code."""
    code_id: str
    name: str
    article_count: int = 0
    source_url: str = ""


class LawCodesResponse(BaseModel):
    """Response for GET /laws/codes."""
    codes: list[LawCodeSummary]
    total: int


class LawChunkResponse(BaseModel):
    """A single law chunk."""
    chunk_id: str
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class LawSearchResponse(BaseModel):
    """Response for GET /laws/search."""
    results: list[LawChunkResponse]
    query: str
    total: int
