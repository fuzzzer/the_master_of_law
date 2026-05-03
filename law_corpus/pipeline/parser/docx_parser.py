"""DOCX parser for Georgian legal documents using python-docx."""

from __future__ import annotations

import io

from pipeline.models.legal_document import LegalDocument
from pipeline.models.scrape_result import ContentFormat, ScrapeResult
from pipeline.parser.base_parser import BaseParser
from pipeline.parser.html_parser import HtmlLegalParser
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class DocxLegalParser(BaseParser):
    """Parse DOCX legal documents."""

    def can_parse(self, result: ScrapeResult) -> bool:
        return result.content_format == ContentFormat.DOCX

    def parse(self, result: ScrapeResult, seed_meta: dict | None = None) -> LegalDocument:
        text = self._extract_text(result.content)
        wrapped = f"<html><body><div id='documentText'>{text}</div></body></html>"
        text_result = ScrapeResult(
            url=result.url, document_id=result.document_id,
            content=wrapped.encode("utf-8"), content_format=ContentFormat.HTML,
            encoding="utf-8", http_status=result.http_status,
            scraped_at=result.scraped_at, content_hash=result.content_hash, cached=result.cached,
        )
        return HtmlLegalParser().parse(text_result, seed_meta)

    @staticmethod
    def _extract_text(docx_bytes: bytes) -> str:
        from docx import Document
        doc = Document(io.BytesIO(docx_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
