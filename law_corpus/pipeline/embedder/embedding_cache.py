"""
Local embedding cache to avoid re-embedding unchanged chunks.

Keyed by ``chunk_id + content_hash`` — if neither changes, the
cached embedding is reused.
"""

from __future__ import annotations

import json
from pathlib import Path

import orjson

from pipeline.config import settings
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingCache:
    """File-backed cache mapping (chunk_id, content_hash) → embedding vector."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = cache_dir or settings.embeddings_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "_cache_index.json"
        self._index: dict[str, str] = self._load_index()

    def _load_index(self) -> dict[str, str]:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                logger.warning("Corrupt embedding cache index — rebuilding")
        return {}

    def _save_index(self) -> None:
        self._index_path.write_text(
            json.dumps(self._index, indent=2), encoding="utf-8",
        )

    @staticmethod
    def _key(chunk_id: str, content_hash: str) -> str:
        return f"{chunk_id}:{content_hash}"

    def get(self, chunk_id: str, content_hash: str) -> list[float] | None:
        """Return cached embedding or None."""
        key = self._key(chunk_id, content_hash)
        filename = self._index.get(key)
        if filename is None:
            return None
        path = self._dir / filename
        if not path.exists():
            return None
        try:
            return list(orjson.loads(path.read_bytes()))
        except (orjson.JSONDecodeError, OSError):
            return None

    def put(self, chunk_id: str, content_hash: str, embedding: list[float]) -> None:
        """Store an embedding in the cache."""
        key = self._key(chunk_id, content_hash)
        filename = f"{chunk_id.replace('.', '_')}.emb.json"
        path = self._dir / filename
        path.write_bytes(orjson.dumps(embedding))
        self._index[key] = filename
        # Save index periodically (every 100 entries)
        if len(self._index) % 100 == 0:
            self._save_index()

    def flush(self) -> None:
        """Persist the index to disk."""
        self._save_index()

    @property
    def size(self) -> int:
        return len(self._index)
