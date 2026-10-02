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

import copy
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
    r"მუხლი\s*(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)

# The source of an amendment, printed under the article it changed:
# "საქართველოს 2016 წლის 2 მარტის კანონი №4798 – ვებგვერდი, 14.03.2016წ."
AMENDMENT_NOTE_RE = re.compile(
    r"^საქართველოს\s.{0,200}?"
    r"(?:კანონი|დეკრეტი|დადგენილება|გადაწყვეტილება|განჩინება|ბრძანებულება)"
    r"\s*(?:№\s*[^\s–]+)?[\s\u00ad]*[–-]",
    re.UNICODE,
)
SEPARATOR_RE = re.compile(r"^[-–—_*\s]+$")

# matsne's own per-article anchor: <a name="part_233">. The page has no
# "#article_N" anchors, so links built on article numbers opened the top.
PART_ANCHOR_RE = re.compile(r"^part_\d+$")
_TO_SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_INVISIBLE_RE = re.compile(r"[\s\u200b\u200c\u200d\ufeff]+")
_HYPHEN_NUMBER_RE = re.compile(r"^(\d+)-(\d+)$")


def element_text(el) -> str:
    """Normalised text of an element, with `<sup>` digits kept.

    matsne writes 52¹ as `52<sup>1</sup>`; get_text() drops the tag, so 52¹
    became "521" and collided with real article 521. The digits are turned
    into superscript characters first, which normalise_georgian then writes
    in the corpus's canonical "52-1" form.
    """
    el = copy.copy(el)
    for sup in el.find_all("sup"):
        digits = _INVISIBLE_RE.sub("", sup.get_text())  # "<sup>\u200b3</sup>" occurs
        if digits.isdigit():
            sup.replace_with(digits.translate(_TO_SUPERSCRIPT))
    return normalise_georgian(el.get_text(strip=True))


def display_article_number(article_num: str) -> str:
    """The canonical "52-1" as matsne and the courts write it: "52¹"."""
    m = _HYPHEN_NUMBER_RE.match(article_num)
    return f"{m.group(1)}{m.group(2).translate(_TO_SUPERSCRIPT)}" if m else article_num


_GEORGIAN_MONTHS = {
    "იანვ": 1, "თებერვ": 2, "მარტ": 3, "აპრილ": 4, "მაის": 5, "ივნის": 6,
    "ივლის": 7, "აგვისტ": 8, "სექტემბ": 9, "ოქტომბ": 10, "ნოემბ": 11, "დეკემბ": 12,
}
# Only the bracketed note marks a version; "ეს კოდექსი ამოქმედდეს 2000 წლის
# 1 იანვრიდან" without brackets is a transitional rule of the law itself.
_TAKES_EFFECT_RE = re.compile(r"\(ამოქმედდეს\s+(\d{4})\s+წლის\s+(\d{1,2})\s+([ა-ჰ]+)")


def takes_effect_on(text: str) -> str | None:
    """ISO date of a version matsne marks "(ამოქმედდეს 2027 წლის 1 იანვრიდან)".

    matsne prints such a version right after the text it will replace, under
    the same number; without the date both had one id and one overwrote the
    other in the store.
    """
    m = _TAKES_EFFECT_RE.search(text)
    if not m:
        return None
    month = next((n for stem, n in _GEORGIAN_MONTHS.items() if m.group(3).startswith(stem)), None)
    return f"{m.group(1)}-{month:02d}-{int(m.group(2)):02d}" if month else None


_FROM_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def _id_safe(number: str) -> str:
    """Chapter "XII¹" → "XII-1" in ids, the form article numbers use."""
    return re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "-" + m.group(0).translate(_FROM_SUPERSCRIPT), number)


def article_anchor(el) -> str | None:
    a = el.find("a", attrs={"name": PART_ANCHOR_RE})
    return a["name"] if a else None

