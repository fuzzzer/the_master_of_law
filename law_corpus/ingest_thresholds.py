"""
Threshold data ingestion into ChromaDB.

Reads structured legal thresholds from threshold_catalog.json,
generates embeddings, and adds them as enriched chunks in the
existing 'georgian_laws' collection with chunk_type='threshold'.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import chromadb
from chromadb.api.types import Embedding, Metadata


CATALOG_PATH = Path(__file__).parent / "data" / "thresholds" / "threshold_catalog.json"
CHROMA_PATH = Path(__file__).parent / "data" / "chroma"
COLLECTION_NAME = "georgian_laws"


def build_threshold_document(entry: dict) -> str:
    """Build a searchable text document from a threshold entry."""
    parts = [
        f"[იურიდიული ზღვარი / Legal Threshold]",
        f"კოდექსი: {_canonicalize_code_name(entry['code_name'])}",
        f"მუხლი: {entry['article_number']}",
        f"აღწერა: {entry['description_ka']}",
    ]
    if entry.get("substance"):
        parts.append(f"ნივთიერება: {entry['substance']}")

    parts.append("ზღვრები:")
    for key, value in entry["values"].items():
        parts.append(f"  • {key}: {value}")

    parts.append(f"შედეგი: {entry['consequence_ka']}")
    parts.append(f"წყარო: {entry['source_url']}")
    return "\n".join(parts)


# Short-form → full canonical code name mapping.
# Narcotics law and personal data law don't have the საქართველოს prefix.
_CODE_NAME_CANONICAL: dict[str, str] = {
    "სისხლის სამართლის კოდექსი": "საქართველოს სისხლის სამართლის კოდექსი",
    "სამოქალაქო კოდექსი": "საქართველოს სამოქალაქო კოდექსი",
    "სისხლის სამართლის საპროცესო კოდექსი": "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი": "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "შრომის კოდექსი": "საქართველოს შრომის კოდექსი",
    "საგადასახადო კოდექსი": "საქართველოს საგადასახადო კოდექსი",
    "სამოქალაქო საპროცესო კოდექსი": "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "საარჩევნო კოდექსი": "საქართველოს საარჩევნო კოდექსი",
    "ზოგადი ადმინისტრაციული კოდექსი": "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "ადმინისტრაციული საპროცესო კოდექსი": "საქართველოს ადმინისტრაციული საპროცესო კოდექსი",
}


def _canonicalize_code_name(raw: str) -> str:
    """Ensure code_name uses the full canonical form with საქართველოს prefix."""
    return _CODE_NAME_CANONICAL.get(raw, raw)


def build_threshold_metadata(entry: dict) -> Metadata:
    """Build ChromaDB metadata for a threshold chunk."""
    return {
        "chunk_type": "threshold",
        "code_name": _canonicalize_code_name(entry["code_name"]),
        "article_number": entry["article_number"],
        "threshold_type": entry["threshold_type"],
        "description_ka": entry["description_ka"],
        "source_url": entry["source_url"],
        "last_verified": entry["last_verified"],
    }


def load_catalog() -> list[dict[str, str]]:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["thresholds"]


BATCH_SIZE = 200
BATCH_DELAY_SECONDS = 60
MAX_RETRIES = 5


def _embed_with_resume(
    embedder, documents: list[str], cache_path: Path
) -> list[Embedding]:
    cached: list[Embedding] = []
    if cache_path.exists():
        cached = json.loads(cache_path.read_text("utf-8"))
        print(f"  Resuming from cache: {len(cached)}/{len(documents)} already embedded")

    if len(cached) >= len(documents):
        print("  All embeddings cached — skipping API calls")
        return cached[: len(documents)]

    import time

    for i in range(len(cached), len(documents), BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                batch_embeddings = embedder.embed_texts(
                    batch, task_type="RETRIEVAL_DOCUMENT"
                )
                cached.extend(batch_embeddings)
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait = 2**attempt * 10
                    print(
                        f"  Rate limited, waiting {wait}s (attempt {attempt}/{MAX_RETRIES})..."
                    )
                    time.sleep(wait)
                else:
                    raise

        cache_path.write_text(json.dumps(cached), encoding="utf-8")
        done = min(i + BATCH_SIZE, len(documents))
        print(f"  Embedded {done}/{len(documents)} (saved to cache)")
        time.sleep(BATCH_DELAY_SECONDS)

    return cached


def ingest(*, dry_run: bool = False) -> int:
    """Ingest threshold data into ChromaDB. Returns count of chunks added."""
    thresholds = load_catalog()
    print(f"Loaded {len(thresholds)} threshold entries from catalog")

    ids = [f"threshold_{t['id']}" for t in thresholds]
    documents = [build_threshold_document(t) for t in thresholds]
    metadatas = [build_threshold_metadata(t) for t in thresholds]

    if dry_run:
        for chunk_id, doc in zip(ids, documents):
            print(f"\n{'='*60}")
            print(f"ID: {chunk_id}")
            print(doc)
        return len(thresholds)

    from dotenv import load_dotenv

    load_dotenv()

    from pipeline.embedder.vertex_embedder import VertexEmbedder

    embedder = VertexEmbedder()
    print(
        f"Embedding {len(documents)} documents with {embedder.model_name} ({embedder.dimensions}-dim)..."
    )

    cache_path = CATALOG_PATH.parent / "embedding_cache.json"
    all_embeddings = _embed_with_resume(embedder, documents, cache_path)

    client = chromadb.PersistentClient(path=str(CHROMA_PATH.resolve()))
    collection = client.get_collection(name=COLLECTION_NAME)

    existing_count = collection.count()
    print(f"Collection '{COLLECTION_NAME}' has {existing_count} chunks")

    collection.upsert(
        ids=ids, documents=documents, metadatas=metadatas, embeddings=all_embeddings
    )

    new_count = collection.count()
    added = new_count - existing_count
    print(f"Upserted {len(thresholds)} threshold chunks (net new: {added})")
    print(f"Collection now has {new_count} total chunks")
    return len(thresholds)


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    ingest(dry_run=dry)
