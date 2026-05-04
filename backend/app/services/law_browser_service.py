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
            else:
                codes.append({"code_id": code_id, "name": code_id})
        return codes

    def get_code(self, code_id: str) -> dict[str, Any] | None:
        """Get a specific code with its structure."""
        index = self._load_code_index()
        return index.get(code_id)

    def get_article(self, article_id: str) -> list[dict[str, Any]]:
        """Get all chunks for a specific article."""
        try:
            results = self.chroma.collection.get(
                where={"article_number": article_id},
                include=["documents", "metadatas"],
            )
            items = []
            if results["ids"]:
                for i, cid in enumerate(results["ids"]):
                    items.append({
                        "chunk_id": cid,
                        "content": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    })
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
            where=where,
        )

    def _load_code_index(self) -> dict:
        if self._code_index is not None:
            return self._code_index
        path = Path(settings.chroma_persist_dir).parent / "index" / "code_index.json"
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
