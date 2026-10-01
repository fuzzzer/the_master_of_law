#!/usr/bin/env python3
"""
Build the deterministic article store (SQLite + FTS5) from parsed law JSON.

Pipeline output step: reads data/georgian_laws/parsed/*.json (produced by the
existing parse step) and writes data/georgian_laws/article_store.db — the
backend's exact-lookup grounding source (mechanism A of the grounding plan).

The DB is opened read-only (immutable) by the backend, so it is built with
journal_mode=DELETE — no WAL sidecar files that would break a read-only mount.

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
    article_count INTEGER NOT NULL
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
    effective_date TEXT
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


def _article_norm(article_id: str, article_number: str) -> str:
    """Bare article number used for lookups and the matsne anchor."""
    if "article_" in article_id:
        return article_id.rsplit("article_", 1)[-1]
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
        conn.execute(
            "INSERT INTO codes VALUES (?, ?, ?, ?, ?, ?)",
            (
                document_id,
                code_name,
                meta.get("title_en"),
                meta.get("document_number"),
                source_url,
                len(articles),
            ),
        )
        stats["codes"] += 1

        for art in articles:
            norm = _article_norm(art.get("article_id", ""), art.get("article_number", ""))
            paragraphs = art.get("paragraphs") or []
            conn.execute(
                "INSERT OR REPLACE INTO articles VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
