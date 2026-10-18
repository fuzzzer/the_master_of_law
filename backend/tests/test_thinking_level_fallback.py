"""A model that rejects `thinking_budget` gets `thinking_level` — once.

gemini-flash-lite-latest answers 400 INVALID_ARGUMENT to a thinking budget
of 0, which the guardrail and the model smoke test both send. The guardrail
failed open on every turn (one wasted call each), and the smoke test called
the model unusable. The client now retries with thinking_level=MINIMAL and
remembers the model.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai.types import ThinkingLevel

from app.integrations import vertex_ai_client as vc


@pytest.fixture(autouse=True)
def _forget_learned_models():
    vc._MODELS_WANTING_LEVEL.clear()
    yield
    vc._MODELS_WANTING_LEVEL.clear()


def _client_whose_model_wants_levels(calls: list):
    async def generate_content(*, model, contents, config):
        calls.append(config.thinking_config)
        if config.thinking_config and config.thinking_config.thinking_budget is not None:
            raise RuntimeError("400 INVALID_ARGUMENT. Request contains an invalid argument.")
        return MagicMock(text="OK", candidates=[])

    fake = MagicMock()
    fake.aio.models.generate_content = AsyncMock(side_effect=generate_content)
    return fake


@pytest.mark.asyncio
async def test_budget_rejected_then_level_sent_and_remembered():
    calls: list = []
    client = vc.VertexAIClient()
    with patch.object(client, "_get_client", return_value=_client_whose_model_wants_levels(calls)):
        text = await client.generate(
            prompt="hi", thinking_budget=0, model_name="gemini-flash-lite-latest",
        )
        assert text == "OK"
        assert calls[0].thinking_budget == 0
        assert calls[1].thinking_level == ThinkingLevel.MINIMAL

        # Second call on the same model: no wasted attempt.
        await client.generate(prompt="hi", thinking_budget=0, model_name="gemini-flash-lite-latest")
        assert len(calls) == 3
        assert calls[2].thinking_level == ThinkingLevel.MINIMAL


@pytest.mark.asyncio
async def test_other_errors_are_not_mistaken_for_a_budget_rejection():
    fake = MagicMock()
    fake.aio.models.generate_content = AsyncMock(
        side_effect=RuntimeError("429 RESOURCE_EXHAUSTED. quota")
    )
    client = vc.VertexAIClient()
    with patch.object(client, "_get_client", return_value=fake), patch.object(
        vc, "RETRY_MAX_ATTEMPTS", 1
    ):
        with pytest.raises(RuntimeError):
            await client.generate(prompt="hi", thinking_budget=0, model_name="m")
    assert "m" not in vc._MODELS_WANTING_LEVEL
