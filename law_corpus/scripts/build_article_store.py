#!/usr/bin/env python3
"""
Build the deterministic article store (SQLite + FTS5) from parsed law JSON.

Pipeline output step: reads data/georgian_laws/parsed/*.json (produced by the
existing parse step) and writes data/georgian_laws/article_store.db — the
backend's exact-lookup grounding source (mechanism A of the grounding plan).

The DB is opened read-only (immutable) by the backend, so it is built with
journal_mode=DELETE — no WAL sidecar files that would break a read-only mount.

Schema version 2 (PRAGMA user_version) adds provenance columns at the end of
``codes`` and ``articles`` — matsne version date, publication number, versioned
URL, retrieval time, the article's real matsne anchor, and whether a row is a
future wording not yet in force. Readers that select columns by name keep
working on both versions.

Usage:
    python scripts/build_article_store.py [--parsed-dir DIR] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PARSED_DIR = PROJECT_DIR / "data" / "georgian_laws" / "parsed"
DEFAULT_OUT = PROJECT_DIR / "data" / "georgian_laws" / "article_store.db"

SCHEMA = """
CREATE TABLE codes (
    document_id   TEXT PRIMARY KEY,
    code_name     TEXT NOT NULL,
    title_en      TEXT,
    document_number TEXT,
    source_url    TEXT NOT NULL,
    article_count INTEGER NOT NULL,
    publication_id TEXT,                   -- matsne consolidated publication number
    version_date  TEXT,                    -- ISO date of that consolidated version
    version_url   TEXT,                    -- source_url?publication=N (exact text held)
    retrieved_at  TEXT,                    -- ISO UTC time the page was fetched
    content_sha256 TEXT                    -- hash of the fetched page
);

CREATE TABLE articles (
    article_id    TEXT PRIMARY KEY,
    document_id   TEXT NOT NULL REFERENCES codes(document_id),
    code_name     TEXT NOT NULL,
    article_number TEXT NOT NULL,          -- "მუხლი 48"
    article_norm  TEXT NOT NULL,           -- "48" (bare number, from article_id)
    article_title TEXT,
    book          TEXT,
    part          TEXT,
    chapter       TEXT,
    content_ka    TEXT NOT NULL,
    paragraphs_json TEXT NOT NULL,         -- JSON: [{number, text, sub_points}]
    cross_references_json TEXT NOT NULL,   -- JSON: ["labour_code.article_47", ...]
    article_url   TEXT NOT NULL,           -- source_url#article_<norm>
    is_repealed   INTEGER NOT NULL DEFAULT 0,
    effective_date TEXT,
    in_force      INTEGER NOT NULL DEFAULT 1, -- 0: future wording ("ამოქმედდეს …")
    matsne_anchor TEXT,                    -- in-page anchor on matsne ("part_476")
    official_url  TEXT,                    -- source_url#<matsne_anchor>: opens the article
    version_date  TEXT                     -- the code's consolidated version date
);

CREATE INDEX idx_articles_doc_norm  ON articles(document_id, article_norm);
CREATE INDEX idx_articles_code_norm ON articles(code_name, article_norm);

CREATE VIRTUAL TABLE articles_fts USING fts5(
    article_id UNINDEXED,
    code_name,
    article_number,
    article_title,
    content_ka
);
"""


SCHEMA_VERSION = 2

CODE_COLUMNS = (
    "document_id", "code_name", "title_en", "document_number", "source_url",
    "article_count", "publication_id", "version_date", "version_url",
    "retrieved_at", "content_sha256",
)
ARTICLE_COLUMNS = (
    "article_id", "document_id", "code_name", "article_number", "article_norm",
    "article_title", "book", "part", "chapter", "content_ka", "paragraphs_json",
    "cross_references_json", "article_url", "is_repealed", "effective_date",
    "in_force", "matsne_anchor", "official_url", "version_date",
)


def _insert_sql(table: str, columns: tuple[str, ...]) -> str:
    return (
        f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) "
        f"VALUES ({', '.join('?' for _ in columns)})"
    )


def _article_norm(article_id: str, article_number: str) -> str:
    """Bare article number used for lookups and the matsne anchor ("259-1" for 259¹)."""
    if "article_" in article_id:
        return article_id.rsplit("article_", 1)[-1].split(".")[0]
    return "".join(ch for ch in article_number if ch.isdigit())


def build(parsed_dir: Path, out_path: Path) -> dict[str, int]:
    files = sorted(parsed_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"No parsed files found in {parsed_dir}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    conn = sqlite3.connect(out_path)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    stats = {"codes": 0, "articles": 0, "paragraphs": 0}
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        meta = doc.get("metadata", {})
        articles = doc.get("articles", [])
        if not articles:
            print(f"  ⚠ {path.name}: 0 articles — skipped")
            continue

        document_id = meta.get("document_id") or path.stem
        code_name = meta.get("title_ka", "")
        source_url = meta.get("source_url", "")
        publication_id = meta.get("publication_id")
        version_date = meta.get("version_date")
        conn.execute(
            _insert_sql("codes", CODE_COLUMNS),
            (
                document_id,
                code_name,
                meta.get("title_en"),
                meta.get("document_number"),
                source_url,
                len(articles),
                publication_id,
                version_date,
                f"{source_url}?publication={publication_id}" if source_url and publication_id else None,
                meta.get("scraped_at"),
                meta.get("content_hash"),
            ),
        )
        stats["codes"] += 1

        for art in articles:
            norm = _article_norm(art.get("article_id", ""), art.get("article_number", ""))
            paragraphs = art.get("paragraphs") or []
            anchor = art.get("matsne_anchor")
            conn.execute(
                _insert_sql("articles", ARTICLE_COLUMNS),
                (
                    art.get("article_id"),
                    document_id,
                    art.get("code_name") or code_name,
                    art.get("article_number", ""),
                    norm,
                    art.get("article_title"),
                    art.get("book"),
                    art.get("part"),
                    art.get("chapter"),
                    art.get("content_ka") or "",
                    json.dumps(paragraphs, ensure_ascii=False),
                    json.dumps(art.get("cross_references") or [], ensure_ascii=False),
                    f"{source_url}#article_{norm}" if source_url else "",
                    1 if art.get("is_repealed") else 0,
                    art.get("effective_date"),
                    0 if art.get("in_force") is False else 1,
                    anchor,
                    f"{source_url}#{anchor}" if source_url and anchor else source_url,
                    version_date,
                ),
            )
            conn.execute(
                "INSERT INTO articles_fts VALUES (?, ?, ?, ?, ?)",
                (
                    art.get("article_id"),
                    art.get("code_name") or code_name,
                    art.get("article_number", ""),
                    art.get("article_title") or "",
                    art.get("content_ka") or "",
                ),
            )
            stats["articles"] += 1
            stats["paragraphs"] += len(paragraphs)

    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parsed-dir", type=Path, default=DEFAULT_PARSED_DIR)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    print(f"Building article store from {args.parsed_dir} → {args.out}")
    stats = build(args.parsed_dir, args.out)
    print(
        f"  ✓ {stats['codes']} codes, {stats['articles']} articles, "
        f"{stats['paragraphs']} paragraphs → {args.out} "
        f"({args.out.stat().st_size / 1024 / 1024:.1f} MB)"
    )


if __name__ == "__main__":
    main()
