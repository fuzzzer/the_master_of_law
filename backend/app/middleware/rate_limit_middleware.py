"""
Per-tier rate limiting middleware.

Rate limits:
  FREE:  5 req/min
  PRO:   30 req/min
  ADMIN: 120 req/min

Uses a Redis-backed sliding window.
"""

from __future__ import annotations

import time
import uuid
import redis.asyncio as aioredis

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config.constants import TIER_RATE_LIMITS, UserTier
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_redis_client = None
_loop = None

def get_redis_client() -> aioredis.Redis:
    global _redis_client, _loop
    import asyncio
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None
    if _redis_client is None or _loop != current_loop:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        _loop = current_loop
    return _redis_client


async def check_redis_rate_limit(rate_limit_key: str, limit: int, window: float = 60.0) -> tuple[bool, int]:
    """
    Verify rate limit against Redis using a sliding window.
    Returns (is_allowed, retry_after_seconds).
    """
    redis_client = get_redis_client()
    now = time.time()
    clear_before = now - window
    try:
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(rate_limit_key, 0, clear_before)
            pipe.zadd(rate_limit_key, {f"{now}-{uuid.uuid4().hex}": now})
            pipe.zcard(rate_limit_key)
            pipe.zrange(rate_limit_key, 0, 0, withscores=True)
            pipe.expire(rate_limit_key, int(window))
            results = await pipe.execute()
            
            cardinality = results[2]
            oldest_range = results[3]
            
            if cardinality > limit:
                oldest_ts = oldest_range[0][1] if oldest_range else now - window
                retry_after = int(window - (now - oldest_ts)) + 1
                return False, max(1, retry_after)
            return True, 0
    except Exception as e:
        logger.error("redis_rate_limit_error", error=str(e))
        if settings.is_production:
            return False, 5  # Fail closed in production
        return True, 0  # Fail open in development


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding window rate limiter, per-user, per-tier."""

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
            # Fall back to client IP for rate limiting
            client_ip = request.client.host if request.client else "unknown"
            rate_limit_key = f"rate_limit:http:ip:{client_ip}"
            limit = 5
            tier_name = "ANONYMOUS"
            user_id = client_ip
        else:
            user_id = user.get("uid", "anonymous")
            tier_str = user.get("tier", "FREE")
            if tier_str == "SUPERADMIN":
                tier_str = "ADMIN"
            try:
                tier = UserTier(tier_str)
            except ValueError:
                tier = UserTier.FREE

            limit = TIER_RATE_LIMITS.get(tier, 5)
            rate_limit_key = f"rate_limit:http:{user_id}"
            tier_name = tier.value
        
        allowed, retry_after = await check_redis_rate_limit(rate_limit_key, limit)
        if not allowed:
            logger.warning("rate_limited", user_id=user_id, tier=tier_name, limit=limit)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded ({limit} req/min for {tier_name} tier)",
                    "retry_after_seconds": retry_after,
                },
            )

        return await call_next(request)
