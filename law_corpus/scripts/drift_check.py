#!/usr/bin/env python3
"""
Live drift sampling (grounding plan 3.3) — belt-and-suspenders on top of the
incremental-update pipeline.

Samples N random non-repealed articles from article_store.db, fetches each
code's live matsne.gov.ge page, and checks that a distinctive fragment of the
stored article text still appears there. A mismatch means the store (and hence
the corpus) has drifted from the law in force — rerun the incremental update.

Usage:
    python scripts/drift_check.py [--samples 10] [--seed N] [--out FILE]

Exit code 1 when any sampled article no longer matches the live source.
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
STORE = PROJECT_DIR / "data" / "georgian_laws" / "article_store.db"
UA = {"User-Agent": "Mozilla/5.0 (law-corpus drift check)"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _page_text(url: str) -> str:
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=60
    ) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return _normalize(html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def _fragment(content: str, length: int = 80) -> str:
    """A distinctive fragment from the middle of the article text."""
    normalized = _normalize(content)
    if len(normalized) <= length:
        return normalized
    start = (len(normalized) - length) // 2
    return normalized[start : start + length]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=int, default=10)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    conn = sqlite3.connect(f"file:{STORE}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT article_id, code_name, article_number, content_ka, article_url "
        "FROM articles WHERE is_repealed = 0 AND LENGTH(content_ka) > 200"
    ).fetchall()
    sample = rng.sample(rows, min(args.samples, len(rows)))

    pages: dict[str, str] = {}
    results = []
    for row in sample:
        doc_url = row["article_url"].split("#")[0]
        if doc_url not in pages:
            try:
                pages[doc_url] = _page_text(doc_url)
            except Exception as e:
                pages[doc_url] = ""
                print(f"  ⚠ fetch failed {doc_url}: {e}")
        fragment = _fragment(row["content_ka"])
        matched = bool(pages[doc_url]) and fragment in pages[doc_url]
        results.append({
            "article_id": row["article_id"],
            "code_name": row["code_name"],
            "article_number": row["article_number"],
            "article_url": row["article_url"],
            "fetched": bool(pages[doc_url]),
            "matched": matched,
        })
        print(f"  {'✓' if matched else '✗'} {row['article_id']}")

    drifted = [r for r in results if r["fetched"] and not r["matched"]]
    unfetched = [r for r in results if not r["fetched"]]
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "samples": len(results),
        "matched": sum(1 for r in results if r["matched"]),
        "drifted": drifted,
        "unfetched": unfetched,
    }
    out = args.out or (
        PROJECT_DIR / "data" / "georgian_laws" / "drift_report.json"
    )
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"\n{report['matched']}/{report['samples']} matched; "
        f"{len(drifted)} drifted; {len(unfetched)} unfetched → {out}"
    )
    sys.exit(1 if drifted else 0)


if __name__ == "__main__":
    main()
