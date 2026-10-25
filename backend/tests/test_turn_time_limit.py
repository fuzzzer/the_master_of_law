"""
A chat turn must end in bounded time with a Georgian message.

The bug this pins: one model request hung for 27 minutes in the 2026-10-24
evaluation. Nothing in the pipeline limited it, so the user watched a spinner
for the whole time and then got nothing.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import httpx
import pytest

from app.services import agent_pipeline_service as aps
from app.services.agent_pipeline_service import AgentPipelineService
from app.utils.provider_errors import ProviderErrorKind, TurnTimeoutError, classify


@pytest.mark.asyncio
async def test_a_turn_past_its_limit_raises_turn_timeout():
    async def hangs(**_kwargs):
        await asyncio.sleep(10)

    svc = AgentPipelineService()
    with patch.object(aps, "TURN_TIMEOUT_S", 0.05), patch.object(svc, "_run", hangs):
        with pytest.raises(TurnTimeoutError):
            await svc.run(user_message="კითხვა")


@pytest.mark.asyncio
async def test_a_turn_inside_its_limit_returns_normally():
    result = aps.PipelineResult(response_text="პასუხი")

    async def quick(**_kwargs):
        return result

    svc = AgentPipelineService()
    with patch.object(svc, "_run", quick):
        assert await svc.run(user_message="კითხვა") is result


@pytest.mark.parametrize("exc", [
    TurnTimeoutError("turn exceeded 300 s"),
    httpx.ReadTimeout("timed out"),
    TimeoutError(),
])
def test_timeouts_become_a_clear_georgian_message(exc):
    err = classify(exc)
    assert err.kind is ProviderErrorKind.TIMEOUT
    assert err.status_code == 504
    assert err.error_code == "ai_timeout"
    assert "დიდი დრო" in err.message_ka
    assert err.is_provider_fault, "a timeout must not surface as a bare 500"
