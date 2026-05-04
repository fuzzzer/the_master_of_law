"""
Per-tier rate limiting middleware.

Rate limits:
  FREE:  5 req/min
  PRO:   30 req/min
  ADMIN: 120 req/min

Uses an in-memory sliding window counter.
In production, this should use Redis for distributed rate limiting.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config.constants import TIER_RATE_LIMITS, UserTier
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter, per-user, per-tier."""

    def __init__(self, app):
        super().__init__(app)
        # user_id -> list of timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # Only rate-limit API routes
        if not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        # Skip rate limiting for health checks and law browsing
        if request.url.path.startswith(("/api/v1/health", "/api/v1/laws/")):
            return await call_next(request)

        # Get user info from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return await call_next(request)

        user_id = user.get("uid", "anonymous")
        tier_str = user.get("tier", "FREE")
        try:
            tier = UserTier(tier_str)
        except ValueError:
            tier = UserTier.FREE

        limit = TIER_RATE_LIMITS.get(tier, 5)
        now = time.time()
        window = 60.0  # 1 minute

        # Clean old entries
        timestamps = self._requests[user_id]
        timestamps[:] = [t for t in timestamps if now - t < window]

        if len(timestamps) >= limit:
            logger.warning("rate_limited", user_id=user_id, tier=tier.value, limit=limit)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded ({limit} req/min for {tier.value} tier)",
                    "retry_after_seconds": int(window - (now - timestamps[0])) + 1,
                },
            )

        timestamps.append(now)
        return await call_next(request)
