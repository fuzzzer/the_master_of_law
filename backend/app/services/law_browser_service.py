"""
Law Browser Service — browse and search the law corpus (always free).

Provides search and browsing over the pre-built ChromaDB corpus
and JSON indices without consuming credits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.integrations.chroma_client import ChromaClient, get_chroma_client
from app.integrations.vertex_embedding_client import get_embedding_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LawBrowserService:
    """Browse and search Georgian law corpus."""

    def __init__(self, chroma: ChromaClient | None = None):
        self._chroma = chroma
        self._code_index: dict | None = None
        self._article_index: dict | None = None

    @property
    def chroma(self) -> ChromaClient:
        if self._chroma is None:
            self._chroma = get_chroma_client()
        return self._chroma

    def list_codes(self) -> list[dict[str, Any]]:
        """List all available legal codes."""
        index = self._load_code_index()
        codes = []
        for code_id, data in index.items():
            if isinstance(data, dict):
                codes.append({
                    "code_id": code_id,
                    "name": data.get("name", code_id),
                    "article_count": data.get("article_count", 0),
                    "source_url": data.get("source_url", ""),
                })
            elif isinstance(data, list):
                unique_articles = set()
                for chunk_id in data:
                    # e.g. "admin_offences_code.article_1.chunk_0"
                    article_part = chunk_id.split(".chunk_")[0]
                    unique_articles.add(article_part)
                codes.append({
                    "code_id": code_id,
                    "name": code_id,
                    "article_count": len(unique_articles),
                    "source_url": "",
                })
            else:
                codes.append({"code_id": code_id, "name": code_id})
        return codes

    def get_code(self, code_id: str) -> dict[str, Any] | None:
        """Get a specific code with its structure."""
        index = self._load_code_index()
        data = index.get(code_id)
        if data is None:
            return None
            
        if isinstance(data, dict):
            return data
            
        if isinstance(data, list):
            try:
                results = self.chroma.collection.get(
                    where={"code_name": code_id},
                    include=["documents", "metadatas"]
                )
                items = []
                if results.get("ids"):
                    for i, cid in enumerate(results["ids"]):
                        items.append({
                            "chunk_id": cid,
                            "content": results["documents"][i] if results.get("documents") else "",
                            "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                        })
                return {"code_id": code_id, "chunks": items}
            except Exception as e:
                logger.error("get_code_failed", code_id=code_id, error=str(e))
                return {"code_id": code_id, "chunks": []}
                
        return {"code_id": code_id, "chunks": []}

    def get_article(self, article_id: str) -> list[dict[str, Any]]:
        """Get all chunks for a specific article.

        ``article_id`` is the chunk-id identity surfaced by :meth:`get_code`,
        e.g. ``"admin_offences_code.article_1.chunk_0"`` (a full chunk id) or
        ``"admin_offences_code.article_1"`` (the article prefix). The chunk
        metadata's ``article_number`` is the human label (e.g. ``"მუხლი 1"``)
        and never equals this id, so we resolve the article *prefix* and fetch
        every chunk that belongs to it by id.
        """
        try:
            # Normalize to the article prefix (drop any ".chunk_N" suffix).
            article_prefix = article_id.split(".chunk_")[0]

            # Enumerate every chunk id for this article from the code index.
            index = self._load_code_index()
            chunk_ids: list[str] = []
            for data in index.values():
                if isinstance(data, list):
                    for cid in data:
                        if isinstance(cid, str) and cid.split(".chunk_")[0] == article_prefix:
                            chunk_ids.append(cid)

            # Fallback: treat the input as a literal chunk id if the index
            # could not resolve it (e.g. dict-shaped index entries).
            if not chunk_ids:
                chunk_ids = [article_id]

            results = self.chroma.collection.get(
                ids=chunk_ids,
                include=["documents", "metadatas"],
            )
            items = []
            if results.get("ids"):
                for i, cid in enumerate(results["ids"]):
                    items.append({
                        "chunk_id": cid,
                        "content": results["documents"][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                    })
                # Order multi-chunk articles by their chunk index for readability.
                items.sort(key=lambda x: (x.get("metadata") or {}).get("chunk_index", 0))
            return items
        except Exception as e:
            logger.error("get_article_failed", article_id=article_id, error=str(e))
            return []

    def search(
        self, query: str, domain: str | None = None, top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search laws by query text.

        Uses vector search for semantic matching.
        """
        try:
            client = get_embedding_client()
            embedding = client.embed_query(query)
        except Exception as e:
            logger.error("search_embedding_failed", error=str(e))
            return []

        where = None
        if domain:
            where = {"code_name": domain}

        return self.chroma.vector_search(
            query_embedding=embedding,
            top_k=top_k,
            collections=["georgian_laws"],
            where=where,
        )

    def _load_code_index(self) -> dict:
        if self._code_index is not None:
            return self._code_index
        path = Path(settings.chroma_persist_dir).parent / "georgian_laws" / "index" / "code_index.json"
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._code_index = json.load(f)
            return self._code_index
        except Exception:
            return {}


_law_browser_service = None

def get_law_browser_service():
    global _law_browser_service
    if _law_browser_service is None:
        _law_browser_service = LawBrowserService()
    return _law_browser_service
