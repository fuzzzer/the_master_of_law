#!/usr/bin/env python3
"""
Build ChromaDB collections for court practice and Grand Chamber decisions.

Reads extracted .txt case files from processed_v2/, chunks them with proper
metadata, embeds using gemini-embedding-001 (768-dim, RETRIEVAL_DOCUMENT),
and stores in ChromaDB collections alongside the existing "georgian_laws".

Collections created:
  - "court_practice"  — Supreme Court case rulings (2022-2026)
  - "grand_chamber"   — Grand Chamber binding decisions and norm interpretations

Usage:
  # Build both collections
  python3 build_court_embeddings.py

  # Build only one
  python3 build_court_embeddings.py --collection court_practice
  python3 build_court_embeddings.py --collection grand_chamber

  # Dry run (chunk + stats, no embedding/indexing)
  python3 build_court_embeddings.py --dry-run

  # Re-embed (clear existing and rebuild)
  python3 build_court_embeddings.py --rebuild
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR.parent.parent / "law_corpus" / "data" / "chroma"

# Embedding config — MUST match existing law corpus
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768
EMBEDDING_TASK_TYPE = "RETRIEVAL_DOCUMENT"
EMBEDDING_BATCH_SIZE = 50
EMBEDDING_DELAY = 5.0  # seconds between batches (rate limiting)


# ─────────────────────────────────────────────
# Chunk data model
# ─────────────────────────────────────────────

@dataclass
class CourtChunk:
    """A single chunk of court decision text with metadata."""
    chunk_id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


# ─────────────────────────────────────────────
# Text chunking
# ─────────────────────────────────────────────

# Court decision section markers
SECTION_PATTERNS = {
    "descriptive": re.compile(
        r'აღწერილობითი\s+ნაწილი|აღწერილობითი|ა\s*ღ\s*წ\s*ე\s*რ\s*ი\s*ლ\s*ო\s*ბ\s*ი\s*თ\s*ი',
        re.IGNORECASE,
    ),
    "reasoning": re.compile(
        r'სამოტივაციო\s+ნაწილი|სამოტივაციო|მ\s*ო\s*ტ\s*ი\s*ვ\s*ა\s*ც\s*ი',
        re.IGNORECASE,
    ),
    "resolution": re.compile(
        r'სარეზოლუციო\s+ნაწილი|სარეზოლუციო|რ\s*ე\s*ზ\s*ო\s*ლ\s*უ\s*ც\s*ი',
        re.IGNORECASE,
    ),
}

# Pattern for numbered sections within a court decision
NUMBERED_SECTION = re.compile(r'^\s*(\d+)\.\s+', re.MULTILINE)


def detect_section(text: str) -> str:
    """Detect which section of a court decision this text belongs to."""
    for section, pattern in SECTION_PATTERNS.items():
        if pattern.search(text[:500]):
            return section
    return "general"


def extract_case_id_from_filename(filename: str) -> str:
    """Extract case ID from filename (e.g., 'case_1.txt' -> 'case_1')."""
    return Path(filename).stem


def detect_year_from_text(text: str) -> int | None:
    """Try to extract the year from case text."""
    # Look for year patterns like "2024 წ." or "2024 წელი" or just "20XX"
    year_match = re.search(r'20(2[0-6]|1\d|0\d)\s*(წ\.|წელი|წლის)', text[:2000])
    if year_match:
        return int("20" + year_match.group(1))
    # Fallback: look for any 4-digit year in first 2000 chars
    year_match = re.search(r'\b(20[012]\d)\b', text[:2000])
    if year_match:
        return int(year_match.group(1))
    return None


def detect_category_from_path(file_path: Path) -> str:
    """Detect case category from file path."""
    path_str = str(file_path).lower()
    if "criminal" in path_str or "sisxli" in path_str:
        return "criminal"
    elif "civil" in path_str or "samoq" in path_str:
        return "civil"
    elif "admin" in path_str:
        return "administrative"
    return "unknown"


def chunk_text(
    text: str,
    target_words: int = 750,
    max_words: int = 1000,
    overlap_words: int = 50,
) -> list[str]:
    """
    Split text into chunks of target_words, with overlap.

    Tries to split at numbered sections (1., 2., 3.) or paragraph boundaries.
    Falls back to word-count-based splitting.
    """
    if not text.strip():
        return []

    words = text.split()
    total_words = len(words)

    if total_words <= max_words:
        return [text.strip()]

    chunks = []
    start = 0

    while start < total_words:
        end = min(start + max_words, total_words)

        # Try to find a good split point (numbered section or double newline)
        if end < total_words:
            # Look backwards from end for a paragraph boundary
            chunk_text_candidate = " ".join(words[start:end])
            # Find last numbered section start within the chunk
            numbered_matches = list(NUMBERED_SECTION.finditer(chunk_text_candidate))
            if numbered_matches and len(numbered_matches) > 1:
                # Split at the last numbered section (if not too short)
                last_match = numbered_matches[-1]
                split_pos = len(chunk_text_candidate[:last_match.start()].split())
                if split_pos >= target_words // 2:
                    end = start + split_pos

        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())

        # Move start with overlap
        start = end - overlap_words if end < total_words else total_words

    return chunks


def extract_norm_interpretation(text: str) -> dict[str, str]:
    """
    For Grand Chamber norm interpretation documents, extract:
    - norm_interpreted: which legal norm was interpreted
    - binding_rule: the established binding interpretation

    Returns empty dict if not a norm interpretation doc.
    """
    result = {}

    # Look for norm references (e.g., "სსკ 19", "სპკ 259")
    norm_match = re.search(
        r'(სსკ|სამოქალაქო\s+კოდექსის?|სპკ|ადმინისტრაციული)\s+(\d+)',
        text[:1000],
    )
    if norm_match:
        result["norm_interpreted"] = norm_match.group(0)

    # Look for interpretation rules (sentences with "დადგენილია" or "განმარტება")
    rule_match = re.search(
        r'(დადგენილია|განმარტება|სავალდებულო\s+ინტერპრეტაცია)[^.]*\.',
        text[:3000],
    )
    if rule_match:
        result["binding_rule"] = rule_match.group(0)[:200]

    return result


def chunk_case_file(
    file_path: Path,
    source: str,  # "court_practice" or "grand_chamber"
    court: str,    # "supreme_court" or "grand_chamber"
) -> list[CourtChunk]:
    """
    Read a case file and produce chunks with metadata.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠️  Cannot read {file_path}: {e}")
        return []

    if not text.strip():
        return []

    case_id = extract_case_id_from_filename(file_path.name)
    category = detect_category_from_path(file_path)
    year = detect_year_from_text(text)
    section = detect_section(text)

    # For Grand Chamber norm interpretations, extract extra metadata
    norm_data = {}
    if source == "grand_chamber":
        norm_data = extract_norm_interpretation(text)

    # Chunk the text
    text_chunks = chunk_text(text)

    chunks = []
    for idx, chunk_content in enumerate(text_chunks):
        # Build unique chunk ID
        content_hash = hashlib.md5(chunk_content.encode("utf-8")).hexdigest()[:8]
        chunk_id = f"{source}:{case_id}:chunk_{idx}:{content_hash}"

        metadata = {
            "source": source,
            "case_id": case_id,
            "category": category,
            "section": section if idx == 0 else detect_section(chunk_content),
            "court": court,
            "chunk_index": idx,
            "total_chunks": len(text_chunks),
            "source_file": file_path.name,
        }
        if year:
            metadata["year"] = year

        # Add norm interpretation data for Grand Chamber
        if norm_data:
            metadata.update(norm_data)

        chunks.append(CourtChunk(
            chunk_id=chunk_id,
            content=chunk_content,
            metadata=metadata,
        ))

    return chunks


