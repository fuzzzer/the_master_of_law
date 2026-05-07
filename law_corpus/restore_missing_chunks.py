#!/usr/bin/env python3
"""
Targeted restore — re-embed ONLY the 517 missing chunks.

Instead of rebuilding all 5,197 chunks (~104 batches, ~1 hour),
this script:
1. Re-chunks all files (instant, no API calls)
2. Gets existing chunk IDs from ChromaDB
3. Finds the delta (missing chunks)
4. Embeds ONLY the missing ones (~11 batches, ~5-10 min)
5. Adds them to ChromaDB

Usage:
    cd law_corpus
    python restore_missing_chunks.py --dry-run   # see what's missing
    python restore_missing_chunks.py              # re-embed & restore
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure law_corpus/ is on the path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.config import settings
from pipeline.court.chunker import CourtChunker
from pipeline.court.embed_pipeline import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DELAY,
    embed_batch,
    get_embedder,
)
from pipeline.utils.logger import setup_logging


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Restore only missing chunks")
    parser.add_argument("--dry-run", action="store_true", help="Show what's missing without embedding")
    parser.add_argument("--batch-size", type=int, default=EMBEDDING_BATCH_SIZE, help="Embedding batch size")
    parser.add_argument("--delay", type=float, default=EMBEDDING_DELAY, help="Delay between batches")
    args = parser.parse_args()

    setup_logging("INFO")

    import chromadb

    print("=" * 60)
    print("🔧 Targeted Chunk Restore — court_practice")
    print("=" * 60)

    # 1. Re-chunk all files (instant)
    data_dir = settings.data_dir / "court_practice" / "extracted"
    print(f"\n📂 Data: {data_dir}")

    chunker = CourtChunker(data_dir=data_dir)
    files = chunker.find_files()
    print(f"📄 Found {len(files)} case files")

    all_chunks = chunker.chunk_all(source="court_practice", court="supreme_court")
    print(f"📦 Total expected chunks: {len(all_chunks)}")

    # Build lookup by chunk_id
    chunk_map = {c.chunk_id: c for c in all_chunks}

    # 2. Get existing IDs from ChromaDB
    chroma_dir = settings.chroma_persist_dir
    client = chromadb.PersistentClient(path=str(chroma_dir))
    coll = client.get_collection("court_practice")
    existing_count = coll.count()
    print(f"📊 Existing in ChromaDB: {existing_count}")

    # Get ALL existing IDs (paginated)
    existing_ids = set()
    offset = 0
    batch_size = 5000
    while True:
        result = coll.get(limit=batch_size, offset=offset, include=[])
        if not result["ids"]:
            break
        existing_ids.update(result["ids"])
        offset += len(result["ids"])

    print(f"📊 Retrieved {len(existing_ids)} existing IDs")

    # 3. Find missing chunks
    expected_ids = set(chunk_map.keys())
    missing_ids = expected_ids - existing_ids
    extra_ids = existing_ids - expected_ids

    print(f"\n{'=' * 60}")
    print(f"📊 Delta Analysis")
    print(f"{'=' * 60}")
    print(f"  Expected: {len(expected_ids)}")
    print(f"  Existing: {len(existing_ids)}")
    print(f"  Missing:  {len(missing_ids)}")
    print(f"  Extra:    {len(extra_ids)}")

    if not missing_ids:
        print("\n✅ No missing chunks! Collection is complete.")
        return

    missing_chunks = [chunk_map[cid] for cid in missing_ids]

    # Show distribution
    categories: dict[str, int] = {}
    case_ids: set[str] = set()
    for c in missing_chunks:
        cat = c.metadata.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        case_ids.add(c.metadata.get("case_id", "unknown"))

    print(f"\n  Missing by category:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count} chunks")
    print(f"  From {len(case_ids)} cases")

    if args.dry_run:
        print("\n🔍 DRY RUN — not embedding. Run without --dry-run to restore.")
        # Show some sample case_ids
        for cid in sorted(case_ids)[:10]:
            matching = [c for c in missing_chunks if c.metadata.get("case_id") == cid]
            print(f"    {cid}: {len(matching)} chunks")
        if len(case_ids) > 10:
            print(f"    ... +{len(case_ids) - 10} more cases")
        return

    # 4. Embed only missing chunks
    batches_needed = (len(missing_chunks) + args.batch_size - 1) // args.batch_size
    print(f"\n📦 Embedding {len(missing_chunks)} missing chunks in {batches_needed} batches")
    print(f"   Model: {settings.embedding_model} ({settings.embedding_dimensions}d)")

    embedder = get_embedder()
    batches = [
        missing_chunks[i:i + args.batch_size]
        for i in range(0, len(missing_chunks), args.batch_size)
    ]

    embedded = 0
    failed = 0
    start_time = time.monotonic()

    for batch_idx, batch in enumerate(batches):
        texts = [c.content for c in batch]

        for attempt in range(3):
            try:
                embeddings = embed_batch(embedder, texts)
                for chunk, emb in zip(batch, embeddings):
                    chunk.embedding = emb
                embedded += len(batch)
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait = 60 * (attempt + 1)
                    print(f"  ⚠️  Rate limited (batch {batch_idx+1}/{batches_needed}), waiting {wait}s...")
                    time.sleep(wait)
                elif attempt < 2:
                    print(f"  ⚠️  Error (attempt {attempt+1}/3): {error_str[:100]}")
                    time.sleep(args.delay * 2)
                else:
                    print(f"  ❌ Failed batch {batch_idx+1}: {error_str[:100]}")
                    failed += len(batch)

        elapsed = time.monotonic() - start_time
        rate = embedded / elapsed if elapsed > 0 else 0
        print(
            f"  📊 Batch {batch_idx+1}/{batches_needed}: "
            f"{embedded} embedded ({rate:.1f}/s), {failed} failed"
        )

        if batch_idx < len(batches) - 1:
            time.sleep(args.delay)

    # 5. Add to ChromaDB
    valid = [c for c in missing_chunks if c.embedding is not None]
    if valid:
        CHROMA_BATCH = 5000
        added = 0
        for i in range(0, len(valid), CHROMA_BATCH):
            b = valid[i:i + CHROMA_BATCH]
            coll.add(
                ids=[c.chunk_id for c in b],
                embeddings=[c.embedding for c in b],
                documents=[c.content for c in b],
                metadatas=[c.metadata for c in b],
            )
            added += len(b)

        final = coll.count()
        elapsed = time.monotonic() - start_time
        print(f"\n{'=' * 60}")
        print(f"✅ Restored {added} chunks in {elapsed:.1f}s")
        print(f"   Collection: {existing_count} → {final} (expected: {len(expected_ids)})")
        if final == len(expected_ids):
            print(f"   🎉 Collection is now COMPLETE!")
        else:
            print(f"   ⚠️  Still missing {len(expected_ids) - final} chunks")
    else:
        print("\n❌ No chunks were successfully embedded")


if __name__ == "__main__":
    main()
