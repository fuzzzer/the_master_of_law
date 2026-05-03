"""Tests for the embedder module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.embedder.embedding_cache import EmbeddingCache


class TestEmbeddingCache:
    """Test the file-backed embedding cache."""

    def test_put_and_get(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        embedding = [0.1, 0.2, 0.3, 0.4]
        cache.put("chunk_1", "hash_abc", embedding)

        result = cache.get("chunk_1", "hash_abc")
        assert result is not None
        assert len(result) == 4
        assert abs(result[0] - 0.1) < 1e-6

    def test_cache_miss(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        result = cache.get("nonexistent", "hash_abc")
        assert result is None

    def test_different_hash_misses(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        cache.put("chunk_1", "hash_v1", [1.0, 2.0])

        # Same chunk_id but different hash should miss
        result = cache.get("chunk_1", "hash_v2")
        assert result is None

    def test_flush_persists(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        cache.put("chunk_1", "hash_abc", [0.1, 0.2])
        cache.flush()

        # Load a new cache instance — should see the same data
        cache2 = EmbeddingCache(cache_dir=tmp_path)
        result = cache2.get("chunk_1", "hash_abc")
        assert result is not None

    def test_size_tracking(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(cache_dir=tmp_path)
        assert cache.size == 0
        cache.put("a", "h1", [1.0])
        cache.put("b", "h2", [2.0])
        assert cache.size == 2
