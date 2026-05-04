"""
Context Cache service — Vertex AI CachedContent for multi-turn cost optimization.

Caches system prompt + retrieved law chunks so they aren't re-sent on every
conversation turn. Saves ~50,000 input tokens in a 10-turn conversation.

NOTE: This uses the google-genai SDK's caching support. The actual Vertex AI
caching API requires specific model support and quota. This service provides
the infrastructure; actual cache creation is a no-op until the production
environment supports it.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory cache store (in production, use Redis or DB)
_cache_store: dict[str, dict[str, Any]] = {}

# Cache TTL
CACHE_TTL_MINUTES = 30


class ContextCacheService:
    """
    Manages context caching for multi-turn conversations.

    On Turn 1: creates a cached context with system prompt + law chunks.
    On Turn 2+: reuses the cache, sending only the new user message.
    On topic change: invalidates and rebuilds with new law chunks.
    """

    def get_or_create_cache(
        self,
        conversation_id: str,
        system_prompt: str,
        law_chunks: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Get an existing cache or create a new one.

        Returns the cache entry with cache_id, or None if caching is disabled.
        """
        # Check for existing valid cache
        existing = _cache_store.get(conversation_id)
        if existing and not self._is_expired(existing):
            logger.info("context_cache_hit", conversation_id=conversation_id)
            return existing

        # Create new cache entry
        cache_id = str(uuid.uuid4())
        cache_entry = {
            "cache_id": cache_id,
            "conversation_id": conversation_id,
            "system_prompt": system_prompt,
            "chunk_ids": [c.get("chunk_id", "") for c in law_chunks],
            "chunk_count": len(law_chunks),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=CACHE_TTL_MINUTES)).isoformat(),
        }

        _cache_store[conversation_id] = cache_entry
        logger.info(
            "context_cache_created",
            conversation_id=conversation_id,
            cache_id=cache_id,
            chunks=len(law_chunks),
        )
        return cache_entry

    def invalidate_cache(self, conversation_id: str) -> bool:
        """
        Invalidate a conversation's cache.

        Called when the user changes topic and new law chunks are needed.
        """
        if conversation_id in _cache_store:
            del _cache_store[conversation_id]
            logger.info("context_cache_invalidated", conversation_id=conversation_id)
            return True
        return False

    def should_rebuild(
        self,
        conversation_id: str,
        new_chunk_ids: list[str],
    ) -> bool:
        """
        Determine if the cache needs rebuilding (e.g., topic change).

        Compares new chunk IDs with cached ones. If >50% are different,
        the topic has likely changed and cache should be rebuilt.
        """
        existing = _cache_store.get(conversation_id)
        if not existing or self._is_expired(existing):
            return True

        cached_ids = set(existing.get("chunk_ids", []))
        new_ids = set(new_chunk_ids)

        if not cached_ids:
            return True

        overlap = len(cached_ids & new_ids)
        overlap_ratio = overlap / max(len(cached_ids), 1)

        # Rebuild if less than 50% overlap
        return overlap_ratio < 0.5

    def get_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        now = datetime.now(timezone.utc)
        active = sum(1 for c in _cache_store.values() if not self._is_expired(c))
        return {
            "total_entries": len(_cache_store),
            "active_entries": active,
            "expired_entries": len(_cache_store) - active,
        }

    def cleanup_expired(self) -> int:
        """Remove expired cache entries. Returns count removed."""
        expired = [k for k, v in _cache_store.items() if self._is_expired(v)]
        for k in expired:
            del _cache_store[k]
        if expired:
            logger.info("context_cache_cleanup", removed=len(expired))
        return len(expired)

    @staticmethod
    def _is_expired(cache_entry: dict[str, Any]) -> bool:
        """Check if a cache entry has expired."""
        expires_at_str = cache_entry.get("expires_at", "")
        if not expires_at_str:
            return True
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            return datetime.now(timezone.utc) > expires_at
        except (ValueError, TypeError):
            return True


_context_cache = None

def get_context_cache_service():
    global _context_cache
    if _context_cache is None:
        _context_cache = ContextCacheService()
    return _context_cache
