"""
Tests for GuardrailService — topic classification with mocked Gemini.

Covers:
- Legal messages → proceed
- Off-topic → redirect
- Harmful → block
- Greetings → greeting response
- ADMIN bypass
- Disabled guardrails
- Low confidence fallback
- Gemini failure fallback
- Fixture-based batch classification
"""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, ".")

import pytest

from app.services.guardrail_service import GuardrailDecision, GuardrailService


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _mock_gemini_response(category: str, confidence: float) -> str:
    return json.dumps({"category": category, "confidence": confidence})


@pytest.fixture
def guardrail_service():
    mock_gemini = MagicMock()
    mock_gemini.generate = AsyncMock()
    return GuardrailService(gemini_client=mock_gemini)


class TestGuardrailDecision:
    def test_legal_should_proceed(self):
        d = GuardrailDecision(category="legal", confidence=0.9, should_proceed=True)
        assert d.should_proceed is True
        assert d.response_text is None

    def test_greeting_response_text(self):
        d = GuardrailDecision(category="greeting", confidence=0.9, should_proceed=False)
        assert d.response_text is not None
        assert "ბუნდოვანი კანონი" in d.response_text

    def test_off_topic_response_text(self):
        d = GuardrailDecision(category="off_topic", confidence=0.9, should_proceed=False)
        assert d.response_text is not None
        assert "სამართლებრივ" in d.response_text

    def test_harmful_response_text(self):
        d = GuardrailDecision(category="harmful", confidence=0.9, should_proceed=False)
        assert d.response_text is not None
        assert "ბოდიში" in d.response_text


class TestGuardrailClassification:
    @pytest.mark.asyncio
    async def test_legal_message_proceeds(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = _mock_gemini_response("legal", 0.95)
        decision = await guardrail_service.classify("ჩემი ბოსი გამათავისუფლა")
        assert decision.category == "legal"
        assert decision.should_proceed is True

    @pytest.mark.asyncio
    async def test_off_topic_blocked(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = _mock_gemini_response("off_topic", 0.9)
        decision = await guardrail_service.classify("რა ამინდი იქნება?")
        assert decision.category == "off_topic"
        assert decision.should_proceed is False

    @pytest.mark.asyncio
    async def test_harmful_blocked(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = _mock_gemini_response("harmful", 0.85)
        decision = await guardrail_service.classify("მინდა ადამიანის მოკვლა")
        assert decision.category == "harmful"
        assert decision.should_proceed is False

    @pytest.mark.asyncio
    async def test_greeting_handled(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = _mock_gemini_response("greeting", 0.95)
        decision = await guardrail_service.classify("გამარჯობა")
        assert decision.category == "greeting"
        assert decision.should_proceed is False

    @pytest.mark.asyncio
    async def test_low_confidence_defaults_to_legal(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = _mock_gemini_response("off_topic", 0.5)
        decision = await guardrail_service.classify("ეს ცოტა გაუგებარი კითხვაა")
        assert decision.category == "legal"
        assert decision.should_proceed is True

    @pytest.mark.asyncio
    async def test_gemini_failure_defaults_to_legal(self, guardrail_service):
        guardrail_service._gemini.generate.side_effect = Exception("API error")
        decision = await guardrail_service.classify("test message")
        assert decision.category == "legal"
        assert decision.should_proceed is True

    @pytest.mark.asyncio
    async def test_invalid_category_defaults_to_legal(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = json.dumps(
            {"category": "unknown_thing", "confidence": 0.9}
        )
        decision = await guardrail_service.classify("test")
        assert decision.category == "legal"
        assert decision.should_proceed is True


class TestGuardrailBypass:
    @pytest.mark.asyncio
    async def test_admin_bypasses_guardrails(self, guardrail_service):
        decision = await guardrail_service.classify("anything", user_tier="ADMIN")
        assert decision.category == "legal"
        assert decision.should_proceed is True
        guardrail_service._gemini.generate.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.guardrail_service.GUARDRAIL_ENABLED", False)
    async def test_disabled_guardrails_always_proceed(self, guardrail_service):
        decision = await guardrail_service.classify("рецепты борща")
        assert decision.category == "legal"
        assert decision.should_proceed is True
        guardrail_service._gemini.generate.assert_not_called()


class TestGuardrailFixtures:
    @pytest.mark.asyncio
    async def test_all_fixture_messages(self, guardrail_service):
        """Verify the guardrail service returns expected categories for all test messages."""
        fixture_path = FIXTURES_DIR / "guardrail_test_messages.json"
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for msg in data["messages"]:
            guardrail_service._gemini.generate.return_value = _mock_gemini_response(
                msg["expected"], 0.9,
            )
            decision = await guardrail_service.classify(msg["text"])
            expected_proceed = msg["expected"] == "legal"
            assert decision.should_proceed == expected_proceed, (
                f"Message: {msg['text']} — expected proceed={expected_proceed}, "
                f"got proceed={decision.should_proceed} (category={decision.category})"
            )


class TestGuardrailCallContract:
    """How we CALL the model — the part a mocked test can still hold honest.

    Every other test in this file mocks `generate` wholesale, which is why 15
    green tests coexisted with a guardrail that had stopped classifying on
    every single request: the mock cannot know that a 50-token output budget
    is entirely consumed by reasoning on a thinking model, leaving empty text.
    These assert the two properties that keep that from recurring.
    """

    @pytest.mark.asyncio
    async def test_disables_thinking_and_leaves_room_for_the_answer(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = _mock_gemini_response("legal", 0.9)
        await guardrail_service.classify("სამსახურიდან გამათავისუფლეს")

        kwargs = guardrail_service._gemini.generate.call_args.kwargs
        # Reasoning tokens come out of max_output_tokens. This call has nothing
        # to reason about, so thinking is off and the budget is all answer.
        assert kwargs["thinking_budget"] == 0, (
            "guardrail must disable thinking — with it on, a small output "
            "budget yields finishReason=MAX_TOKENS and empty text"
        )
        assert kwargs["max_output_tokens"] >= 128, (
            "budget must have headroom over the ~11 tokens of JSON actually "
            "emitted, so re-enabling thinking cannot silently empty it"
        )

    @pytest.mark.asyncio
    async def test_empty_response_is_distinguishable_from_a_real_verdict(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = ""
        decision = await guardrail_service.classify("სამსახურიდან გამათავისუფლეს")

        # Still fails OPEN — refusing a real legal question is the worse error.
        assert decision.category == "legal"
        assert decision.should_proceed is True
        # But it must NOT look like a successful low-confidence classification,
        # which is what (legal, 0.0) did: a guardrail that had been dead for
        # every request read as normal in the trace.
        assert decision.confidence is None

    @pytest.mark.asyncio
    async def test_exception_is_also_distinguishable(self, guardrail_service):
        guardrail_service._gemini.generate.side_effect = Exception("503 UNAVAILABLE")
        decision = await guardrail_service.classify("test")
        assert decision.should_proceed is True
        assert decision.confidence is None

    @pytest.mark.asyncio
    async def test_a_real_verdict_still_carries_its_confidence(self, guardrail_service):
        guardrail_service._gemini.generate.return_value = _mock_gemini_response("off_topic", 0.95)
        decision = await guardrail_service.classify("რა ამინდია დღეს?")
        assert decision.category == "off_topic"
        assert decision.confidence == 0.95
