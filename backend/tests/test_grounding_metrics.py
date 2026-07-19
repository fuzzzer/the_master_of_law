"""Tests for the grounding metrics aggregation (plan 4.1)."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.grounding_metrics_service import compute_grounding_metrics


def _trace(steps: list[dict], response: str = "") -> SimpleNamespace:
    return SimpleNamespace(steps=steps, response_text=response)


class TestComputeGroundingMetrics:
    def test_empty(self):
        m = compute_grounding_metrics([])
        assert m["traces_analyzed"] == 0
        assert m["statute_grounding"]["rate"] is None

    def test_grounded_and_clean_trace(self):
        t = _trace(
            steps=[
                {"step": "rag_final_selection",
                 "data": {"chunks": [{"collection": "georgian_laws"}]}},
                {"step": "citation_verification",
                 "data": {"extracted": [{"a": 1}], "not_found": []}},
                {"step": "anchoring_check",
                 "data": {"claim_paragraphs": 4, "unanchored": 1}},
            ],
            response="მიმართეთ სასამართლოს 30 დღის ვადაში",
        )
        m = compute_grounding_metrics([t])
        assert m["statute_grounding"]["rate"] == 1.0
        assert m["citation_verification"]["rate"] == 1.0
        assert m["deadline_coverage"]["rate"] == 1.0
        assert m["anchoring"]["unanchored_rate"] == 0.25

    def test_ungrounded_trace_counted(self):
        t = _trace(
            steps=[
                {"step": "rag_final_selection",
                 "data": {"chunks": [{"collection": "court_practice"}]}},
            ],
        )
        m = compute_grounding_metrics([t])
        assert m["statute_grounding"]["rate"] == 0.0

    def test_tool_grounding_counts(self):
        t = _trace(
            steps=[
                {"step": "rag_final_selection", "data": {"chunks": []}},
                {"step": "tool_executed",
                 "data": {"tool": "get_article", "result": {"found": True}}},
            ],
        )
        m = compute_grounding_metrics([t])
        assert m["statute_grounding"]["rate"] == 1.0
