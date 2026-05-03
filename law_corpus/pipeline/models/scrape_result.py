"""
Model for raw scraper output — before any parsing.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ContentFormat(str, enum.Enum):
    """Format of the scraped content."""
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    TEXT = "text"
    JSON = "json"


class ScrapeResult(BaseModel):
    """One scraped page / document download."""

    url: str = Field(..., description="Source URL")
    document_id: str = Field(
        ..., description="Inferred document slug"
    )
    content: bytes = Field(
        ..., description="Raw content bytes"
    )
    content_format: ContentFormat = Field(
        ..., description="Detected format"
    )
    encoding: str = Field(
        default="utf-8", description="Character encoding"
    )
    http_status: int = Field(
        default=200, description="HTTP response status code"
    )
    headers: dict[str, str] = Field(
        default_factory=dict, description="Response headers"
    )
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(),
    )
    content_hash: str = Field(
        default="", description="SHA-256 of content for dedup"
    )
    cached: bool = Field(
        default=False, description="True if served from local cache"
    )

    # Optional metadata discovered during scraping
    discovered_title: Optional[str] = Field(default=None)
    discovered_links: list[str] = Field(
        default_factory=list,
        description="Outgoing links discovered on this page",
    )

    model_config = {"arbitrary_types_allowed": True}
