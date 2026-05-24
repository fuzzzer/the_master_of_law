"""
Tests for rate limiting middleware.

Tests the in-memory sliding window rate limiter for all tiers.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.constants import TIER_RATE_LIMITS, UserTier
from app.middleware.rate_limit_middleware import RateLimitMiddleware


def _make_request(path: str = "/api/v1/chat/123/send", user: dict | None = None):
    """Create a mock Request with the given path and user state."""
    request = MagicMock()
    request.url.path = path
    request.method = "POST"
    if user:
        request.state.user = user
    else:
        # No user attribute at all
        request.state = MagicMock(spec=[])
    return request


def _make_call_next():
    """Create a mock call_next that returns a 200 response."""
    response = MagicMock()
    response.status_code = 200
    return AsyncMock(return_value=response)


class TestRateLimitMiddleware:
    """Rate limiting per-user, per-tier."""

    def setup_method(self):
        self.app = MagicMock()
        self.middleware = RateLimitMiddleware(self.app)

    @pytest.mark.asyncio
    async def test_within_free_limit(self):
        """5 requests within FREE limit should all pass."""
        user = {"uid": "user1", "tier": "FREE"}
        call_next = _make_call_next()

        for _ in range(5):
            request = _make_request(user=user)
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_exceed_free_limit(self):
        """6th request in a minute should be rate limited."""
        user = {"uid": "user2", "tier": "FREE"}
        call_next = _make_call_next()

        for _ in range(5):
            request = _make_request(user=user)
            await self.middleware.dispatch(request, call_next)

        # 6th request → 429
        request = _make_request(user=user)
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 429
        assert response.body is not None

    @pytest.mark.asyncio
    async def test_pro_tier_limit(self):
        """PRO tier should allow 30 requests."""
        user = {"uid": "user3", "tier": "PRO"}
        call_next = _make_call_next()

        for _ in range(30):
            request = _make_request(user=user)
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_tier_limit(self):
        """ADMIN tier should allow 120 requests."""
        user = {"uid": "user4", "tier": "ADMIN"}
        call_next = _make_call_next()

        for _ in range(120):
            request = _make_request(user=user)
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_window_reset(self):
        """After the 60s window expires, counter should reset."""
        user = {"uid": "user5", "tier": "FREE"}
        call_next = _make_call_next()

        # Fill the window
        for _ in range(5):
            request = _make_request(user=user)
            await self.middleware.dispatch(request, call_next)

        # Manually expire timestamps
        now = time.time()
        self.middleware._requests["user5"] = [now - 61.0] * 5

        # Should pass now
        request = _make_request(user=user)
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_public_path_bypass_health(self):
        """Health check paths should bypass rate limiting."""
        call_next = _make_call_next()
        request = _make_request(path="/api/v1/health")
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_public_path_bypass_laws(self):
        """Law browsing paths should bypass rate limiting."""
        call_next = _make_call_next()
        request = _make_request(path="/api/v1/laws/search")
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_user_bypasses(self):
        """Requests with no user state should pass through (auth not done yet)."""
        call_next = _make_call_next()
        request = _make_request(user=None)
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_non_api_path_bypasses(self):
        """Non-API paths (/docs, etc.) should bypass rate limiting."""
        call_next = _make_call_next()
        request = _make_request(path="/docs")
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unknown_tier_defaults_to_free(self):
        """Unknown tier string should default to FREE limits."""
        user = {"uid": "user6", "tier": "UNKNOWN"}
        call_next = _make_call_next()

        for _ in range(5):
            request = _make_request(user=user)
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 200

        # 6th → 429 (FREE limit)
        request = _make_request(user=user)
        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_cleanup_removes_expired(self):
        """Old timestamps outside window should be cleaned."""
        user = {"uid": "user7", "tier": "FREE"}
        call_next = _make_call_next()
        now = time.time()

        # Plant old and new timestamps
        self.middleware._requests["user7"] = [now - 120, now - 90, now - 1]

        request = _make_request(user=user)
        await self.middleware.dispatch(request, call_next)

        # Only the recent timestamp + current should remain
        assert len(self.middleware._requests["user7"]) == 2
