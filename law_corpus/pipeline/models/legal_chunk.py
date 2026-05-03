"""
Model for an embeddable chunk of legal text.

Each chunk is the atomic unit that gets embedded and indexed.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class LegalChunk(BaseModel):
    """A single embeddable chunk of legal text."""

    chunk_id: str = Field(
        ...,
        description=(
            "Unique chunk identifier, e.g. "
            "'civil_code.book_1.chapter_3.article_45.chunk_0'"
        ),
    )
    document_id: str = Field(
        ..., description="Parent document slug"
    )
    content: str = Field(
        ..., description="Assembled text content ready for embedding"
    )
    content_ka: str = Field(
        ..., description="Georgian text (may differ from content if header injected)"
    )
    content_en: Optional[str] = Field(
        default=None, description="English translation (if available)"
    )

    # ── Structural metadata ──────────────────────────────────
    code_name: str = Field(
        ..., description="e.g. 'სამოქალაქო კოდექსი'"
    )
    book: Optional[str] = Field(default=None)
    part: Optional[str] = Field(default=None)
    chapter: Optional[str] = Field(default=None)
    article_number: str = Field(
        ..., description="e.g. 'მუხლი 45'"
    )
    article_title: Optional[str] = Field(default=None)
    paragraph_number: Optional[str] = Field(default=None)

    # ── Source provenance (for AI citations) ──────────────────
    source_url: str = Field(
        default="",
        description="Canonical URL of the parent document on matsne.gov.ge",
    )
    article_url: str = Field(
        default="",
        description=(
            "Deep-link to this specific article on matsne.gov.ge, "
            "e.g. 'https://matsne.gov.ge/ka/document/view/31702#article_45'"
        ),
    )
    document_number: str = Field(
        default="",
        description="Official registration / document number",
    )
    adoption_date: Optional[date] = Field(
        default=None,
        description="Date the parent law was adopted (for citation)",
    )
    citation_text: str = Field(
        default="",
        description=(
            "Pre-formatted Georgian citation string, e.g. "
            "'სამოქალაქო კოდექსი, მუხლი 45, matsne.gov.ge/ka/document/view/31702'"
        ),
    )

    # ── Chunk position ───────────────────────────────────────
    chunk_index: int = Field(
        ..., description="0-based position within the parent article"
    )
    total_chunks_in_article: int = Field(
        ..., description="Total number of chunks for this article"
    )
    token_count: int = Field(
        default=0, description="Estimated token count"
    )

    # ── Legal metadata ───────────────────────────────────────
    legal_domains: list[str] = Field(default_factory=list)
    keywords_ka: list[str] = Field(default_factory=list)
    keywords_en: list[str] = Field(default_factory=list)
    cross_references: list[str] = Field(
        default_factory=list,
        description="Referenced article IDs",
    )

    # ── Versioning ───────────────────────────────────────────
    effective_date: Optional[date] = Field(default=None)
    last_updated: Optional[datetime] = Field(default=None)
    is_current: bool = Field(default=True)

    # ── Embedding (populated later) ──────────────────────────
    embedding: Optional[list[float]] = Field(
        default=None,
        description="Vector embedding (set by the embedder stage)",
        exclude=True,  # exclude from JSON serialisation by default
    )
    content_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 of content for change detection / cache keying",
    )
