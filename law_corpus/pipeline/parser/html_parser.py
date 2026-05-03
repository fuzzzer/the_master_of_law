"""
HTML parser for Georgian legal documents from matsne.gov.ge.

Converts raw HTML into structured ``LegalDocument`` objects with
articles, paragraphs, and metadata properly extracted.
"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from pipeline.models.document_metadata import DocumentMetadata
from pipeline.models.legal_article import ArticleParagraph, LegalArticle
from pipeline.models.legal_document import LegalDocument
from pipeline.models.scrape_result import ContentFormat, ScrapeResult
from pipeline.parser.base_parser import BaseParser
from pipeline.parser.metadata_extractor import MetadataExtractor
from pipeline.parser.structure_extractor import StructureExtractor
from pipeline.utils.georgian_text import normalise_georgian
from pipeline.utils.legal_reference_parser import parse_references
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class HtmlLegalParser(BaseParser):
    """Parse HTML legal documents from matsne.gov.ge."""

    def __init__(self) -> None:
        self._structure_extractor = StructureExtractor()
        self._metadata_extractor = MetadataExtractor()

    def can_parse(self, result: ScrapeResult) -> bool:
        return result.content_format == ContentFormat.HTML

    def parse(
        self,
        result: ScrapeResult,
        seed_meta: dict | None = None,
    ) -> LegalDocument:
        """
        Parse a scraped HTML page into a LegalDocument.

        Parameters
        ----------
        result : ScrapeResult
            Raw scrape result containing HTML bytes.
        seed_meta : dict, optional
            Pre-populated metadata from the seed list.
        """
        html_text = result.content.decode(result.encoding, errors="replace")
        soup = BeautifulSoup(html_text, "lxml")

        # Extract main content area
        body_text = self._extract_body_text(soup)

        # Extract metadata
        metadata = self._metadata_extractor.extract(
            html_text, result.document_id, seed_meta,
        )

        # Extract structure
        nodes = self._structure_extractor.extract(body_text)
        flat_articles = self._structure_extractor.flatten_articles(nodes)

        # Build article models
        articles: list[LegalArticle] = []
        for art_data in flat_articles:
            content_ka = normalise_georgian(art_data.get("content", ""))
            article_number = f"მუხლი {art_data['number']}"

            # Parse cross-references
            refs = parse_references(content_ka)
            cross_ref_ids = [
                f"{result.document_id}.article_{r.article_number}"
                for r in refs
            ]

            # Build hierarchical article ID
            parts = [result.document_id]
            if art_data.get("book"):
                parts.append(f"book_{art_data['book'].split('.')[0].strip()}")
            if art_data.get("chapter"):
                parts.append(f"chapter_{art_data['chapter'].split('.')[0].strip()}")
            parts.append(f"article_{art_data['number']}")
            article_id = ".".join(parts)

            # Parse paragraphs from content
            paragraphs = self._parse_paragraphs(content_ka)

            articles.append(LegalArticle(
                article_id=article_id,
                document_id=result.document_id,
                code_name=metadata.title_ka,
                book=art_data.get("book"),
                part=art_data.get("part"),
                chapter=art_data.get("chapter"),
                article_number=article_number,
                article_title=art_data.get("title") or None,
                content_ka=content_ka,
                paragraphs=paragraphs,
                cross_references=cross_ref_ids,
                effective_date=metadata.effective_date,
                is_repealed="გაუქმებული" in content_ka,
            ))

        logger.info(
            "Parsed %s: %d articles extracted",
            result.document_id, len(articles),
        )

        return LegalDocument(
            metadata=metadata,
            articles=articles,
            raw_html=html_text,
        )

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _extract_body_text(soup: BeautifulSoup) -> str:
        """
        Extract the main legal text from the page, stripping navigation,
        headers, footers, and other non-content elements.
        """
        # matsne.gov.ge typically wraps law content in specific containers
        content_div = (
            soup.find("div", {"id": "documentText"})
            or soup.find("div", class_="law-body")
            or soup.find("div", class_="document-content")
            or soup.find("article")
            or soup.find("main")
        )
        if content_div:
            return content_div.get_text(separator="\n", strip=True)

        # Fallback: use the whole body
        body = soup.find("body")
        if body:
            # Remove script/style/nav elements
            for tag in body.find_all(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return body.get_text(separator="\n", strip=True)

        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _parse_paragraphs(content: str) -> list[ArticleParagraph]:
        """
        Split article content into numbered paragraphs.

        Looks for patterns like:
          1. text...
          2. text...
          ა) text...
          ბ) text...
        """
        import re

        paragraphs: list[ArticleParagraph] = []
        lines = content.split("\n")
        current_num: str | None = None
        current_lines: list[str] = []

        num_pattern = re.compile(r"^\s*(\d+)\s*[.)]\s*(.*)", re.UNICODE)
        letter_pattern = re.compile(r"^\s*([ა-ჰ])\s*\)\s*(.*)", re.UNICODE)

        for line in lines:
            stripped = line.strip()
            num_m = num_pattern.match(stripped)
            let_m = letter_pattern.match(stripped)

            if num_m:
                # Flush previous paragraph
                if current_num is not None and current_lines:
                    paragraphs.append(ArticleParagraph(
                        number=current_num,
                        text="\n".join(current_lines).strip(),
                    ))
                current_num = num_m.group(1)
                current_lines = [num_m.group(2)]
            elif let_m:
                if current_num is not None and current_lines:
                    paragraphs.append(ArticleParagraph(
                        number=current_num,
                        text="\n".join(current_lines).strip(),
                    ))
                current_num = let_m.group(1)
                current_lines = [let_m.group(2)]
            else:
                current_lines.append(stripped)

        # Flush last paragraph
        if current_num is not None and current_lines:
            paragraphs.append(ArticleParagraph(
                number=current_num,
                text="\n".join(current_lines).strip(),
            ))

        return paragraphs
