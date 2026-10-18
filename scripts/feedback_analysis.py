#!/usr/bin/env python3
"""
feedback_analysis.py — Analyze feedback from the database and generate improvement priorities.

Reads all feedback, groups by category, identifies the 5 weakest areas,
and outputs a prioritized improvement plan.

Usage:
    # Against the API (dev mode):
    python scripts/feedback_analysis.py

    # With custom API URL:
    python scripts/feedback_analysis.py --api-url http://production-server:8000
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError


def fetch_summary(api_url: str) -> dict:
    """Fetch the feedback summary from the admin endpoint."""
    url = f"{api_url}/api/v1/feedback/summary"
    req = Request(url, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        print(f"ERROR: Could not connect to API at {url}")
        print(f"  {e}")
        sys.exit(1)


def analyze_categories(categories: dict) -> list[dict]:
    """Rank categories by average rating (worst first)."""
    ranked = []
    for name, stats in categories.items():
        ranked.append({
            "category": name,
            "avg_rating": stats["avg"],
            "feedback_count": stats["count"],
            "severity": categorize_severity(stats["avg"]),
        })
    ranked.sort(key=lambda x: x["avg_rating"])
    return ranked


def categorize_severity(avg: float) -> str:
    if avg < 2.0:
        return "CRITICAL"
    elif avg < 3.0:
        return "HIGH"
    elif avg < 3.5:
        return "MEDIUM"
    elif avg < 4.0:
        return "LOW"
    return "OK"


IMPROVEMENT_SUGGESTIONS = {
    "accuracy": [
        "Review RAG retrieval relevance — are the right articles being found?",
        "Check Gemini prompt for hallucination patterns",
        "Add more eval test cases focused on factual accuracy",
    ],
    "completeness": [
        "Increase RAG_RERANK_TOP_K to include more context",
        "Check if relevant articles are being filtered out during merge",
        "Add multi-collection cross-referencing for comprehensive answers",
    ],
    "relevance": [
        "Tune query expansion prompts for better Georgian legal terminology",
        "Review embedding quality for domain-specific terms",
        "Add guardrail check for off-topic responses",
    ],
    "formatting": [
        "Review system prompt formatting instructions",
        "Add structured output templates for common response types",
        "Test Georgian text rendering across different displays",
    ],
    "citation_quality": [
        "Validate citation extraction regex against corpus",
        "Cross-reference cited articles with actual corpus chunks",
        "Add citation verification step after generation",
    ],
    "legal_reasoning": [
        "Enhance source-specific prompt injection for court practice",
        "Add Grand Chamber binding decision priority rules",
        "Increase context window for complex multi-article analysis",
    ],
    "overall": [
        "Run full eval pipeline and compare with previous baseline",
        "Review the 5 worst-scoring case files in detail",
        "Conduct a manual review session with legal expert",
    ],
}


def generate_improvement_plan(ranked: list[dict]) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  FEEDBACK ANALYSIS — IMPROVEMENT PRIORITIES")
    lines.append("=" * 60)
    lines.append("")

    top5 = ranked[:5]
    for i, item in enumerate(top5, 1):
        cat = item["category"]
        lines.append(f"  #{i}  {cat.upper()}")
        lines.append(f"      Avg Rating: {item['avg_rating']:.1f}/5  |  Feedback Count: {item['feedback_count']}  |  Severity: {item['severity']}")
        suggestions = IMPROVEMENT_SUGGESTIONS.get(cat, ["No specific suggestions available"])
        for s in suggestions:
            lines.append(f"      → {s}")
        lines.append("")

    lines.append("-" * 60)

    ok_items = [r for r in ranked if r["severity"] == "OK"]
    if ok_items:
        lines.append(f"  ✓ Performing well: {', '.join(r['category'] for r in ok_items)}")
    lines.append("")

    return "\n".join(lines)


def generate_eval_suggestions(ranked: list[dict]) -> str:
    lines = []
    lines.append("SUGGESTED NEW EVAL TEST CASES:")
    lines.append("")

    for item in ranked[:3]:
        cat = item["category"]
        if item["severity"] in ("CRITICAL", "HIGH"):
            lines.append(f"  [{cat}] — Add 5 focused test cases targeting {cat}")
        elif item["severity"] == "MEDIUM":
            lines.append(f"  [{cat}] — Add 3 test cases for edge cases in {cat}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze feedback and generate improvement priorities")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API URL")
    args = parser.parse_args()

    print(f"Fetching feedback summary from {args.api_url}...")
    summary = fetch_summary(args.api_url)

    total = summary.get("total_feedback", 0)
    if total == 0:
        print("No feedback found. Submit feedback first via POST /api/v1/feedback")
        sys.exit(0)

    print(f"Total feedback entries: {total}")
    print()

    categories = summary.get("categories", {})
    ranked = analyze_categories(categories)

    plan = generate_improvement_plan(ranked)
    print(plan)

    eval_suggestions = generate_eval_suggestions(ranked)
    print(eval_suggestions)

    worst = summary.get("worst_cases", [])
    if worst:
        print()
        print("WORST-PERFORMING TARGETS:")
        for w in worst[:5]:
            print(f"  {w['target_type']}:{w['target_id']}  avg={w['avg_rating']:.1f}  count={w['feedback_count']}")

    print()
    print("Done. Use these priorities to guide the next improvement cycle.")


if __name__ == "__main__":
    main()