CHAPTER_RE = re.compile(
    r"თავი\s+([IVXLCDM\d]+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|-\d+)?)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)

BOOK_RE = re.compile(
    r"წიგნი\s+([IVXLCDM\d]+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|-\d+)?)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)

PART_RE = re.compile(
    r"კარი\s+([IVXLCDM\d]+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|-\d+)?)\s*[.\-–—]?\s*(.*)",
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
        current_article_anchor: str | None = None
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
            text = element_text(p)
            if not text:
                continue

            # ── Check for oldStyleDocumentPart anchors inside this <p> ──
            old_style_anchor = p.find("a", class_="oldStyleDocumentPart") if uses_old_style else None
            anchor_text = element_text(old_style_anchor) if old_style_anchor else None

            # ── Structural markers (standard classes) ──
            if "wignixml" in classes:
                # Book marker
                self._flush_article(
                    articles, document_id, metadata,
                    current_article_num, current_article_title,
                    current_paragraphs, current_book, current_part, current_chapter,
                    anchor=current_article_anchor,
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
                    anchor=current_article_anchor,
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
                    anchor=current_article_anchor,
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
                    anchor=current_article_anchor,
                )
                current_article_anchor = article_anchor(p)
                m = ARTICLE_RE.search(text)
                if m:
                    current_article_num = normalise_superscripts(m.group(1))
                    current_article_title = m.group(2).strip() or None
                else:
                    # Fallback: try to extract article number from malformed text.
                    # Common case: "მუხლი7.სრულისათაური" (no space after მუხლი)
                    # or "მუხლის 1692. სათაური"
                    fallback_m = re.search(r"მუხლი\s*(\d+(?:-\d+)?)", text)
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
                        anchor=current_article_anchor,
                    )
                    current_article_num = normalise_superscripts(m_art.group(1))
                    current_article_title = m_art.group(2).strip() or None
                    current_article_anchor = article_anchor(p)
                    current_paragraphs = []
                elif m_chap:
                    self._flush_article(
                        articles, document_id, metadata,
                        current_article_num, current_article_title,
                        current_paragraphs, current_book, current_part, current_chapter,
                        anchor=current_article_anchor,
                    )
                    current_article_num = None
                    current_paragraphs = []
                    current_chapter = f"{m_chap.group(1)}. {m_chap.group(2).strip()}"
                elif m_part:
                    self._flush_article(
                        articles, document_id, metadata,
                        current_article_num, current_article_title,
                        current_paragraphs, current_book, current_part, current_chapter,
                        anchor=current_article_anchor,
                    )
                    current_article_num = None
                    current_paragraphs = []
                    current_part = f"{m_part.group(1)}. {m_part.group(2).strip()}"
                elif m_book:
                    self._flush_article(
                        articles, document_id, metadata,
                        current_article_num, current_article_title,
                        current_paragraphs, current_book, current_part, current_chapter,
                        anchor=current_article_anchor,
                    )
                    current_article_num = None
                    current_paragraphs = []
                    current_book = f"{m_book.group(1)}. {m_book.group(2).strip()}"

            # ── Old-style body text: plain <p> with content ──
            # ── Old-style header with neither class nor anchor: <p><b>მუხლი 14¹. …
            # It used to be read as body text of the article before it.
            elif (
                uses_old_style and not classes and p.find("b")
                and not p.find("a", class_="oldStyleDocumentPart")
                and (m_bare := re.match(r"მუხლი\s*(\d+(?:-\d+)?)\s*[.\-–—]\s*(.*)", text))
            ):
                self._flush_article(
                    articles, document_id, metadata,
                    current_article_num, current_article_title,
                    current_paragraphs, current_book, current_part, current_chapter,
                    anchor=current_article_anchor,
                )
                current_article_num = m_bare.group(1)
                current_article_title = m_bare.group(2).strip() or None
                current_article_anchor = None
                current_paragraphs = []

            elif not classes and current_article_num is not None:
                # Body text in a plain <p>: all of it in old-style docs, and
                # in class-style docs too — the last paragraph of a version
                # with its "(ამოქმედდეს …)]" note is a classless <p>, and
                # skipping it dropped law text (a fine's amount) from the store.
                # Skip amendment/footnote lines (italic citation links).
                if not p.find("a", class_="oldStyleDocumentPart"):
                    # Skip amendment footnotes (italic text with law references)
                    is_footnote = bool(
                        (p.find("i") and p.find("a") and "კანონი" in text)
                        or AMENDMENT_NOTE_RE.match(text)
                        or SEPARATOR_RE.match(text)
                    )
                    if not is_footnote:
                        current_paragraphs.append(text)

        # Flush last article
        self._flush_article(
            articles, document_id, metadata,
            current_article_num, current_article_title,
            current_paragraphs, current_book, current_part, current_chapter,
            anchor=current_article_anchor,
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
        anchor: str | None = None,
    ) -> None:
        """Build a LegalArticle from accumulated data and append to list."""
        if article_num is None:
            return

        content_ka = "\n".join(paragraph_texts).strip()
        article_number = f"მუხლი {display_article_number(article_num)}"

        # Parse cross-references
        refs = parse_references(content_ka)
        cross_ref_ids = [
            f"{document_id}.article_{r.article_number}"
            for r in refs
        ]

        # Build hierarchical article ID
        parts = [document_id]
        if book:
            parts.append(f"book_{_id_safe(book.split('.')[0].strip())}")
        if chapter:
            parts.append(f"chapter_{_id_safe(chapter.split('.')[0].strip())}")
        parts.append(f"article_{article_num}")
        article_id = ".".join(parts)
        if effective_from := takes_effect_on(f"{article_title or ''} {content_ka}"):
            article_id += f"@{effective_from}"

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
            source_anchor=anchor,
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

        # "2-1." is paragraph 2¹ (written 2<sup>1</sup> on matsne)
        num_pattern = re.compile(r"^\s*(\d+(?:-\d+)?)\s*[.)]\s*(.*)", re.UNICODE)
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
