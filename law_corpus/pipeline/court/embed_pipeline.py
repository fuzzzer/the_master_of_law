"""
Court embedding pipeline — chunk, embed, and index court decisions.

Reads extracted .txt case files, chunks them with court-specific logic,
embeds using the same model as georgian_laws, and indexes into ChromaDB.

Usage:
    # From law_corpus/ directory:
    python -m pipeline.court.embed_pipeline --dry-run
    python -m pipeline.court.embed_pipeline
    python -m pipeline.court.embed_pipeline --collection court_practice
    python -m pipeline.court.embed_pipeline --rebuild
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure law_corpus/ is on the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.config import settings
from pipeline.court.chunker import CourtChunk, CourtChunker
from pipeline.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)

# ── Constants ────────────────────────────────────────────────

# Use the same model/dimensions as configured in settings (matches georgian_laws)
EMBEDDING_BATCH_SIZE = 50
EMBEDDING_DELAY = 5.0

DATA_DIR = settings.data_dir

# Module data directories
MODULE_PATHS = {
    "court_practice": {
        "data_dir": DATA_DIR / "court_practice" / "extracted",
        "source": "court_practice",
        "court": "supreme_court",
        "description": "Supreme Court case law (2022-2026)",
    },
    "grand_chamber": {
        "data_dir": DATA_DIR / "grand_chamber" / "extracted",
        "source": "grand_chamber",
        "court": "grand_chamber",
        "description": "Grand Chamber binding decisions",
    },
}


# ── Embedding (reuses existing VertexEmbedder — same auth as georgian_laws) ──

def get_embedder():
    """
    Create the shared embedder — same as georgian_laws pipeline.

    Auth: uses Vertex AI ADC (gcloud auth application-default login).
    No API key needed.
    """
    from pipeline.embedder.vertex_embedder import VertexEmbedder
    return VertexEmbedder()


def embed_batch(embedder, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the shared embedder."""
    return embedder.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")


def embed_all_chunks(
    chunks: list[CourtChunk],
    batch_size: int = EMBEDDING_BATCH_SIZE,
    delay: float = EMBEDDING_DELAY,
) -> list[CourtChunk]:
    """Embed all chunks in batches with rate limiting."""
    if not chunks:
        return chunks

    embedder = get_embedder()
    total = len(chunks)
    batches = [chunks[i:i + batch_size] for i in range(0, total, batch_size)]
    total_batches = len(batches)

    print(f"  📦 Embedding {total} chunks in {total_batches} batches (size={batch_size})")
    print(f"     Model: {settings.embedding_model} ({settings.embedding_dimensions}d)")
    print(f"     Auth: Vertex AI ADC (project={settings.google_cloud_project})")
    start_time = time.monotonic()
    embedded = 0
    failed = 0

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
                    print(f"  ⚠️  Rate limited (batch {batch_idx+1}/{total_batches}), waiting {wait}s...")
                    time.sleep(wait)
                elif attempt < 2:
                    print(f"  ⚠️  Error (attempt {attempt+1}/3): {error_str[:100]}")
                    time.sleep(delay * 2)
                else:
                    print(f"  ❌ Failed batch {batch_idx+1}: {error_str[:100]}")
                    failed += len(batch)

        if (batch_idx + 1) % 10 == 0 or batch_idx == total_batches - 1:
            elapsed = time.monotonic() - start_time
            rate = embedded / elapsed if elapsed > 0 else 0
            print(
                f"  📊 Progress: {batch_idx+1}/{total_batches} batches, "
                f"{embedded} embedded ({rate:.1f}/s), {failed} failed"
            )

        time.sleep(delay)

    elapsed = time.monotonic() - start_time
    print(f"  ✅ Embedding complete: {embedded}/{total} in {elapsed:.1f}s")

    return chunks


# ── ChromaDB indexing ────────────────────────────────────────

