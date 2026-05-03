#!/usr/bin/env python3
"""Validate corpus completeness and quality."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.config import settings
from pipeline.scraper.matsne_scraper import SEED_LAWS


def main() -> int:
    issues: list[str] = []
    total_articles = 0
    total_chunks = 0

    # Check each priority level
    for priority in ("P0", "P1", "P2"):
        laws = [l for l in SEED_LAWS if l["priority"] == priority]
        found = 0
        for law in laws:
            parsed = settings.parsed_dir / f"{law['document_id']}.json"
            if parsed.exists():
                found += 1
            else:
                issues.append(f"[{priority}] Missing parsed: {law['document_id']}")

        print(f"  {priority}: {found}/{len(laws)} laws parsed")

    # Count total articles and chunks
    if settings.parsed_dir.exists():
        import json
        for f in sorted(settings.parsed_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text("utf-8"))
                article_count = len(data.get("articles", []))
                total_articles += article_count
            except Exception:
                issues.append(f"  Cannot read: {f.name}")

    if settings.chunks_dir.exists():
        import orjson
        for f in sorted(settings.chunks_dir.glob("*.json")):
            try:
                data = orjson.loads(f.read_bytes())
                total_chunks += len(data)
            except Exception:
                issues.append(f"  Cannot read chunks: {f.name}")

    print(f"\n  Total articles: {total_articles}")
    print(f"  Total chunks: {total_chunks}")

    if issues:
        print(f"\n⚠ {len(issues)} issues found:")
        for issue in issues:
            print(f"  {issue}")
        return 1

    print("\n✓ Corpus validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
