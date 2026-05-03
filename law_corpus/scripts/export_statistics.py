#!/usr/bin/env python3
"""Generate and display corpus statistics."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.config import settings


def main() -> None:
    print("═══════════════════════════════════════════════")
    print("  Georgian Law Corpus — Statistics Report")
    print("═══════════════════════════════════════════════")

    # Raw documents
    raw_count = 0
    if settings.raw_html_dir.exists():
        raw_count = len(list(settings.raw_html_dir.glob("*.html")))
    print(f"\n  Raw HTML documents:  {raw_count}")

    # Parsed documents
    parsed_count = 0
    total_articles = 0
    docs_by_type: dict[str, int] = {}
    if settings.parsed_dir.exists():
        for f in settings.parsed_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text("utf-8"))
                parsed_count += 1
                articles = data.get("articles", [])
                total_articles += len(articles)
                dtype = data.get("metadata", {}).get("document_type", "unknown")
                docs_by_type[dtype] = docs_by_type.get(dtype, 0) + 1
            except Exception:
                pass

    print(f"  Parsed documents:    {parsed_count}")
    print(f"  Total articles:      {total_articles}")

    if docs_by_type:
        print(f"\n  By document type:")
        for dtype, count in sorted(docs_by_type.items()):
            print(f"    {dtype}: {count}")

    # Chunks
    total_chunks = 0
    total_tokens = 0
    if settings.chunks_dir.exists():
        import orjson
        for f in settings.chunks_dir.glob("*.json"):
            try:
                chunks = orjson.loads(f.read_bytes())
                total_chunks += len(chunks)
                total_tokens += sum(c.get("token_count", 0) for c in chunks)
            except Exception:
                pass

    print(f"\n  Total chunks:        {total_chunks}")
    print(f"  Total tokens:        {total_tokens:,}")

    # Embedding cache
    cache_index = settings.embeddings_dir / "_cache_index.json"
    emb_count = 0
    if cache_index.exists():
        try:
            emb_count = len(json.loads(cache_index.read_text("utf-8")))
        except Exception:
            pass
    print(f"  Cached embeddings:   {emb_count}")

    # Checkpoint status
    if settings.checkpoint_dir.exists():
        print(f"\n  Checkpoints:")
        for cp in settings.checkpoint_dir.glob("*_checkpoint.json"):
            try:
                data = json.loads(cp.read_text("utf-8"))
                stage = data.get("stage", cp.stem)
                completed = data.get("completed_count", 0)
                failed = len(data.get("failed_items", []))
                print(f"    {stage}: {completed} completed, {failed} failed")
            except Exception:
                pass

    print("\n═══════════════════════════════════════════════")


if __name__ == "__main__":
    main()
