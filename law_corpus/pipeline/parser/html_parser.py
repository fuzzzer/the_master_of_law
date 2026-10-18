"""
HTML parser for Georgian legal documents from matsne.gov.ge.

Converts raw HTML into structured ``LegalDocument`` objects with
articles, paragraphs, and metadata properly extracted.

Works directly with matsne.gov.ge CSS classes:
  - muxlixml   → Article (მუხლი)
  - tavixml    → Chapter (თავი)
  - nawilixml  → Part (კარი)
  - wignixml   → Book (წიგნი)
  - abzacixml  → Paragraph text
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from pipeline.models.document_metadata import DocumentMetadata
from pipeline.models.legal_article import ArticleParagraph, LegalArticle
from pipeline.models.legal_document import LegalDocument
from pipeline.models.scrape_result import ContentFormat, ScrapeResult
from pipeline.parser.base_parser import BaseParser
from pipeline.parser.metadata_extractor import MetadataExtractor
from pipeline.utils.georgian_text import normalise_georgian, normalise_superscripts
from pipeline.utils.legal_reference_parser import parse_references
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Regex to extract article number and title from muxlixml text
ARTICLE_RE = re.compile(
    r"მუხლი\s+(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)

CHAPTER_RE = re.compile(
    r"თავი\s+([IVXLCDM\d]+)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)

BOOK_RE = re.compile(
    r"წიგნი\s+([IVXLCDM\d]+)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)

PART_RE = re.compile(
    r"კარი\s+([IVXLCDM\d]+)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)


class HtmlLegalParser(BaseParser):
    """Parse HTML legal documents from matsne.gov.ge."""

    def __init__(self) -> None:
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

        Uses matsne.gov.ge CSS classes directly:
          - <p class="muxlixml"> for article headers
          - <p class="abzacixml"> for article body paragraphs
          - <p class="tavixml"> for chapter markers
        """
        html_text = result.content.decode(result.encoding, errors="replace")
        soup = BeautifulSoup(html_text, "lxml")

        # Extract metadata
        metadata = self._metadata_extractor.extract(
            html_text, result.document_id, seed_meta,
        )

        # Extract articles using CSS classes
        articles = self._extract_articles_from_classes(soup, result.document_id, metadata)

        logger.info(
            "Parsed %s: %d articles extracted",
            result.document_id, len(articles),
        )

        return LegalDocument(
            metadata=metadata,
            articles=articles,
            raw_html=html_text,
        )

    def _extract_articles_from_classes(
        self,
        soup: BeautifulSoup,
        document_id: str,
        metadata: DocumentMetadata,
    ) -> list[LegalArticle]:
        """
        Walk all <p> elements in order. Use CSS classes to detect
        structural markers (book, chapter, article) and collect
        paragraph text for each article.

        Supports two HTML templates from matsne.gov.ge:
          1. Standard: muxlixml / abzacixml / tavixml CSS classes
          2. Old-style: ``oldStyleDocumentPart`` anchors inside plain
             ``<p>`` tags with body text in ``<p style="text-align:…">``
        """
        articles: list[LegalArticle] = []

        # Current hierarchy
        current_book: str | None = None
        current_part: str | None = None
        current_chapter: str | None = None

        # Current article being built
        current_article_num: str | None = None
        current_article_title: str | None = None
        current_paragraphs: list[str] = []

        # Detect old-style format: many oldStyleDocumentPart anchors
        # but few/no muxlixml <p> elements around articles 4+
        uses_old_style = (
            len(soup.find_all("a", class_="oldStyleDocumentPart")) > 10
            and len(soup.find_all("p", class_="muxlixml")) < 10
        )

        # Walk ALL <p> tags in document order
        for p in soup.find_all("p"):
            classes = p.get("class") or []
            text = normalise_georgian(p.get_text(strip=True))
            if not text:
                continue

            # ── Check for oldStyleDocumentPart anchors inside this <p> ──
            old_style_anchor = p.find("a", class_="oldStyleDocumentPart") if uses_old_style else None
            anchor_text = normalise_georgian(old_style_anchor.get_text(strip=True)) if old_style_anchor else None

            # ── Structural markers (standard classes) ──
            if "wignixml" in classes:
                # Book marker
                self._flush_article(
                    articles, document_id, metadata,
                    current_article_num, current_article_title,
                    current_paragraphs, current_book, current_part, current_chapter,
                )
                current_article_num = None
                current_paragraphs = []
                m = BOOK_RE.search(text)
                current_book = f"{m.group(1)}. {m.group(2).strip()}" if m else text

            elif "nawilixml" in classes:
                # Part marker
                self._flush_article(
                    articles, document_id, metadata,
                    current_article_num, current_article_title,
                    current_paragraphs, current_book, current_part, current_chapter,
                )
                current_article_num = None
                current_paragraphs = []
                m = PART_RE.search(text)
                current_part = f"{m.group(1)}. {m.group(2).strip()}" if m else text

            elif "tavixml" in classes:
                # Chapter marker
                self._flush_article(
                    articles, document_id, metadata,
                    current_article_num, current_article_title,
                    current_paragraphs, current_book, current_part, current_chapter,
                )
                current_article_num = None
                current_paragraphs = []
                m = CHAPTER_RE.search(text)
                current_chapter = f"{m.group(1)}. {m.group(2).strip()}" if m else text

            elif "muxlixml" in classes:
                # Article header — flush previous article, start new one
                self._flush_article(
                    articles, document_id, metadata,
                    current_article_num, current_article_title,
                    current_paragraphs, current_book, current_part, current_chapter,
                )
                m = ARTICLE_RE.search(text)
                if m:
                    current_article_num = normalise_superscripts(m.group(1))
                    current_article_title = m.group(2).strip() or None
                else:
                    # Fallback: try to extract article number from malformed text.
                    # Common case: "მუხლი7.სრულისათაური" (no space after მუხლი)
                    # or "მუხლის 1692. სათაური"
                    fallback_m = re.search(r"მუხლი\s*(\d+)", text)
                    if fallback_m:
                        current_article_num = normalise_superscripts(fallback_m.group(1))
                        # Extract title: everything after "number." or "number "
                        title_m = re.search(r"\d+\s*[.\-–—]\s*(.*)", text)
                        current_article_title = title_m.group(1).strip() if title_m else None
                    else:
                        # Last resort: log warning and use sanitised text
                        logger.warning("Unparseable article header: %s", text[:80])
                        current_article_num = text
                        current_article_title = None
                current_paragraphs = []

            elif "abzacixml" in classes:
                # Paragraph text — append to current article
                if current_article_num is not None:
                    current_paragraphs.append(text)

            # ── Old-style fallback: detect structure from anchor text ──
            elif anchor_text and uses_old_style:
                # Check for article header
                m_art = ARTICLE_RE.search(anchor_text)
                m_chap = CHAPTER_RE.search(anchor_text)
                m_part = PART_RE.search(anchor_text)
                m_book = BOOK_RE.search(anchor_text)

                if m_art:
                    self._flush_article(
                        articles, document_id, metadata,
                        current_article_num, current_article_title,
                        current_paragraphs, current_book, current_part, current_chapter,
                    )
                    current_article_num = normalise_superscripts(m_art.group(1))
                    current_article_title = m_art.group(2).strip() or None
                    current_paragraphs = []
                elif m_chap:
                    self._flush_article(
                        articles, document_id, metadata,
                        current_article_num, current_article_title,
                        current_paragraphs, current_book, current_part, current_chapter,
                    )
                    current_article_num = None
                    current_paragraphs = []
                    current_chapter = f"{m_chap.group(1)}. {m_chap.group(2).strip()}"
                elif m_part:
                    self._flush_article(
                        articles, document_id, metadata,
                        current_article_num, current_article_title,
                        current_paragraphs, current_book, current_part, current_chapter,
                    )
                    current_article_num = None
                    current_paragraphs = []
                    current_part = f"{m_part.group(1)}. {m_part.group(2).strip()}"
                elif m_book:
                    self._flush_article(
                        articles, document_id, metadata,
                        current_article_num, current_article_title,
                        current_paragraphs, current_book, current_part, current_chapter,
                    )
                    current_article_num = None
                    current_paragraphs = []
                    current_book = f"{m_book.group(1)}. {m_book.group(2).strip()}"

            # ── Old-style body text: plain <p> with content ──
            elif uses_old_style and not classes and current_article_num is not None:
                # In old-style docs, body text lives in plain <p> tags
                # (often with style="text-align: justify" but not always).
                # Skip amendment/footnote lines (italic citation links).
                if not p.find("a", class_="oldStyleDocumentPart"):
                    # Skip amendment footnotes (italic text with law references)
                    is_footnote = bool(p.find("i") and p.find("a") and "კანონი" in text)
                    if not is_footnote:
                        current_paragraphs.append(text)

        # Flush last article
        self._flush_article(
            articles, document_id, metadata,
            current_article_num, current_article_title,
            current_paragraphs, current_book, current_part, current_chapter,
        )

        return articles

    def _flush_article(
        self,
        articles: list[LegalArticle],
        document_id: str,
        metadata: DocumentMetadata,
        article_num: str | None,
        article_title: str | None,
        paragraph_texts: list[str],
        book: str | None,
        part: str | None,
        chapter: str | None,
    ) -> None:
        """Build a LegalArticle from accumulated data and append to list."""
        if article_num is None:
            return

        content_ka = "\n".join(paragraph_texts).strip()
        article_number = f"მუხლი {article_num}"

        # Parse cross-references
        refs = parse_references(content_ka)
        cross_ref_ids = [
            f"{document_id}.article_{r.article_number}"
            for r in refs
        ]

        # Build hierarchical article ID
        parts = [document_id]
        if book:
            parts.append(f"book_{book.split('.')[0].strip()}")
        if chapter:
            parts.append(f"chapter_{chapter.split('.')[0].strip()}")
        parts.append(f"article_{article_num}")
        article_id = ".".join(parts)

        # Parse numbered paragraphs from the collected text
        paragraphs = self._parse_paragraphs(content_ka)

        articles.append(LegalArticle(
            article_id=article_id,
            document_id=document_id,
            code_name=metadata.title_ka,
            book=book,
            part=part,
            chapter=chapter,
            article_number=article_number,
            article_title=article_title,
            content_ka=content_ka,
            paragraphs=paragraphs,
            cross_references=cross_ref_ids,
            effective_date=metadata.effective_date,
            is_repealed="გაუქმებული" in content_ka,
        ))

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

        if current_num is not None and current_lines:
            paragraphs.append(ArticleParagraph(
                number=current_num,
                text="\n".join(current_lines).strip(),
            ))

        return paragraphs
