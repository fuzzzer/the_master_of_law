"""
ChromaDB integration — read-only connection to the pre-built law corpus.

The ChromaDB data at ``law_corpus/data/chroma/`` contains 9,450 chunks
across 12 Georgian legal codes, embedded with ``gemini-embedding-001``
at 768 dimensions.  This client provides a thin async-friendly wrapper
around the synchronous ``chromadb`` Python SDK.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaClient:
    """Manages the ChromaDB connection and provides search methods."""

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str | None = None,
    ) -> None:
        self._persist_dir = persist_dir or settings.chroma_persist_dir
        self._collection_name = collection_name or settings.chroma_collection_name
        self._client: chromadb.ClientAPI | None = None
        self._collection: chromadb.Collection | None = None

    # ── Lifecycle ────────────────────────────────────────────

    def connect(self) -> None:
        """Initialize the PersistentClient and verify the collection exists."""
        resolved = Path(self._persist_dir).resolve()
        logger.info("chroma_connecting", path=str(resolved))

        self._client = chromadb.PersistentClient(path=str(resolved))
        self._collection = self._client.get_collection(
            name=self._collection_name,
        )

        count = self._collection.count()
        logger.info(
            "chroma_connected",
            collection=self._collection_name,
            document_count=count,
        )

    @property
    def is_connected(self) -> bool:
        return self._collection is not None

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            raise RuntimeError("ChromaDB not connected — call connect() first")
        return self._collection

    # ── Search ───────────────────────────────────────────────

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 50,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query the collection by embedding vector.

        Returns a list of hit dicts with keys:
            chunk_id, content, metadata, distance
        """
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        hits: list[dict[str, Any]] = []
        if results["ids"]:
            for i, chunk_id in enumerate(results["ids"][0]):
                hits.append({
                    "chunk_id": chunk_id,
                    "content": (
                        results["documents"][0][i] if results["documents"] else ""
                    ),
                    "metadata": (
                        results["metadatas"][0][i] if results["metadatas"] else {}
                    ),
                    "distance": (
                        results["distances"][0][i] if results["distances"] else 0.0
                    ),
                })
        return hits

    def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Fetch specific chunks by their IDs."""
        if not ids:
            return []

        results = self.collection.get(
            ids=ids,
            include=["documents", "metadatas"],
        )

        items: list[dict[str, Any]] = []
        if results["ids"]:
            for i, chunk_id in enumerate(results["ids"]):
                items.append({
                    "chunk_id": chunk_id,
                    "content": (
                        results["documents"][i] if results["documents"] else ""
                    ),
                    "metadata": (
                        results["metadatas"][i] if results["metadatas"] else {}
                    ),
                })
        return items

    def count(self) -> int:
        """Return total number of documents in the collection."""
        return self.collection.count()


# ── Singleton ────────────────────────────────────────────────

_chroma_client: ChromaClient | None = None


def get_chroma_client() -> ChromaClient:
    """Return the singleton ChromaClient, connecting on first use."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
        _chroma_client.connect()
    return _chroma_client
