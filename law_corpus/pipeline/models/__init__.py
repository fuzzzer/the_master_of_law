"""Pydantic data models for the pipeline."""

from pipeline.models.document_metadata import DocumentMetadata, LegalDocumentType
from pipeline.models.legal_article import LegalArticle
from pipeline.models.legal_chunk import LegalChunk
from pipeline.models.legal_document import LegalDocument
from pipeline.models.scrape_result import ScrapeResult

__all__ = [
    "DocumentMetadata",
    "LegalArticle",
    "LegalChunk",
    "LegalDocument",
    "LegalDocumentType",
    "ScrapeResult",
]
