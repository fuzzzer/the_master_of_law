"""
Model Config Service — the effective model for each tier, changeable at runtime.

The two tiers (STRONG / CHEAP) are configured from the environment, which is
right for deployment but useless for the thing people actually want to do:
compare models against real Georgian legal questions without a redeploy. This
adds a runtime OVERRIDE on top of the env value.

Precedence, highest first:
    1. runtime override   (set from the UI, stored in Redis)
    2. environment        (GEMINI_STRONG_MODEL / GEMINI_CHEAP_MODEL)

Redis rather than process memory because the API runs as one container today
but is not promised to stay that way — an override held in a worker's globals
would apply to whichever worker happened to serve the next request, which is
the kind of "it works intermittently" that costs an afternoon to diagnose.
It also survives a restart, which an operator changing a model expects.

Redis being down must NOT take the app with it: every read falls back to the
env value, because a working app on the configured model beats a 500.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

REDIS_KEY = "fuzzzy:model_config"

# Reads happen 6-12 times per request; a Redis round-trip each time is waste.
# The TTL is the worst-case delay between changing a model and it taking
# effect, so it is short enough that an operator does not think it failed.
_CACHE_TTL_S = 5.0

TIERS = ("strong", "cheap")


@dataclass(frozen=True)
class TierModel:
    tier: str
    model: str
    source: str  # "override" | "env"


class ModelConfigService:
    def __init__(self) -> None:
        self._cache: dict[str, str] = {}
        self._cache_at: float = 0.0

    # ── Effective values ──────────────────────────────────────

    def _env_default(self, tier: str) -> str:
        return (
            settings.gemini_strong_model
            if tier == "strong"
            else settings.gemini_cheap_model
        )

    async def _overrides(self) -> dict[str, str]:
        """Current overrides, cached briefly. Never raises."""
        now = time.monotonic()
        if self._cache_at and (now - self._cache_at) < _CACHE_TTL_S:
            return self._cache
        try:
            from app.middleware.rate_limit_middleware import get_redis_client

            raw = await get_redis_client().get(REDIS_KEY)
            data = json.loads(raw) if raw else {}
            if not isinstance(data, dict):
                data = {}
            self._cache = {
                t: str(data[t]) for t in TIERS if isinstance(data.get(t), str) and data[t]
            }
        except Exception as e:  # noqa: BLE001 — a config store outage is not an outage
            logger.warning("model_config_read_failed", error=str(e)[:200])
            # Keep serving the last known value rather than thrashing to env
            # on a blip; if we never read one, _cache is {} and env wins.
        self._cache_at = now
        return self._cache

    async def resolve(self, tier: str) -> TierModel:
        if tier not in TIERS:
            raise ValueError(f"unknown tier {tier!r}")
        override = (await self._overrides()).get(tier)
        if override:
            return TierModel(tier=tier, model=override, source="override")
        return TierModel(tier=tier, model=self._env_default(tier), source="env")

    async def strong(self) -> str:
        return (await self.resolve("strong")).model

    async def cheap(self) -> str:
        return (await self.resolve("cheap")).model

    async def current(self) -> dict[str, TierModel]:
        return {t: await self.resolve(t) for t in TIERS}

    # ── Mutation ──────────────────────────────────────────────

    async def set_models(
        self,
        *,
        strong: str | None = None,
        cheap: str | None = None,
    ) -> dict[str, TierModel]:
        """Override one or both tiers. Passing None leaves a tier untouched."""
        current = dict(await self._overrides())
        if strong:
            current["strong"] = strong
        if cheap:
            current["cheap"] = cheap

        from app.middleware.rate_limit_middleware import get_redis_client

        await get_redis_client().set(REDIS_KEY, json.dumps(current))
        # Write-through, so the change is visible immediately rather than
        # after the TTL — an operator who changes a model and sees the old
        # one echoed back assumes it did not work.
        self._cache = current
        self._cache_at = time.monotonic()
        logger.info("model_config_set", strong=strong, cheap=cheap)
        return await self.current()

    async def reset(self) -> dict[str, TierModel]:
        """Drop all overrides and fall back to the environment."""
        from app.middleware.rate_limit_middleware import get_redis_client

        await get_redis_client().delete(REDIS_KEY)
        self._cache = {}
        self._cache_at = time.monotonic()
        logger.info("model_config_reset")
        return await self.current()


_service: ModelConfigService | None = None


def get_model_config_service() -> ModelConfigService:
    global _service
    if _service is None:
        _service = ModelConfigService()
    return _service


# ── Convenience for call sites ───────────────────────────────
# Every place that used to read settings.gemini_*_model calls one of these
# instead, so a runtime change reaches the whole pipeline and there is no
# second source of truth to drift.

async def strong_model() -> str:
    return await get_model_config_service().strong()


async def cheap_model() -> str:
    return await get_model_config_service().cheap()
