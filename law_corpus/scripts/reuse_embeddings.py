#!/usr/bin/env python3
"""
Carry existing embeddings over to rebuilt chunks whose text did not change.

A rebuild that only changes a chunk's ids or its "წყარო:" link line (e.g.
"#article_48" → matsne's real "#part_174") changes its content hash, so the
embedder would re-embed it — 15k texts, while a free key allows 1,000 a day.
The link line carries no legal meaning, so a chunk whose text without that
line equals an old chunk's reuses the old vector. Only chunks whose wording
really changed are left for the embedder.

Usage:
    python -m scripts.reuse_embeddings --old-root data --new-root data_v2_superscripts
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pipeline.embedder.embedding_cache import EmbeddingCache

SOURCE_LINE = re.compile(r"\nწყარო: \S+")


def _text_without_link(content: str) -> str:
    return SOURCE_LINE.sub("", content)


def _chunks(root: Path):
    for path in sorted((root / "georgian_laws" / "chunks").glob("*.json")):
        yield from json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-root", type=Path, required=True)
    ap.add_argument("--new-root", type=Path, required=True)
    args = ap.parse_args()

    old_cache = EmbeddingCache(args.old_root / "georgian_laws" / "embeddings")
    new_cache = EmbeddingCache(args.new_root / "georgian_laws" / "embeddings")
    old_by_text = {
        _text_without_link(c["content"]): (c["chunk_id"], c["content_hash"])
        for c in _chunks(args.old_root)
    }

    reused = already = left = 0
    for c in _chunks(args.new_root):
        if new_cache.get(c["chunk_id"], c["content_hash"]) is not None:
            already += 1
            continue
        old = old_by_text.get(_text_without_link(c["content"]))
        vector = old_cache.get(*old) if old else None
        if vector is None:
            left += 1
            continue
        new_cache.put(c["chunk_id"], c["content_hash"], vector)
        reused += 1
    new_cache.flush()
    print(f"reused {reused}, already embedded {already}, left to embed {left}")


if __name__ == "__main__":
    main()
