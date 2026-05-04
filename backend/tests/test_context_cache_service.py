"""
Tests for the Context Cache Service.

Verifies:
- Cache creation and retrieval
- Cache expiry detection
- Cache invalidation
- Topic change detection (chunk overlap)
- Cleanup of expired entries
"""

from __future__ import annotations

import sys
sys.path.insert(0, ".")

import time
import pytest
from datetime import datetime, timedelta, timezone

from app.services.context_cache_service import (
    ContextCacheService,
    _cache_store,
    CACHE_TTL_MINUTES,
)


class TestContextCache:
    """Tests for ContextCacheService."""

    def setup_method(self):
        self.svc = ContextCacheService()
        _cache_store.clear()

    def teardown_method(self):
        _cache_store.clear()

    def test_create_new_cache(self):
        result = self.svc.get_or_create_cache(
            conversation_id="conv-1",
            system_prompt="test prompt",
            law_chunks=[{"chunk_id": "c1"}, {"chunk_id": "c2"}],
        )
        assert result is not None
        assert result["conversation_id"] == "conv-1"
        assert result["chunk_count"] == 2

    def test_cache_hit(self):
        # Create first
        first = self.svc.get_or_create_cache("conv-1", "prompt", [{"chunk_id": "c1"}])
        # Get again — should return same
        second = self.svc.get_or_create_cache("conv-1", "prompt", [{"chunk_id": "c1"}])
        assert first["cache_id"] == second["cache_id"]

    def test_invalidate_cache(self):
        self.svc.get_or_create_cache("conv-1", "prompt", [])
        assert self.svc.invalidate_cache("conv-1") is True
        assert "conv-1" not in _cache_store

    def test_invalidate_nonexistent(self):
        assert self.svc.invalidate_cache("nonexistent") is False

    def test_should_rebuild_no_existing(self):
        assert self.svc.should_rebuild("conv-1", ["c1", "c2"]) is True

    def test_should_rebuild_same_chunks(self):
        self.svc.get_or_create_cache("conv-1", "prompt", [
            {"chunk_id": "c1"}, {"chunk_id": "c2"}, {"chunk_id": "c3"},
        ])
        # Same chunks → should NOT rebuild
        assert self.svc.should_rebuild("conv-1", ["c1", "c2", "c3"]) is False

    def test_should_rebuild_different_chunks(self):
        self.svc.get_or_create_cache("conv-1", "prompt", [
            {"chunk_id": "c1"}, {"chunk_id": "c2"},
        ])
        # Completely different chunks → should rebuild
        assert self.svc.should_rebuild("conv-1", ["c10", "c11"]) is True

    def test_should_rebuild_partial_overlap(self):
        self.svc.get_or_create_cache("conv-1", "prompt", [
            {"chunk_id": "c1"}, {"chunk_id": "c2"}, {"chunk_id": "c3"}, {"chunk_id": "c4"},
        ])
        # 1 out of 4 overlap = 25% < 50% → should rebuild
        assert self.svc.should_rebuild("conv-1", ["c1", "c10", "c11", "c12"]) is True

    def test_expired_cache_detected(self):
        self.svc.get_or_create_cache("conv-1", "prompt", [])
        # Manually expire
        _cache_store["conv-1"]["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()
        # Should create a new cache
        result = self.svc.get_or_create_cache("conv-1", "prompt", [{"chunk_id": "new"}])
        assert result["chunk_count"] == 1  # New cache with new chunks

    def test_cleanup_expired(self):
        self.svc.get_or_create_cache("conv-1", "prompt", [])
        self.svc.get_or_create_cache("conv-2", "prompt", [])
        # Expire conv-1
        _cache_store["conv-1"]["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()
        removed = self.svc.cleanup_expired()
        assert removed == 1
        assert "conv-1" not in _cache_store
        assert "conv-2" in _cache_store

    def test_get_stats(self):
        self.svc.get_or_create_cache("conv-1", "prompt", [])
        self.svc.get_or_create_cache("conv-2", "prompt", [])
        stats = self.svc.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0


class TestCacheTTL:
    """Tests for cache TTL configuration."""

    def test_ttl_is_30_minutes(self):
        assert CACHE_TTL_MINUTES == 30
