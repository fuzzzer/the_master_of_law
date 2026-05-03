"""
Model for a single legal article (მუხლი).

An article is the *primary structural unit* of Georgian legislation.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class LegalArticle(BaseModel):
    """A single article extracted from a legal document."""

    article_id: str = Field(
        ...,
        description=(
            "Hierarchical ID, e.g. 'civil_code.book_1.chapter_3.article_45'"
        ),
    )
    document_id: str = Field(
        ..., description="Parent document slug"
    )

    # ── Position in hierarchy ────────────────────────────────
    code_name: str = Field(
        ..., description="Name of the parent code / law in Georgian"
    )
    book: Optional[str] = Field(default=None, description="წიგნი (Book)")
    part: Optional[str] = Field(default=None, description="კარი (Part/Title)")
    chapter: Optional[str] = Field(default=None, description="თავი (Chapter)")

    # ── Article content ──────────────────────────────────────
    article_number: str = Field(
        ...,
        description="Human-visible number, e.g. 'მუხლი 45' or 'მუხლი 100-1'",
    )
    article_title: Optional[str] = Field(
        default=None, description="Article heading / title (if any)"
    )
    content_ka: str = Field(
        ..., description="Full article text in Georgian"
    )
    content_en: Optional[str] = Field(
        default=None, description="English translation (if available)"
    )

    # ── Paragraphs ───────────────────────────────────────────
    paragraphs: list[ArticleParagraph] = Field(
        default_factory=list,
        description="Parsed sub-structure of the article",
    )

    # ── Cross-references ─────────────────────────────────────
    cross_references: list[str] = Field(
        default_factory=list,
        description="Article IDs referenced within this article",
    )

    # ── Versioning ───────────────────────────────────────────
    effective_date: Optional[date] = Field(default=None)
    is_repealed: bool = Field(
        default=False,
        description="True if this article has been repealed (გაუქმებული)",
    )


class ArticleParagraph(BaseModel):
    """A paragraph (პუნქტი) or sub-point (ქვეპუნქტი) within an article."""

    number: str = Field(
        ..., description="Paragraph label, e.g. '1' or 'ა'"
    )
    text: str = Field(
        ..., description="Paragraph text in Georgian"
    )
    sub_points: list[ArticleParagraph] = Field(
        default_factory=list,
        description="Nested sub-points (ქვეპუნქტი)",
    )


# Rebuild the forward-reference now that ArticleParagraph is defined.
LegalArticle.model_rebuild()
