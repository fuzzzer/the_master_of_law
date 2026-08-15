"""
Tests for the runtime model tier override.

The property that matters is precedence and failure behaviour: an override
wins over env, and a config-store outage falls back to env rather than taking
the app down — a working app on the configured model beats a 500.
"""

import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, ".")

import pytest

from app.services.model_config_service import ModelConfigService


def _redis(get_value=None, fail=False):
    r = MagicMock()
    if fail:
        r.get = AsyncMock(side_effect=RuntimeError("redis down"))
        r.set = AsyncMock(side_effect=RuntimeError("redis down"))
    else:
        r.get = AsyncMock(return_value=get_value)
        r.set = AsyncMock()
        r.delete = AsyncMock()
    return r


def _patched(svc_redis):
    return patch(
        "app.middleware.rate_limit_middleware.get_redis_client",
        return_value=svc_redis,
    )


class TestPrecedence:
    @pytest.mark.asyncio
    async def test_env_is_used_when_nothing_is_overridden(self):
        svc = ModelConfigService()
        with _patched(_redis(None)):
            strong = await svc.resolve("strong")
        assert strong.source == "env"
        assert strong.model  # whatever the environment says

    @pytest.mark.asyncio
    async def test_override_beats_env(self):
        svc = ModelConfigService()
        with _patched(_redis(json.dumps({"strong": "model-x"}))):
            strong = await svc.resolve("strong")
            cheap = await svc.resolve("cheap")
        assert (strong.model, strong.source) == ("model-x", "override")
        assert cheap.source == "env", "an untouched tier must not be dragged along"

    @pytest.mark.asyncio
    async def test_setting_one_tier_leaves_the_other_alone(self):
        svc = ModelConfigService()
        r = _redis(json.dumps({"strong": "model-x", "cheap": "model-y"}))
        with _patched(r):
            await svc.set_models(cheap="model-z")
        written = json.loads(r.set.call_args[0][1])
        assert written == {"strong": "model-x", "cheap": "model-z"}

    @pytest.mark.asyncio
    async def test_a_change_is_visible_immediately_not_after_the_ttl(self):
        """An operator who changes a model and sees the old one echoed back
        assumes it did not work."""
        svc = ModelConfigService()
        with _patched(_redis(None)):
            await svc.set_models(strong="model-new")
            assert (await svc.resolve("strong")).model == "model-new"


class TestFailureBehaviour:
    @pytest.mark.asyncio
    async def test_a_config_store_outage_falls_back_to_env(self):
        svc = ModelConfigService()
        with _patched(_redis(fail=True)):
            strong = await svc.resolve("strong")
        assert strong.source == "env"
        assert strong.model

    @pytest.mark.asyncio
    async def test_garbage_in_the_store_is_ignored(self):
        svc = ModelConfigService()
        with _patched(_redis("not json at all")):
            assert (await svc.resolve("strong")).source == "env"

    @pytest.mark.asyncio
    async def test_a_non_string_override_is_ignored(self):
        svc = ModelConfigService()
        with _patched(_redis(json.dumps({"strong": 42}))):
            assert (await svc.resolve("strong")).source == "env"

    @pytest.mark.asyncio
    async def test_unknown_tier_is_a_programming_error(self):
        svc = ModelConfigService()
        with pytest.raises(ValueError):
            await svc.resolve("medium")


class TestReset:
    @pytest.mark.asyncio
    async def test_reset_returns_both_tiers_to_env(self):
        svc = ModelConfigService()
        r = _redis(json.dumps({"strong": "x", "cheap": "y"}))
        with _patched(r):
            current = await svc.reset()
        r.delete.assert_awaited_once()
        assert {t.source for t in current.values()} == {"env"}
