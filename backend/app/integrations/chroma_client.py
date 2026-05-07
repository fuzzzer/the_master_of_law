"""
ChromaDB integration — multi-collection support for the pre-built law corpus
and court practice data.

Collections:
  - "georgian_laws"   — 15 legal codes from Matsne (9,450 chunks)
  - "court_practice"  — Supreme Court case rulings (2022-2026)
  - "grand_chamber"   — Grand Chamber binding decisions & norm interpretations

The ChromaDB data at ``law_corpus/data/chroma/`` is embedded with
``gemini-embedding-001`` at 768 dimensions.  This client provides a thin
async-friendly wrapper around the synchronous ``chromadb`` Python SDK.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaClient:
    """Multi-collection ChromaDB client for the RAG pipeline."""

    # Collection registry — describes all expected collections.
    # Not all collections may be present in a given deployment.
    COLLECTIONS: dict[str, dict[str, str]] = {
        "georgian_laws": {
            "description": "Legal codes from Matsne (15 codes, 9,450 chunks)",
            "name_ka": "კანონმდებლობა",
        },
        "court_practice": {
            "description": "Supreme Court case rulings (2022-2026, ~600 cases)",
            "name_ka": "სასამართლო პრაქტიკა",
        },
        "grand_chamber": {
            "description": "Grand Chamber binding decisions and norm interpretations",
            "name_ka": "დიდი პალატა (სავალდებულო)",
        },
    }

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str | None = None,
    ) -> None:
        self._persist_dir = persist_dir or settings.chroma_persist_dir
        # Legacy single-collection name (for backward compat)
        self._legacy_collection_name = collection_name or settings.chroma_collection_name
        self._client: chromadb.ClientAPI | None = None
        self._collections: dict[str, chromadb.Collection] = {}
        # Legacy single-collection reference (backward compat)
        self._collection: chromadb.Collection | None = None

    # ── Lifecycle ────────────────────────────────────────────

    def connect(self) -> None:
        """Initialize the PersistentClient and load all available collections."""
        resolved = Path(self._persist_dir).resolve()
        logger.info("chroma_connecting", path=str(resolved))

        self._client = chromadb.PersistentClient(path=str(resolved))
        self._collections = {}

        # Load all available collections
        for name in self.COLLECTIONS:
            try:
                col = self._client.get_collection(name=name)
                self._collections[name] = col
                logger.info(
                    "chroma_collection_loaded",
                    name=name,
                    count=col.count(),
                )
            except Exception:
                logger.warning("chroma_collection_missing", name=name)

        # Legacy backward compat: set _collection to the primary collection
        if self._legacy_collection_name in self._collections:
            self._collection = self._collections[self._legacy_collection_name]
        elif self._collections:
            # Fallback to first available
            self._collection = next(iter(self._collections.values()))
        else:
            self._collection = None

        total = sum(c.count() for c in self._collections.values())
        logger.info(
            "chroma_connected",
            collections=list(self._collections.keys()),
            total_documents=total,
        )

    @property
    def is_connected(self) -> bool:
        return len(self._collections) > 0

    @property
    def collection(self) -> chromadb.Collection:
        """Legacy: returns the primary (georgian_laws) collection."""
        if self._collection is None:
            raise RuntimeError("ChromaDB not connected — call connect() first")
        return self._collection

    @property
    def available_collections(self) -> list[str]:
        """Return names of loaded collections."""
        return list(self._collections.keys())

    # ── Search ───────────────────────────────────────────────

    def vector_search(
        self,
        query_embedding: list[float],
        top_k: int = 50,
        collections: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query across specified collections by embedding vector.

        Parameters
        ----------
        query_embedding : list[float]
            The query embedding vector (768-dim).
        top_k : int
            Maximum results to return.
        collections : list[str] | None
            Which collections to search. None = all available.
        where : dict | None
            ChromaDB where filter.

        Returns
        -------
        list[dict]
            Hit dicts with keys: chunk_id, content, metadata, distance.
            Metadata includes "_collection" key identifying the source.
        """
        target = collections or list(self._collections.keys())
        all_hits: list[dict[str, Any]] = []

        for col_name in target:
            if col_name not in self._collections:
                continue

            col = self._collections[col_name]
            kwargs: dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                kwargs["where"] = where

            try:
                results = col.query(**kwargs)
            except Exception as e:
                logger.error(
                    "chroma_search_error",
                    collection=col_name,
                    error=str(e),
                )
                continue

            if results["ids"]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    meta = (
                        results["metadatas"][0][i] if results["metadatas"] else {}
                    )
                    # Tag with source collection
                    meta["_collection"] = col_name
                    all_hits.append({
                        "chunk_id": chunk_id,
                        "content": (
                            results["documents"][0][i]
                            if results["documents"]
                            else ""
                        ),
                        "metadata": meta,
                        "distance": (
                            results["distances"][0][i]
                            if results["distances"]
                            else 0.0
                        ),
                    })

        # Sort by distance (best matches first) and limit to top_k
        all_hits.sort(key=lambda x: x["distance"])
        return all_hits[:top_k]

    def get_by_ids(
        self,
        ids: list[str],
        collections: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch specific chunks by their IDs, searching across collections."""
        if not ids:
            return []

        target = collections or list(self._collections.keys())
        items: list[dict[str, Any]] = []
        remaining_ids = set(ids)

        for col_name in target:
            if not remaining_ids:
                break
            if col_name not in self._collections:
                continue

            col = self._collections[col_name]
            try:
                results = col.get(
                    ids=list(remaining_ids),
                    include=["documents", "metadatas"],
                )
            except Exception:
                continue

            if results["ids"]:
                for i, chunk_id in enumerate(results["ids"]):
                    meta = (
                        results["metadatas"][i] if results["metadatas"] else {}
                    )
                    meta["_collection"] = col_name
                    items.append({
                        "chunk_id": chunk_id,
                        "content": (
                            results["documents"][i]
                            if results["documents"]
                            else ""
                        ),
                        "metadata": meta,
                    })
                    remaining_ids.discard(chunk_id)

        return items

    def count(self, collection_name: str | None = None) -> int:
        """Return total number of documents, optionally for a specific collection."""
        if collection_name:
            if collection_name in self._collections:
                return self._collections[collection_name].count()
            return 0
        return sum(c.count() for c in self._collections.values())

    def get_collection_info(self) -> list[dict[str, Any]]:
        """Return information about all registered collections."""
        info = []
        for name, meta in self.COLLECTIONS.items():
            available = name in self._collections
            info.append({
                "id": name,
                "name_ka": meta["name_ka"],
                "description": meta["description"],
                "available": available,
                "chunk_count": (
                    self._collections[name].count() if available else 0
                ),
            })
        return info


# ── Singleton ────────────────────────────────────────────────

_chroma_client: ChromaClient | None = None


def get_chroma_client() -> ChromaClient:
    """Return the singleton ChromaClient, connecting on first use."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
        _chroma_client.connect()
    return _chroma_client