# ─────────────────────────────────────────────
# Embedding
# ─────────────────────────────────────────────

def get_embedding_client():
    """Create a Gemini embedding client using google-genai SDK."""
    from google import genai
    from google.genai.types import EmbedContentConfig

    api_key = os.environ.get("GOOGLE_API_KEY", "")

    if api_key:
        print("  🔑 Using Google AI API key auth for embeddings")
        client = genai.Client(api_key=api_key)
    else:
        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0225498420")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        print(f"  🔑 Using Vertex AI ADC auth (project={project}, location={location})")
        client = genai.Client(vertexai=True, project=project, location=location)

    return client


def embed_batch(client, texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using gemini-embedding-001."""
    from google.genai.types import EmbedContentConfig

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=EmbedContentConfig(
            task_type=EMBEDDING_TASK_TYPE,
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )
    return [list(e.values) for e in result.embeddings]


def embed_all_chunks(
    chunks: list[CourtChunk],
    batch_size: int = EMBEDDING_BATCH_SIZE,
    delay: float = EMBEDDING_DELAY,
) -> list[CourtChunk]:
    """Embed all chunks in batches with rate limiting."""
    if not chunks:
        return chunks

    client = get_embedding_client()
    total = len(chunks)
    batches = [chunks[i:i + batch_size] for i in range(0, total, batch_size)]
    total_batches = len(batches)

    print(f"\n  📦 Embedding {total} chunks in {total_batches} batches (size={batch_size})")
    start_time = time.monotonic()
    embedded = 0
    failed = 0

    for batch_idx, batch in enumerate(batches):
        texts = [c.content for c in batch]

        for attempt in range(3):
            try:
                embeddings = embed_batch(client, texts)
                for chunk, emb in zip(batch, embeddings):
                    chunk.embedding = emb
                embedded += len(batch)
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"  ⚠️  Rate limited (batch {batch_idx+1}/{total_batches}), waiting 60s...")
                    time.sleep(60)
                elif attempt < 2:
                    print(f"  ⚠️  Error (attempt {attempt+1}/3): {error_str[:100]}")
                    time.sleep(delay * 2)
                else:
                    print(f"  ❌ Failed batch {batch_idx+1}: {error_str[:100]}")
                    failed += len(batch)

        if (batch_idx + 1) % 10 == 0 or batch_idx == total_batches - 1:
            elapsed = time.monotonic() - start_time
            rate = embedded / elapsed if elapsed > 0 else 0
            print(f"  📊 Progress: {batch_idx+1}/{total_batches} batches, {embedded} embedded ({rate:.1f}/s), {failed} failed")

        time.sleep(delay)

    elapsed = time.monotonic() - start_time
    print(f"  ✅ Embedding complete: {embedded} embedded, {failed} failed in {elapsed:.1f}s")

    return chunks


# ─────────────────────────────────────────────
# ChromaDB indexing
# ─────────────────────────────────────────────

def index_to_chroma(
    chunks: list[CourtChunk],
    collection_name: str,
    collection_description: str,
    rebuild: bool = False,
) -> int:
    """Store embedded chunks in a ChromaDB collection."""
    import chromadb

    print(f"\n  📁 Indexing to ChromaDB collection: {collection_name}")
    print(f"     Path: {CHROMA_DIR}")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if rebuild:
        try:
            client.delete_collection(collection_name)
            print(f"  🗑️  Deleted existing collection: {collection_name}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": collection_description},
    )

    existing_count = collection.count()
    print(f"  📊 Existing documents: {existing_count}")

    # Filter chunks that have embeddings
    valid_chunks = [c for c in chunks if c.embedding is not None]
    if not valid_chunks:
        print("  ⚠️  No chunks with embeddings to index")
        return 0

    # Batch add to ChromaDB (max 5000 per call)
    CHROMA_BATCH = 5000
    added = 0
    for i in range(0, len(valid_chunks), CHROMA_BATCH):
        batch = valid_chunks[i:i + CHROMA_BATCH]
        collection.add(
            ids=[c.chunk_id for c in batch],
            embeddings=[c.embedding for c in batch],
            documents=[c.content for c in batch],
            metadatas=[c.metadata for c in batch],
        )
        added += len(batch)

    final_count = collection.count()
    print(f"  ✅ Indexed {added} chunks. Total in collection: {final_count}")
    return added


# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────

def find_case_files(source_type: str) -> list[Path]:
    """Find all extracted case .txt files for a given source type."""
    if source_type == "court_practice":
        # All Supreme Court cases (criminal, civil, administrative)
        base = BASE_DIR / "extracted" / "supreme_court"
        files = []
        for category in ("criminal", "civil", "administrative"):
            cat_dir = base / category
            if cat_dir.exists():
                files.extend(sorted(cat_dir.glob("*.txt")))
        return files

    elif source_type == "grand_chamber":
        # Grand Chamber cases — sibling to supreme_court
        base = BASE_DIR / "extracted" / "grand_chamber"
        if base.exists():
            return sorted(base.rglob("*.txt"))
        return []

    return []


def build_collection(
    source_type: str,
    collection_name: str,
    collection_description: str,
    dry_run: bool = False,
    rebuild: bool = False,
) -> dict[str, Any]:
    """Build a complete ChromaDB collection from extracted case files."""
    print(f"\n{'='*60}")
    print(f"🏛️  Building collection: {collection_name}")
    print(f"{'='*60}")

    # Find source files
    files = find_case_files(source_type)
    print(f"  📄 Found {len(files)} case files")

    if not files:
        print("  ⚠️  No files found — skipping")
        return {"files": 0, "chunks": 0, "indexed": 0}

    # Chunk all files
    court = "grand_chamber" if source_type == "grand_chamber" else "supreme_court"
    all_chunks: list[CourtChunk] = []

    for f in files:
        chunks = chunk_case_file(f, source=source_type, court=court)
        all_chunks.extend(chunks)

    print(f"  📦 Total chunks: {len(all_chunks)}")

    # Show chunk distribution
    categories = {}
    for c in all_chunks:
        cat = c.metadata.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"     {cat}: {count} chunks")

    if dry_run:
        print("\n  🔍 DRY RUN — not embedding or indexing")
        # Show sample chunks
        if all_chunks:
            sample = all_chunks[0]
            print(f"\n  Sample chunk:")
            print(f"    ID: {sample.chunk_id}")
            print(f"    Metadata: {json.dumps(sample.metadata, ensure_ascii=False, indent=2)}")
            print(f"    Content preview: {sample.content[:200]}...")
        return {"files": len(files), "chunks": len(all_chunks), "indexed": 0}

    # Embed
    all_chunks = embed_all_chunks(all_chunks)

    # Index to ChromaDB
    indexed = index_to_chroma(
        all_chunks,
        collection_name=collection_name,
        collection_description=collection_description,
        rebuild=rebuild,
    )

    return {"files": len(files), "chunks": len(all_chunks), "indexed": indexed}


def main():
    parser = argparse.ArgumentParser(
        description="Build ChromaDB collections for court practice and Grand Chamber"
    )
    parser.add_argument(
        "--collection",
        choices=["court_practice", "grand_chamber", "all"],
        default="all",
        help="Which collection to build (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Chunk only, no embedding/indexing")
    parser.add_argument("--rebuild", action="store_true", help="Delete existing collection and rebuild")
    args = parser.parse_args()

    print("=" * 60)
    print("🏛️  Court Practice & Grand Chamber Embedding Pipeline")
    print("=" * 60)
    print(f"ChromaDB: {CHROMA_DIR}")
    print(f"Model: {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS}d)")

    results = {}

    if args.collection in ("court_practice", "all"):
        results["court_practice"] = build_collection(
            source_type="court_practice",
            collection_name="court_practice",
            collection_description="Supreme Court case rulings 2022-2026",
            dry_run=args.dry_run,
            rebuild=args.rebuild,
        )

    if args.collection in ("grand_chamber", "all"):
        results["grand_chamber"] = build_collection(
            source_type="grand_chamber",
            collection_name="grand_chamber",
            collection_description="Grand Chamber binding decisions and norm interpretations",
            dry_run=args.dry_run,
            rebuild=args.rebuild,
        )

    # Final summary
    print(f"\n{'='*60}")
    print("📊 Final Summary")
    print("=" * 60)
    for name, stats in results.items():
        print(f"  {name}: {stats['files']} files → {stats['chunks']} chunks → {stats['indexed']} indexed")


if __name__ == "__main__":
    main()
