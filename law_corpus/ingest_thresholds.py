"""
Ingest structured legal threshold data into ChromaDB.

Reads ``data/thresholds/threshold_catalog.json``, generates embeddings
with ``gemini-embedding-001`` (RETRIEVAL_DOCUMENT), and upserts chunks
into the existing ``georgian_laws`` collection with
``chunk_type: "threshold"`` metadata.

Usage:
    cd law_corpus
    python -m ingest_thresholds

Or from project root:
    python law_corpus/ingest_thresholds.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from project root or law_corpus directory
_repo_root = Path(__file__).resolve().parent
if _repo_root.name == "law_corpus":
    sys.path.insert(0, str(_repo_root))

from pipeline.config import settings
from pipeline.utils.logger import get_logger

logger = get_logger("ingest_thresholds")


def _load_catalog(path: Path | None = None) -> list[dict]:
    catalog_path = path or (_repo_root / "data" / "thresholds" / "threshold_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("thresholds", [])


def _build_document(th: dict) -> str:
    """Build human-readable text from a threshold entry for embedding."""
    parts = [
        f"სამართლებრივი ზღვარი: {th['description_ka']}",
        f"კოდექსი: {th['code_name']}",
        f"მუხლი: {th['article_number']}",
        f"ზღვრის ტიპი: {th['threshold_type']}",
    ]
    if th.get("substance"):
        parts.append(f"საგანი: {th['substance']}")
    if th.get("values"):
        parts.append("მნიშვნელობები:")
        for key, val in th["values"].items():
            parts.append(f"  • {key}: {val}")
    if th.get("consequence_ka"):
        parts.append(f"შედეგი: {th['consequence_ka']}")
    return "\n".join(parts)


def _build_metadata(th: dict) -> dict:
    """Build ChromaDB metadata dict from a threshold entry."""
    meta = {
        "chunk_type": "threshold",
        "code_name": th.get("code_name", ""),
        "article_number": th.get("article_number", ""),
        "threshold_type": th.get("threshold_type", ""),
        "description_ka": th.get("description_ka", ""),
        "source_url": th.get("source_url", ""),
        "last_verified": th.get("last_verified", ""),
        "threshold_id": th.get("id", ""),
    }
    if th.get("substance"):
        meta["substance"] = th["substance"]
    # Flatten values dict into dot-notation strings for ChromaDB metadata
    # (ChromaDB does not support nested dicts in metadata)
    for key, val in th.get("values", {}).items():
        meta[f"value_{key}"] = str(val)
    return meta


def _get_embedder():
    """Return a Vertex embedder configured for DOCUMENT embedding."""
    from google import genai
    from google.genai.types import EmbedContentConfig

    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
    model = settings.embedding_model
    dimensions = settings.embedding_dimensions

    def embed_texts(texts: list[str]) -> list[list[float]]:
        result = client.models.embed_content(
            model=model,
            contents=texts,
            config=EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=dimensions,
            ),
        )
        return [list(e.values) for e in result.embeddings]

    return embed_texts


def ingest(
    catalog_path: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Ingest all threshold entries into ChromaDB. Returns count inserted."""
    thresholds = _load_catalog(catalog_path)
    if not thresholds:
        logger.warning("No thresholds found in catalog")
        return 0

    logger.info("Loaded %d thresholds from catalog", len(thresholds))

    # Build documents and metadata
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for th in thresholds:
        th_id = th.get("id")
        if not th_id:
            logger.warning("Skipping threshold without id")
            continue
        doc = _build_document(th)
        meta = _build_metadata(th)
        documents.append(doc)
        metadatas.append(meta)
        ids.append(th_id)

    if dry_run:
        logger.info("DRY RUN — would insert %d threshold chunks", len(ids))
        for i, doc in enumerate(documents[:3]):
            logger.info("Sample %d:\n%s\n---", i + 1, doc[:400])
        return len(ids)

    # Generate embeddings
    logger.info("Generating embeddings for %d thresholds...", len(documents))
    embed_fn = _get_embedder()
    embeddings = embed_fn(documents)
    logger.info("Embeddings generated: %d vectors of dim %d", len(embeddings), len(embeddings[0]))

    # Upsert into ChromaDB
    import chromadb

    persist_dir = Path(settings.chroma_persist_dir).resolve()
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(
        name="georgian_laws",
        metadata={"hnsw:space": "cosine"},
    )

    # Delete any existing threshold chunks to avoid duplicates
    existing_ids = set(collection.get(ids=ids)["ids"])
    if existing_ids:
        collection.delete(ids=list(existing_ids))
        logger.info("Deleted %d existing threshold chunks before re-insert", len(existing_ids))

    batch_size = 50
    total_upserted = 0
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i : i + batch_size]
        batch_embeddings = embeddings[i : i + batch_size]
        batch_documents = documents[i : i + batch_size]
        batch_metadatas = metadatas[i : i + batch_size]
        collection.upsert(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )
        total_upserted += len(batch_ids)
        logger.info("Upserted batch %d/%d (%d chunks)", i // batch_size + 1, (len(ids) - 1) // batch_size + 1, len(batch_ids))

    logger.info(
        "Threshold ingestion complete: %d chunks in collection '%s' (total now %d)",
        total_upserted,
        "georgian_laws",
        collection.count(),
    )
    return total_upserted


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest legal thresholds into ChromaDB")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be inserted without writing")
    parser.add_argument("--catalog", type=Path, default=None, help="Path to threshold_catalog.json")
    args = parser.parse_args()

    count = ingest(catalog_path=args.catalog, dry_run=args.dry_run)
    print(f"\n✅ Ingested {count} threshold chunks into ChromaDB")
