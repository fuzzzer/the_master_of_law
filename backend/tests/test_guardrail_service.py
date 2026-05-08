"""
Unit tests for GuardrailService.

All Gemini Flash calls are mocked to avoid external dependencies.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.guardrail_schema import GuardrailCategory, GuardrailDecision
from app.services.guardrail_service import (
    GUARDRAIL_RESPONSES_KA,
    GuardrailService,
)


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def mock_gemini():
    gemini = MagicMock()
    gemini.generate = AsyncMock()
    return gemini


@pytest.fixture
def service(mock_gemini):
    return GuardrailService(
        gemini_client=mock_gemini,
        confidence_threshold=0.7,
        enabled=True,
    )


# ── Classification tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_classify_legal(service, mock_gemini):
    mock_gemini.generate.return_value = json.dumps({"category": "legal", "confidence": 0.95})
    decision = await service.classify("რამდენია ჯარიმა სიჩქარის გადაჭარბებისთვის?")
    assert decision.category == GuardrailCategory.LEGAL
    assert decision.is_legal is True
    assert decision.confidence == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_classify_greeting(service, mock_gemini):
    mock_gemini.generate.return_value = json.dumps({"category": "greeting", "confidence": 0.92})
    decision = await service.classify("გამარჯობა")
    assert decision.category == GuardrailCategory.GREETING
    assert decision.is_legal is False


@pytest.mark.asyncio
async def test_classify_off_topic(service, mock_gemini):
    mock_gemini.generate.return_value = json.dumps({"category": "off_topic", "confidence": 0.88})
    decision = await service.classify("რა ამინდია დღეს?")
    assert decision.category == GuardrailCategory.OFF_TOPIC
    assert decision.is_legal is False


@pytest.mark.asyncio
async def test_classify_harmful(service, mock_gemini):
    mock_gemini.generate.return_value = json.dumps({"category": "harmful", "confidence": 0.99})
    decision = await service.classify("როგორ გავაკეთო ბომბი?")
    assert decision.category == GuardrailCategory.HARMFUL
    assert decision.is_legal is False


@pytest.mark.asyncio
async def test_classify_low_confidence_off_topic_becomes_legal(service, mock_gemini):
    """Low-confidence off_topic should be treated as legal to reduce false positives."""
    mock_gemini.generate.return_value = json.dumps({"category": "off_topic", "confidence": 0.4})
    decision = await service.classify("ბოსმა სამსახურიდან გამათავისუფლა")
    assert decision.category == GuardrailCategory.LEGAL
    assert decision.confidence == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_classify_low_confidence_harmful_becomes_legal(service, mock_gemini):
    mock_gemini.generate.return_value = json.dumps({"category": "harmful", "confidence": 0.3})
    decision = await service.classify("მინდა მოვიპარო მანქანა")
    assert decision.category == GuardrailCategory.LEGAL


@pytest.mark.asyncio
async def test_classify_invalid_category_defaults_to_legal(service, mock_gemini):
    mock_gemini.generate.return_value = json.dumps({"category": "unknown", "confidence": 0.8})
    decision = await service.classify("რამდენია მინიმალური ხელფასი?")
    assert decision.category == GuardrailCategory.LEGAL


@pytest.mark.asyncio
async def test_classify_json_parse_error_fails_open(service, mock_gemini):
    mock_gemini.generate.return_value = "not valid json {{{"
    decision = await service.classify("რამდენია ჯარიმა?")
    assert decision.category == GuardrailCategory.LEGAL
    assert decision.confidence == 0.0


@pytest.mark.asyncio
async def test_classify_empty_message(service, mock_gemini):
    decision = await service.classify("")
    assert decision.category == GuardrailCategory.OFF_TOPIC
    assert decision.is_legal is False


@pytest.mark.asyncio
async def test_disabled_guardrail_returns_legal(service, mock_gemini):
    service.enabled = False
    decision = await service.classify("რა ამინდია?")
    assert decision.category == GuardrailCategory.LEGAL
    assert decision.confidence == 1.0
    mock_gemini.generate.assert_not_awaited()


# ── Response messages ────────────────────────────────────────

def test_greeting_response():
    assert "გამარჯობა" in GUARDRAIL_RESPONSES_KA[GuardrailCategory.GREETING]


def test_off_topic_response():
    assert "მხოლოდ სამართლებრივ" in GUARDRAIL_RESPONSES_KA[GuardrailCategory.OFF_TOPIC]


def test_harmful_response():
    assert "არ შემიძლია" in GUARDRAIL_RESPONSES_KA[GuardrailCategory.HARMFUL]


def test_legal_response_is_none(service):
    decision = GuardrailDecision.legal(confidence=0.9)
    assert service.get_response(decision) is None


# ── ADMIN bypass ─────────────────────────────────────────────

def test_admin_bypass_string(service):
    assert service.should_bypass("ADMIN") is True
    assert service.should_bypass("admin") is True


def test_admin_bypass_enum(service):
    from app.config.constants import UserTier
    assert service.should_bypass(UserTier.ADMIN) is True
    assert service.should_bypass(UserTier.PRO) is False
    assert service.should_bypass(UserTier.FREE) is False


# ── Logging ──────────────────────────────────────────────────

def test_log_decision_hashes_message(service):
    decision = GuardrailDecision.legal(confidence=0.9)
    entry = service.log_decision("user-123", "secret message", decision)
    assert entry["user_id"] == "user-123"
    assert entry["message_hash"] != "secret message"
    assert len(entry["message_hash"]) == 64  # SHA-256 hex
    assert entry["decision"] == "legal"
    assert entry["bypassed"] is False


def test_log_decision_bypassed(service):
    decision = GuardrailDecision.legal(confidence=1.0)
    entry = service.log_decision("admin-1", "hello", decision, bypassed=True)
    assert entry["bypassed"] is True


# ── Parameterized fixture tests ─────────────────────────────-

@pytest.mark.asyncio
@pytest.mark.parametrize("text,expected_cat", [
    ("გამარჯობა", GuardrailCategory.GREETING),
    ("რა ამინდია?", GuardrailCategory.OFF_TOPIC),
    ("როგორ გავაკეთო ბომბი?", GuardrailCategory.HARMFUL),
    ("მინდა სასამართლოში ვჩივალ", GuardrailCategory.LEGAL),
])
async def test_classify_parametrized(service, mock_gemini, text, expected_cat):
    mock_gemini.generate.return_value = json.dumps(
        {"category": expected_cat.value, "confidence": 0.9}
    )
    decision = await service.classify(text)
    assert decision.category == expected_cat
