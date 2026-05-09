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


CATALOG_PATH = Path(__file__).parent / "data" / "thresholds" / "threshold_catalog.json"
CHROMA_PATH = Path(__file__).parent / "data" / "chroma"
COLLECTION_NAME = "georgian_laws"


def build_threshold_document(entry: dict) -> str:
    """Build a searchable text document from a threshold entry."""
    parts = [
        f"[იურიდიული ზღვარი / Legal Threshold]",
        f"კოდექსი: {entry['code_name']}",
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


def build_threshold_metadata(entry: dict) -> dict:
    """Build ChromaDB metadata for a threshold chunk."""
    return {
        "chunk_type": "threshold",
        "code_name": entry["code_name"],
        "article_number": entry["article_number"],
        "threshold_type": entry["threshold_type"],
        "description_ka": entry["description_ka"],
        "source_url": entry["source_url"],
        "last_verified": entry["last_verified"],
    }


def load_catalog() -> list[dict]:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["thresholds"]


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

    client = chromadb.PersistentClient(path=str(CHROMA_PATH.resolve()))
    collection = client.get_collection(name=COLLECTION_NAME)

    existing_count = collection.count()
    print(f"Collection '{COLLECTION_NAME}' has {existing_count} chunks")

    # Upsert (idempotent) — ChromaDB will re-embed using its configured function
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    new_count = collection.count()
    added = new_count - existing_count
    print(f"Upserted {len(thresholds)} threshold chunks (net new: {added})")
    print(f"Collection now has {new_count} total chunks")
    return len(thresholds)


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    ingest(dry_run=dry)