def index_to_chroma(
    chunks: list[CourtChunk],
    collection_name: str,
    description: str,
    rebuild: bool = False,
) -> int:
    """Store embedded chunks in a ChromaDB collection."""
    import chromadb

    chroma_dir = settings.chroma_persist_dir
    print(f"\n  📁 Indexing to ChromaDB collection: {collection_name}")
    print(f"     Path: {chroma_dir}")

    client = chromadb.PersistentClient(path=str(chroma_dir))

    if rebuild:
        try:
            client.delete_collection(collection_name)
            print(f"  🗑️  Deleted existing collection: {collection_name}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": description},
    )

    existing = collection.count()
    print(f"  📊 Existing documents: {existing}")

    valid = [c for c in chunks if c.embedding is not None]
    if not valid:
        print("  ⚠️  No chunks with embeddings to index")
        return 0

    CHROMA_BATCH = 5000
    added = 0
    for i in range(0, len(valid), CHROMA_BATCH):
        batch = valid[i:i + CHROMA_BATCH]
        collection.add(
            ids=[c.chunk_id for c in batch],
            embeddings=[c.embedding for c in batch],
            documents=[c.content for c in batch],
            metadatas=[c.metadata for c in batch],
        )
        added += len(batch)

    final = collection.count()
    print(f"  ✅ Indexed {added} chunks. Total in collection: {final}")
    return added


# ── Pipeline orchestrator ────────────────────────────────────

def run_pipeline(
    collection_name: str,
    dry_run: bool = False,
    rebuild: bool = False,
) -> dict:
    """Run the full pipeline for a single collection."""
    if collection_name not in MODULE_PATHS:
        print(f"  ❌ Unknown collection: {collection_name}")
        return {}

    config = MODULE_PATHS[collection_name]
    data_dir = config["data_dir"]

    print(f"\n{'='*60}")
    print(f"🏛️  Building collection: {collection_name}")
    print(f"{'='*60}")
    print(f"  📂 Data: {data_dir}")

    if not data_dir.exists():
        print(f"  ❌ Data directory not found: {data_dir}")
        print(f"     Copy extracted .txt files here first.")
        return {"files": 0, "chunks": 0, "indexed": 0}

    # 1. Chunk
    chunker = CourtChunker(data_dir=data_dir)
    files = chunker.find_files()
    print(f"  📄 Found {len(files)} case files")

    chunks = chunker.chunk_all(
        source=config["source"],
        court=config["court"],
    )
    print(f"  📦 Total chunks: {len(chunks)}")

    # Show distribution
    categories: dict[str, int] = {}
    for c in chunks:
        cat = c.metadata.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"     {cat}: {count} chunks")

    if dry_run:
        print("\n  🔍 DRY RUN — not embedding or indexing")
        if chunks:
            sample = chunks[0]
            print(f"\n  Sample chunk:")
            print(f"    ID: {sample.chunk_id}")
            print(f"    Metadata: {json.dumps(sample.metadata, ensure_ascii=False, indent=2)}")
            print(f"    Content preview: {sample.content[:200]}...")
        return {"files": len(files), "chunks": len(chunks), "indexed": 0}

    # 2. Embed
    chunks = embed_all_chunks(chunks)

    # 3. Index
    indexed = index_to_chroma(
        chunks=chunks,
        collection_name=collection_name,
        description=config["description"],
        rebuild=rebuild,
    )

    return {"files": len(files), "chunks": len(chunks), "indexed": indexed}


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Court Embedding Pipeline — chunk, embed, index court decisions",
    )
    parser.add_argument(
        "--collection", type=str,
        choices=list(MODULE_PATHS.keys()),
        help="Build a specific collection (default: all)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Chunk and show stats without embedding",
    )
    parser.add_argument(
        "--rebuild", action="store_true",
        help="Delete existing collection and rebuild from scratch",
    )
    args = parser.parse_args()

    setup_logging("INFO")

    print("=" * 60)
    print("🏛️  Court Practice & Grand Chamber Embedding Pipeline")
    print("=" * 60)
    print(f"ChromaDB: {settings.chroma_persist_dir}")
    print(f"Model: {settings.embedding_model} ({settings.embedding_dimensions}d)")
    print(f"Auth: Vertex AI ADC (gcloud auth application-default login)")

    collections = [args.collection] if args.collection else list(MODULE_PATHS.keys())
    results = {}

    for name in collections:
        result = run_pipeline(
            collection_name=name,
            dry_run=args.dry_run,
            rebuild=args.rebuild,
        )
        results[name] = result

    # Summary
    print(f"\n{'='*60}")
    print("📊 Final Summary")
    print("=" * 60)
    for name, r in results.items():
        print(f"  {name}: {r.get('files', 0)} files → {r.get('chunks', 0)} chunks → {r.get('indexed', 0)} indexed")


if __name__ == "__main__":
    main()
