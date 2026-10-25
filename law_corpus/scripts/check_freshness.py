#!/usr/bin/env python3
"""
List laws whose consolidated version on matsne.gov.ge is newer than the store's.

For each code in the article store, reads only the top of its matsne page (the
version selector sits above the law text) and compares matsne's current
publication number and date with the stored ones. Also flags an act matsne
marks as no longer in force. Polite: honours robots.txt and its Crawl-delay
(never under 10 s), one honest user agent, nothing written to matsne.

Meant for a nightly job later; it schedules nothing itself. Exit code 0 when
everything is current, 2 when at least one law changed or lost force.

Usage:
    python scripts/check_freshness.py --store data/georgian_laws/article_store.db [--json changed.json]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path
from urllib.robotparser import RobotFileParser

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from pipeline.config import settings  # noqa: E402
from pipeline.scraper.matsne_scraper import BASE_URL, MatsneScraper  # noqa: E402

MIN_DELAY_SECONDS = 10.0
# The version selector precedes the law text; a lost-force notice opens it.
_DOCUMENT_START = b'id="maindoc"'
_READ_PAST_START = 4_000
_MAX_BYTES = 1_500_000


def _fetch_head(url: str) -> str:
    """The start of a page: its header and the first lines of the law text."""
    request = urllib.request.Request(url, headers={"User-Agent": settings.scrape_user_agent})
    data = b""
    with urllib.request.urlopen(request, timeout=60) as response:
        while len(data) < _MAX_BYTES:
            start = data.find(_DOCUMENT_START)
            if start >= 0 and len(data) - start > _READ_PAST_START:
                break
            chunk = response.read(32_768)
            if not chunk:
                break
            data += chunk
    return data.decode("utf-8", errors="replace")


def check(store: Path) -> list[dict]:
    conn = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    codes = conn.execute(
        "SELECT document_id, code_name, source_url, publication_id, version_date FROM codes ORDER BY document_id"
    ).fetchall()
    conn.close()

    robots = RobotFileParser(f"{BASE_URL}/robots.txt")
    robots.read()
    delay = max(MIN_DELAY_SECONDS, float(robots.crawl_delay(settings.scrape_user_agent) or 0))

    results = []
    for i, code in enumerate(codes):
        url = code["source_url"]
        if not robots.can_fetch(settings.scrape_user_agent, url):
            results.append({"document_id": code["document_id"], "status": "skipped: robots.txt disallows"})
            continue
        if i:
            time.sleep(delay)
        try:
            info = MatsneScraper.extract_version_info(_fetch_head(url))
        except Exception as exc:  # network errors are reported, not fatal
            results.append({"document_id": code["document_id"], "status": f"error: {exc}"})
            continue
        changed = info["publication_id"] != code["publication_id"]
        status = "lost force" if info["lost_force_notice"] else ("changed" if changed else "current")
        results.append({
            "document_id": code["document_id"],
            "code_name": code["code_name"],
            "url": url,
            "status": status,
            "stored_publication": code["publication_id"],
            "stored_version_date": code["version_date"],
            "matsne_publication": info["publication_id"],
            "matsne_version_date": info["version_date"],
            "lost_force_notice": info["lost_force_notice"],
            "replaced_by_matsne_id": info["replaced_by_matsne_id"],
        })
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", type=Path, required=True)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    results = check(args.store)
    if args.json:
        args.json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in results:
        line = f"  {r['document_id']:26} {r['status']}"
        if r.get("matsne_version_date"):
            line += f" (stored {r['stored_version_date']}, matsne {r['matsne_version_date']})"
        print(line)
    stale = [r for r in results if r["status"] in ("changed", "lost force")]
    print(f"{len(stale)} of {len(results)} laws need a refresh")
    sys.exit(2 if stale else 0)


if __name__ == "__main__":
    main()
