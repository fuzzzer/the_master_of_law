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
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.services.trace_service import record_step
from app.utils.logger import get_logger

logger = get_logger(__name__)

_GEO_PREFIX = "საქართველოს "

# Superscript digits in article numbers like "მუხლი 166¹". Stores since schema
# version 2 keep them apart ("166-1"); older stores flattened them ("1661"),
# which made 11¹ and 111 the same key.
_SUPERSCRIPT_MAP = str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")
_ARTICLE_NUMBER_RE = re.compile(r"(\d+)\s*([¹²³⁴⁵⁶⁷⁸⁹⁰]*)(?:-(\d+)(?![ა-ჰ]))?")


def _normalize_article(article: str) -> str:
    """'მუხლი 48', '48-ე', '48', '166¹', '166-1' → stored form ('48', '166-1')."""
    a = article.replace("მუხლი", "").strip()
    m = _ARTICLE_NUMBER_RE.match(a)
    if not m:
        return a
    sub = m.group(2).translate(_SUPERSCRIPT_MAP) or m.group(3)
    return f"{m.group(1)}-{sub}" if sub else m.group(1)


def _legacy_norm(norm: str) -> str:
    """Key of the same article in a pre-version-2 store ('166-1' → '1661')."""
    return norm.replace("-", "")


def _normalize_code(code: str) -> str:
    return code.removeprefix(_GEO_PREFIX).strip().lower()


# Version and source columns that newer store builds may carry. Passed through
# when present so callers can show when a text was in force; older stores
# simply lack them.
OPTIONAL_ARTICLE_COLUMNS = (
    "effective_date",
    "version_date",
    "in_force_since",
    "source_url",
    "matsne_url",
)

_FTS_TOKEN_CHARS = re.compile(r"[\w\u10D0-\u10FF]+")


def _query_tokens(query: str) -> list[str]:
    return _FTS_TOKEN_CHARS.findall(query)


def _all_tokens_expression(query: str) -> str:
    """Every token must match. Quoting keeps FTS5 syntax characters inert."""
    return " ".join(f'"{t}"' for t in _query_tokens(query))


def _any_token_expression(query: str) -> str:
    """Any token or its stem may match: long words become prefix queries."""
    terms: list[str] = []
    for token in _query_tokens(query):
        if token.isdigit():
            terms.append(f'"{token}"')
        elif len(token) >= 6:
            terms.append(f'"{token[:-2]}"*')
        elif len(token) >= 4:
            terms.append(f'"{token[:-1]}"*')
    return " OR ".join(terms)


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
            "48", "მუხლი 48", "48-ე" or superscript forms ("166¹").
        paragraph : str | None
            If given, the matching paragraph is surfaced under "paragraph".
        """
        if not self.is_available:
            return None
        doc_id = self.resolve_code(code)
        norm = _normalize_article(article)
        if not norm:
            return None

        # Some numbers map to several rows (removed placeholders, future
        # wordings) — prefer rows in force with substantive content.
        in_force_first = "in_force DESC, " if self._has_column("in_force") else ""
        selection = (
            f"ORDER BY {in_force_first}(article_title LIKE '%ამოღებულია%') ASC, "
            "LENGTH(article_id) ASC LIMIT 1"
        )
        key = norm if self._has_column("in_force") else _legacy_norm(norm)
        with self._connect() as conn:
            if doc_id:
                row = conn.execute(
                    f"SELECT * FROM articles WHERE document_id = ? AND article_norm = ? {selection}",
                    (doc_id, key),
                ).fetchone()
            else:
                row = conn.execute(
                    f"SELECT * FROM articles WHERE article_norm = ? {selection}", (key,)
                ).fetchone()

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

    def fts_search(
        self,
        query: str,
        limit: int = 10,
        document_id: str | None = None,
        match_any: bool = False,
    ) -> list[dict[str, Any]]:
        """Full-text search over article titles and content (FTS5).

        By default every token must match. ``match_any`` matches any token
        and also word-stem prefixes, because Georgian inflects nouns
        ("ხელშეკრულება" / "ხელშეკრულების") and a literal match misses them.
        ``document_id`` restricts the search to one code.
        """
        if not self.is_available or not query.strip():
            return []
        match_expr = _any_token_expression(query) if match_any else _all_tokens_expression(query)
        if not match_expr:
            return []
        sql = (
            "SELECT a.* FROM articles_fts f "
            "JOIN articles a ON a.article_id = f.article_id "
            "WHERE articles_fts MATCH ?"
        )
        params: list[Any] = [match_expr]
        if document_id:
            sql += " AND a.document_id = ?"
            params.append(document_id)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError as e:
            logger.warning("article_store_fts_failed", error=str(e), query=query[:80])
            return []
        return [self._row_to_article(r) for r in rows]

    def keyword_search(
        self, query: str, limit: int = 20, code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Keyword search that needs no model call, ranked by BM25.

        Georgian words carry case endings ("ხელშეკრულების", "ხელშეკრულებით"),
        so each word is matched by its stem as a prefix, and any word may
        match (OR) — exact all-words matching finds almost nothing for an
        everyday question.
        """
        if not self.is_available:
            return []
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) >= 3][:12]
        if not words:
            return []
        match_expr = " OR ".join(
            '"' + (w[:-2] if len(w) > 5 else w) + '"*' for w in words
        )
        sql = (
            "SELECT a.* FROM articles_fts f JOIN articles a ON a.article_id = f.article_id "
            "WHERE articles_fts MATCH ? AND a.is_repealed = 0"
        )
        params: list[Any] = [match_expr]
        if code:
            doc_id = self.resolve_code(code)
            if not doc_id:
                return []
            sql += " AND a.document_id = ?"
            params.append(doc_id)
        sql += " ORDER BY bm25(articles_fts) LIMIT ?"
        params.append(limit)
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError as e:
            logger.warning("article_store_keyword_search_failed", error=str(e), query=query[:80])
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

    def _has_column(self, column: str) -> bool:
        """True if the store's articles table has *column* (schema version 2+)."""
        if not hasattr(self, "_article_columns"):
            with self._connect() as conn:
                self._article_columns = {
                    r[1] for r in conn.execute("PRAGMA table_info(articles)")
                }
        return column in self._article_columns

    def list_codes(self) -> list[dict[str, Any]]:
        """All codes in the store with article counts."""
        if not self.is_available:
            return []
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM codes ORDER BY document_id").fetchall()
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
        if self._has_column("in_force"):
            sql += " AND in_force = 1"
        params: list[Any] = [doc_id]
        if chapter:
            sql += " AND chapter LIKE ?"
            params.append(f"%{chapter}%")
        sql += " ORDER BY CAST(article_norm AS INTEGER), article_norm"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_article(r) for r in rows]

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
        columns = row.keys()
        optional = {c: row[c] for c in OPTIONAL_ARTICLE_COLUMNS if c in columns}
        return optional | {
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
            # Schema version 2: official matsne link and version (None on older stores)
            "official_url": row["official_url"] if "official_url" in row.keys() else None,
            "version_date": row["version_date"] if "version_date" in row.keys() else None,
            "in_force": bool(row["in_force"]) if "in_force" in row.keys() else True,
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
