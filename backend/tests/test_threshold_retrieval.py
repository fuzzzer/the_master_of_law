"""
Unit tests for threshold detection and reranking.
"""

from __future__ import annotations

import pytest

from app.services.threshold_rerank_service import ThresholdRerankService


# ── Threshold query detection ────────────────────────────────

@pytest.mark.parametrize("query,expected", [
    ("რამდენია ჯარიმა სიჩქარის გადაჭარბებისთვის?", True),
    ("მარიხუანას 100 გრამი აღმომიჩინეს", True),
    ("10,000 ლარიანი ზარალი", True),
    ("0.5 პრომილი ალკოჰოლი", True),
    ("3 წლის ვადა", True),
    ("20 დღის ვადა საჩივრისთვის", True),
    ("50% განაკვეთი", True),
    ("ბოსმა სამსახურიდან გამათავისუფლა", False),
    ("გამარჯობა", False),
    ("", False),
    ("რა ამინდია?", False),
    ("5 კგ ჰეროინი", True),
    ("500 ლარი ჯარიმა", True),
])
def test_is_threshold_query(query, expected):
    assert ThresholdRerankService.is_threshold_query(query) is expected


# ── Boost application ────────────────────────────────────────

def test_apply_boost_on_non_threshold_query():
    candidates = [
        {"chunk_id": "c1", "distance": 0.2, "metadata": {"chunk_type": "statute"}},
        {"chunk_id": "c2", "distance": 0.3, "metadata": {"chunk_type": "threshold"}},
    ]
    result = ThresholdRerankService.apply_threshold_boost(candidates, "ჩემი მეზობელი მაწუხებს")
    # No boost applied on non-threshold query
    assert result == candidates


def test_apply_boost_on_threshold_query():
    candidates = [
        {"chunk_id": "c1", "distance": 0.2, "metadata": {"chunk_type": "statute"}},
        {"chunk_id": "c2", "distance": 0.3, "metadata": {"chunk_type": "threshold"}},
        {"chunk_id": "c3", "distance": 0.25, "metadata": {"chunk_type": "threshold"}},
    ]
    result = ThresholdRerankService.apply_threshold_boost(candidates, "რამდენია ჯარიმა?")
    # Threshold chunks should have reduced distance
    c2 = next(r for r in result if r["chunk_id"] == "c2")
    c3 = next(r for r in result if r["chunk_id"] == "c3")
    assert c2["original_distance"] == 0.3
    assert c2["distance"] == pytest.approx(0.3 / 1.5)
    assert c3["original_distance"] == 0.25
    assert c3["distance"] == pytest.approx(0.25 / 1.5)
    assert c2["threshold_boost_applied"] is True


def test_boost_reorders_results():
    """A threshold chunk with worse original distance can outrank a statute after boost."""
    candidates = [
        {"chunk_id": "statute", "distance": 0.15, "metadata": {"chunk_type": "statute"}},
        {"chunk_id": "threshold", "distance": 0.20, "metadata": {"chunk_type": "threshold"}},
    ]
    result = ThresholdRerankService.apply_threshold_boost(candidates, "100 გრამი მარიხუანა")
    # After boost: threshold distance = 0.20 / 1.5 ≈ 0.133, which beats statute 0.15
    assert result[0]["chunk_id"] == "threshold"
    assert result[1]["chunk_id"] == "statute"


def test_apply_boost_empty_candidates():
    assert ThresholdRerankService.apply_threshold_boost([], "რამდენია?") == []


# ── Get threshold chunks ─────────────────────────────────────

def test_get_threshold_chunks():
    candidates = [
        {"chunk_id": "c1", "metadata": {"chunk_type": "statute"}},
        {"chunk_id": "c2", "metadata": {"chunk_type": "threshold"}},
        {"chunk_id": "c3", "metadata": {"chunk_type": "threshold"}},
    ]
    thresholds = ThresholdRerankService.get_threshold_chunks(candidates)
    assert len(thresholds) == 2
    assert {t["chunk_id"] for t in thresholds} == {"c2", "c3"}


def test_get_threshold_chunks_none():
    assert ThresholdRerankService.get_threshold_chunks([]) == []
