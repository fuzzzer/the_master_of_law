"""
Extracts structured legal hierarchy from parsed HTML/text.

Georgian legal hierarchy:
    კოდექსი (Code) → წიგნი (Book) → კარი (Part) → თავი (Chapter) → მუხლი (Article) → პუნქტი (Paragraph)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from pipeline.utils.georgian_text import normalise_georgian, normalise_superscripts
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StructuralNode:
    """A node in the legal document hierarchy."""
    level: str           # "book", "part", "chapter", "article", "paragraph"
    number: str          # "1", "2", "3-1", etc.
    title: str           # Section title text
    content: str = ""    # Text content (mainly for articles/paragraphs)
    children: list["StructuralNode"] = field(default_factory=list)


# ── Regex patterns for Georgian legal structure ──────────────

PATTERNS = {
    "book": re.compile(r"წიგნი\s+([IVXLCDM\d]+)\s*[.\-–—]?\s*(.*)", re.UNICODE),
    "part": re.compile(r"კარი\s+([IVXLCDM\d]+)\s*[.\-–—]?\s*(.*)", re.UNICODE),
    "chapter": re.compile(r"თავი\s+([IVXLCDM\d]+)\s*[.\-–—]?\s*(.*)", re.UNICODE),
    "article": re.compile(
        r"მუხლი\s+(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)\s*[.\-–—]?\s*(.*)",
        re.UNICODE,
    ),
}

# Paragraph/point patterns
PARAGRAPH_PATTERN = re.compile(r"^\s*(\d+)\s*[.)]\s*(.*)", re.UNICODE | re.DOTALL)
GEORGIAN_LETTER_PATTERN = re.compile(
    r"^\s*([ა-ჰ](?:\.[ა-ჰ])?)\s*\)\s*(.*)", re.UNICODE | re.DOTALL
)


class StructureExtractor:
    """Extract the hierarchical structure of a Georgian legal document."""

    def extract(self, text: str) -> list[StructuralNode]:
        """Parse raw text into a tree of StructuralNodes."""
        text = normalise_georgian(text)
        lines = text.split("\n")
        root_children: list[StructuralNode] = []

        current_book: Optional[StructuralNode] = None
        current_part: Optional[StructuralNode] = None
        current_chapter: Optional[StructuralNode] = None
        current_article: Optional[StructuralNode] = None
        content_buffer: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Try to match structural markers (highest to lowest)
            book_m = PATTERNS["book"].match(stripped)
            part_m = PATTERNS["part"].match(stripped)
            chapter_m = PATTERNS["chapter"].match(stripped)
            article_m = PATTERNS["article"].match(stripped)

            if book_m:
                self._flush_content(current_article, content_buffer)
                node = StructuralNode(
                    level="book",
                    number=book_m.group(1),
                    title=book_m.group(2).strip(),
                )
                root_children.append(node)
                current_book = node
                current_part = None
                current_chapter = None
                current_article = None

            elif part_m:
                self._flush_content(current_article, content_buffer)
                node = StructuralNode(
                    level="part",
                    number=part_m.group(1),
                    title=part_m.group(2).strip(),
                )
                parent = current_book or root_children
                if isinstance(parent, StructuralNode):
                    parent.children.append(node)
                else:
                    root_children.append(node)
                current_part = node
                current_chapter = None
                current_article = None

            elif chapter_m:
                self._flush_content(current_article, content_buffer)
                node = StructuralNode(
                    level="chapter",
                    number=chapter_m.group(1),
                    title=chapter_m.group(2).strip(),
                )
                parent = current_part or current_book
                if parent:
                    parent.children.append(node)
                else:
                    root_children.append(node)
                current_chapter = node
                current_article = None

            elif article_m:
                self._flush_content(current_article, content_buffer)
                num = normalise_superscripts(article_m.group(1))
                node = StructuralNode(
                    level="article",
                    number=num,
                    title=article_m.group(2).strip(),
                )
                parent = current_chapter or current_part or current_book
                if parent:
                    parent.children.append(node)
                else:
                    root_children.append(node)
                current_article = node

            else:
                # Accumulate content for the current article
                content_buffer.append(stripped)

        # Flush remaining content
        self._flush_content(current_article, content_buffer)

        return root_children

    @staticmethod
    def _flush_content(
        article: Optional[StructuralNode],
        buffer: list[str],
    ) -> None:
        """Append buffered lines to the current article's content."""
        if article is not None and buffer:
            article.content += "\n".join(buffer) + "\n"
        buffer.clear()

    def flatten_articles(
        self,
        nodes: list[StructuralNode],
        path: dict[str, str] | None = None,
    ) -> list[dict]:
        """
        Flatten the tree into a list of article dicts with their
        hierarchical path (book, part, chapter) attached.
        """
        path = path or {}
        articles: list[dict] = []

        for node in nodes:
            new_path = {**path}
            if node.level in ("book", "part", "chapter"):
                new_path[node.level] = f"{node.number}. {node.title}".strip()
                articles.extend(self.flatten_articles(node.children, new_path))
            elif node.level == "article":
                articles.append({
                    "number": node.number,
                    "title": node.title,
                    "content": node.content.strip(),
                    "book": new_path.get("book"),
                    "part": new_path.get("part"),
                    "chapter": new_path.get("chapter"),
                })
                # Also flatten any sub-articles
                if node.children:
                    articles.extend(self.flatten_articles(node.children, new_path))

        return articles
