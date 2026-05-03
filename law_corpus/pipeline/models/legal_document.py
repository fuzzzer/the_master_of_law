"""
Model for a complete legal document (a whole code / law).

A ``LegalDocument`` aggregates its metadata and all of its articles.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from pipeline.models.document_metadata import DocumentMetadata
from pipeline.models.legal_article import LegalArticle


class LegalDocument(BaseModel):
    """
    A full legal document — one code, one law, one decree, etc.

    This is the output of the *parser* stage and the input to the *chunker*.
    """

    metadata: DocumentMetadata
    articles: list[LegalArticle] = Field(default_factory=list)

    # Optional raw content (kept for debugging; not serialised by default)
    raw_html: Optional[str] = Field(default=None, exclude=True)
    raw_text: Optional[str] = Field(default=None, exclude=True)

    @property
    def document_id(self) -> str:
        return self.metadata.document_id

    @property
    def article_count(self) -> int:
        return len(self.articles)
