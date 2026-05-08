"""
Integration tests for guardrail + threshold end-to-end flow.

These tests exercise the full pipeline with mocked external services.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.guardrail_schema import GuardrailCategory, GuardrailDecision
from app.services.guardrail_service import GuardrailService
from app.services.threshold_rerank_service import ThresholdRerankService


@pytest.fixture
def mock_gemini():
    gemini = MagicMock()
    gemini.generate = AsyncMock()
    return gemini


# ── End-to-end guardrail flow ────────────────────────────────

@pytest.mark.asyncio
async def test_guardrail_blocks_harmful(mock_gemini):
    service = GuardrailService(gemini_client=mock_gemini, enabled=True)
    mock_gemini.generate.return_value = json.dumps({"category": "harmful", "confidence": 0.95})
    decision = await service.classify("როგორ გავაკეთო ბომბი სახლის პირობებში?")
    assert decision.category == GuardrailCategory.HARMFUL
    response = service.get_response(decision)
    assert response is not None
    assert "არ შემიძლია" in response


@pytest.mark.asyncio
async def test_guardrail_redirects_off_topic(mock_gemini):
    service = GuardrailService(gemini_client=mock_gemini, enabled=True)
    mock_gemini.generate.return_value = json.dumps({"category": "off_topic", "confidence": 0.90})
    decision = await service.classify("რომელი გუნდი მოიგო ევრო 2024-ზე?")
    assert decision.category == GuardrailCategory.OFF_TOPIC
    response = service.get_response(decision)
    assert response is not None
    assert "მხოლოდ სამართლებრივ" in response


@pytest.mark.asyncio
async def test_guardrail_greeting_then_legal(mock_gemini):
    service = GuardrailService(gemini_client=mock_gemini, enabled=True)
    # Pure greeting
    mock_gemini.generate.return_value = json.dumps({"category": "greeting", "confidence": 0.95})
    decision = await service.classify("გამარჯობა")
    assert decision.category == GuardrailCategory.GREETING
    response = service.get_response(decision)
    assert "გამარჯობა" in response
    assert "კანონის ოსტატი" in response


@pytest.mark.asyncio
async def test_guardrail_allows_legal(mock_gemini):
    service = GuardrailService(gemini_client=mock_gemini, enabled=True)
    mock_gemini.generate.return_value = json.dumps({"category": "legal", "confidence": 0.92})
    decision = await service.classify("დამსაქმებელმა ხელშეკრულება ვადამდე შემიწყვიტა")
    assert decision.category == GuardrailCategory.LEGAL
    assert decision.is_legal is True
    assert service.get_response(decision) is None


def test_guardrail_admin_bypass(mock_gemini):
    service = GuardrailService(gemini_client=mock_gemini, enabled=True)
    # Bypass is a pure helper — no Gemini call needed.
    assert service.should_bypass("ADMIN") is True
    assert service.should_bypass("admin") is True
    assert service.should_bypass("PRO") is False


# ── Threshold + RAG integration ──────────────────────────────

def test_threshold_boost_with_realistic_candidates():
    """Simulate a RAG candidate list with mixed statute and threshold chunks."""
    candidates = [
        {
            "chunk_id": "statute_260",
            "distance": 0.18,
            "metadata": {"chunk_type": "statute", "code_name": "სისხლის სამართლის კოდექსი", "article_number": "მუხლი 260"},
            "content": "ნარკოტიკული საშუალების უკანონო ბრუნვა...",
        },
        {
            "chunk_id": "threshold_marijuana",
            "distance": 0.28,
            "metadata": {"chunk_type": "threshold", "threshold_type": "drug_quantity", "substance": "მარიხუანა"},
            "content": "სამართლებრივი ზღვარი: ნარკოტიკული საშუალების უკანონო ბრუნვის ოდენობები — მარიხუანა...",
        },
        {
            "chunk_id": "statute_273",
            "distance": 0.22,
            "metadata": {"chunk_type": "statute", "code_name": "სისხლის სამართლის კოდექსი", "article_number": "მუხლი 273"},
            "content": "ადმინისტრაციული პასუხისმგებლობა...",
        },
    ]

    # Non-threshold query — no boost
    result_no_boost = ThresholdRerankService.apply_threshold_boost(
        candidates, "ნარკოტიკული საშუალების ბრუნვა"
    )
    assert result_no_boost[0]["chunk_id"] == "statute_260"  # lowest distance

    # Threshold query — boost applied, threshold_marijuana should outrank statute_273
    result_boost = ThresholdRerankService.apply_threshold_boost(
        candidates, "მარიხუანას 100 გრამი რა შედეგი აქვს?"
    )
    # After boost: threshold distance = 0.28 / 1.5 ≈ 0.187
    # statute_260 = 0.18, statute_273 = 0.22
    # Order should be: statute_260 (0.18), threshold_marijuana (~0.187), statute_273 (0.22)
    ids = [r["chunk_id"] for r in result_boost]
    assert ids[0] == "statute_260"
    assert ids[1] == "threshold_marijuana"
    assert ids[2] == "statute_273"


# ── Fixture-based batch test ─────────────────────────────────

@pytest.mark.asyncio
async def test_guardrail_fixture_batch(mock_gemini):
    """Run all fixture messages through guardrail with expected outputs."""
    import pathlib

    fixture_path = pathlib.Path(__file__).with_name("fixtures") / "guardrail_test_messages.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    service = GuardrailService(gemini_client=mock_gemini, enabled=True)

    legal_count = 0
    for item in messages:
        expected = item["expected"]
        mock_gemini.generate.return_value = json.dumps(
            {"category": expected, "confidence": 0.9}
        )
        decision = await service.classify(item["text"])
        assert decision.category.value == expected, (
            f"Failed for text: {item['text'][:50]}... expected {expected}, got {decision.category.value}"
        )
        if decision.is_legal:
            legal_count += 1

    # 10 legal + low-confidence auto-promoted = at least 10 legal
    assert legal_count >= 10
