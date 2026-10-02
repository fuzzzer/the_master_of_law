"""
Article Store Service — deterministic (code, article, paragraph) → full text.

Grounding mechanism A: exact lookups against the SQLite article store built by
the law_corpus pipeline (scripts/build_article_store.py). Unlike similarity
search, a lookup here either returns the full consolidated article text with
its matsne anchor, or proves the article does not exist in the corpus.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.services.trace_service import record_step
from app.utils.logger import get_logger

logger = get_logger(__name__)

_GEO_PREFIX = "საქართველოს "

# Article 166¹ is stored as "166-1" — the corpus pipeline's canonical form.
# It used to be flattened to "1661", where it collided with real articles.
_SUPERSCRIPT_MAP = str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")
_ARTICLE_NUMBER_RE = re.compile(r"(\d+)(?:\s*([¹²³⁴⁵⁶⁷⁸⁹⁰]+)|-(\d+)(?![ა-ჰ]))?")


def _normalize_article(article: str) -> str:
    """'მუხლი 48', '48-ე', '166¹', '166¹-ე', '166-1' → stored form ('48', '166-1')."""
    m = _ARTICLE_NUMBER_RE.search(article.replace("მუხლი", ""))
    if not m:
        return ""
    sub = (m.group(2) or "").translate(_SUPERSCRIPT_MAP) or m.group(3)
    return f"{m.group(1)}-{sub}" if sub else m.group(1)


def _version_date(article_id: str) -> date | None:
    """The date a dated version takes effect: 'article_61@2026-09-01'."""
    if "@" not in article_id:
        return None
    try:
        return date.fromisoformat(article_id.rsplit("@", 1)[1])
    except ValueError:
        return None


def _in_force(rows: list, today: date) -> Any:
    """Of an article's versions, the one in force today.

    matsne prints a coming text after the current one, under the same
    number, marked "(ამოქმედდეს …)". The latest version whose date has come
    wins over the undated text; a version still to come is used only when
    nothing else exists.
    """
    started = [r for r in rows if (d := _version_date(r["article_id"])) and d <= today]
    if started:
        return max(started, key=lambda r: _version_date(r["article_id"]))
    undated = [r for r in rows if _version_date(r["article_id"]) is None]
    return (undated or sorted(rows, key=lambda r: _version_date(r["article_id"])))[0]


def _in_force_per_article(rows: list, today: date) -> list:
    """Rows in order, one per (code, article) — the version in force."""
    groups: dict[tuple[str, str], list] = {}
    for r in rows:
        groups.setdefault((r["document_id"], r["article_norm"]), []).append(r)
    chosen = {id(_in_force(g, today)) for g in groups.values()}
    return [r for r in rows if id(r) in chosen]


def _normalize_code(code: str) -> str:
    return code.removeprefix(_GEO_PREFIX).strip().lower()


_PARAGRAPH_NUMBER_RE = re.compile(r"\d+(?:-\d+)?")


def provision_text(paragraphs: list[dict], paragraph: str, sub_point: str = "") -> str | None:
    """The text of paragraph (and sub-point) of an article, or None if absent.

    The store keeps an article's provisions as one flat list — "1", "ა",
    "გ", "2", "5", "ა", "გ" — so a letter belongs to the numbered paragraph
    above it. Matching a letter anywhere in the list would accept 47(1)(გ)
    for 47(5)(გ).
    """
    parent = ""
    for p in paragraphs:
        number = str(p.get("number", "")).strip()
        if _PARAGRAPH_NUMBER_RE.fullmatch(number):  # "2", or "2-1" for 2¹
            parent = number
            if number == paragraph and not sub_point:
                return p.get("text", "")
        elif sub_point and number == sub_point and parent == paragraph:
            return p.get("text", "")
    return None


class ArticleStoreService:
    """Read-only lookups against the article store SQLite DB."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or (
            Path(settings.chroma_persist_dir).parent / "georgian_laws" / "article_store.db"
        )
        self._code_lookup: dict[str, str] | None = None  # normalized name → document_id
        self._code_text_cache: dict[str, tuple[str, int]] = {}  # document_id → (text, count)

    @property
    def is_available(self) -> bool:
        return self._db_path.exists()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            f"file:{self._db_path}?mode=ro&immutable=1", uri=True
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _load_code_lookup(self) -> dict[str, str]:
        """Map document_id and normalized Georgian names to document_id."""
        if self._code_lookup is not None:
            return self._code_lookup
        lookup: dict[str, str] = {}
        with self._connect() as conn:
            for row in conn.execute("SELECT document_id, code_name FROM codes"):
                doc_id = row["document_id"]
                lookup[doc_id.lower()] = doc_id
                lookup[_normalize_code(row["code_name"])] = doc_id
        self._code_lookup = lookup
        return lookup

    def resolve_code(self, code: str) -> str | None:
        """Resolve a document_id or (partial) Georgian code name to a document_id."""
        if not code:
            return None
        lookup = self._load_code_lookup()
        normalized = _normalize_code(code)
        if normalized in lookup:
            return lookup[normalized]
        # containment fallback: "შრომის კოდექსი" inside the full stored name
        for name, doc_id in lookup.items():
            if normalized and (normalized in name or name in normalized):
                return doc_id
        return None

    def get_article(
        self,
        code: str,
        article: str,
        paragraph: str | None = None,
    ) -> dict[str, Any] | None:
        """Exact article lookup.

        Parameters
        ----------
        code : str
            document_id ("labour_code") or Georgian code name (with or
            without the "საქართველოს" prefix).
        article : str
            "48", "მუხლი 48", "48-ე", or 166¹ as "166¹" or "166-1".
        paragraph : str | None
            If given, the matching paragraph is surfaced under "paragraph".
        """
        if not self.is_available:
            return None
        doc_id = self.resolve_code(code)
        norm = _normalize_article(article)
        if not norm:
            return None

        # One number is one article; several rows are its dated versions.
        with self._connect() as conn:
            if doc_id:
                rows = conn.execute(
                    "SELECT * FROM articles WHERE document_id = ? AND article_norm = ?",
                    (doc_id, norm),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM articles WHERE article_norm = ? ORDER BY document_id", (norm,)
                ).fetchall()
                rows = [r for r in rows if r["document_id"] == rows[0]["document_id"]] if rows else []
        row = _in_force(rows, date.today()) if rows else None

        result = self._row_to_article(row) if row else None
        if result and paragraph:
            wanted = str(paragraph).strip()
            result["paragraph"] = next(
                (p for p in result["paragraphs"] if str(p.get("number")) == wanted),
                None,
            )
        record_step(
            "article_store_lookup",
            code=code,
            article=article,
            paragraph=paragraph,
            resolved_document_id=doc_id,
            found=result is not None,
            article_id=result["article_id"] if result else None,
        )
        return result

    def fts_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Full-text search over article titles and content (FTS5)."""
        if not self.is_available or not query.strip():
            return []
        # Quote each token to keep FTS5 syntax characters inert
        match_expr = " ".join(
            '"' + t.replace('"', "") + '"' for t in query.split()
        )
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT a.* FROM articles_fts f "
                    "JOIN articles a ON a.article_id = f.article_id "
                    "WHERE articles_fts MATCH ? ORDER BY rank LIMIT ?",
                    (match_expr, limit),
                ).fetchall()
        except sqlite3.OperationalError as e:
            logger.warning("article_store_fts_failed", error=str(e), query=query[:80])
            return []
        return [self._row_to_article(r) for r in rows]

    def has_article_url(self, url: str) -> bool:
        """True if the URL byte-matches a store article URL (cached set)."""
        if not self.is_available:
            return False
        if not hasattr(self, "_url_set"):
            with self._connect() as conn:
                self._url_set = {
                    r[0] for r in conn.execute("SELECT article_url FROM articles")
                }
        return url in self._url_set

    def list_codes(self) -> list[dict[str, Any]]:
        """All codes in the store with article counts."""
        if not self.is_available:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT document_id, code_name, document_number, source_url, article_count "
                "FROM codes ORDER BY document_id"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_code_articles(
        self, code: str, chapter: str | None = None
    ) -> list[dict[str, Any]]:
        """All (non-repealed) articles of a code, optionally one chapter, in order."""
        doc_id = self.resolve_code(code)
        if not doc_id or not self.is_available:
            return []
        sql = (
            "SELECT * FROM articles WHERE document_id = ? AND is_repealed = 0"
        )
        params: list[Any] = [doc_id]
        if chapter:
            sql += " AND chapter LIKE ?"
            params.append(f"%{chapter}%")
        sql += " ORDER BY CAST(article_norm AS INTEGER), article_norm"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_article(r) for r in _in_force_per_article(rows, date.today())]

    def get_code_full_text(self, code: str) -> tuple[str, int] | None:
        """Concatenated full text of a code for whole-code context injection.

        Returns (text, article_count) or None if the code is unknown.
        Memoized — the store is immutable for the process lifetime.
        """
        doc_id = self.resolve_code(code)
        if doc_id and doc_id in self._code_text_cache:
            return self._code_text_cache[doc_id]
        articles = self.get_code_articles(code)
        if not articles:
            return None
        parts: list[str] = []
        for art in articles:
            header = f"{art['article_number']}. {art['article_title'] or ''}".strip()
            parts.append(f"{header}\nURL: {art['article_url']}\n{art['content_ka']}")
        result = ("\n\n".join(parts), len(articles))
        if doc_id:
            self._code_text_cache[doc_id] = result
        return result

    @staticmethod
    def _row_to_article(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "article_id": row["article_id"],
            "document_id": row["document_id"],
            "code_name": row["code_name"],
            "article_number": row["article_number"],
            "article_title": row["article_title"],
            "book": row["book"],
            "part": row["part"],
            "chapter": row["chapter"],
            "content_ka": row["content_ka"],
            "paragraphs": json.loads(row["paragraphs_json"]),
            "cross_references": json.loads(row["cross_references_json"]),
            "article_url": row["article_url"],
            "is_repealed": bool(row["is_repealed"]),
        }


_article_store: ArticleStoreService | None = None


def get_article_store_service() -> ArticleStoreService:
    global _article_store
    if _article_store is None:
        _article_store = ArticleStoreService()
        logger.info(
            "article_store_initialized",
            path=str(_article_store._db_path),
            available=_article_store.is_available,
        )
    return _article_store
