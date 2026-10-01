"""
Grounding metrics — nightly-style aggregation over pipeline traces (plan 4.1).

Computes the certification-rubric rates (statute grounding, citation
verification, case attribution, deadline coverage, anchoring) from recorded
traces so grounding drift is visible on the trace dashboard without anyone
asking.
"""

from __future__ import annotations

import re
from typing import Any

_ACTION_RE = re.compile(r"სასამართლო|საჩივ|სარჩელ|გაასაჩივრ|იჩივლ|მიმართ")
_DEADLINE_RE = re.compile(r"ვადა|ვადაში|ვადის|დღის განმავლობაში|გადაამოწმ|დაუყოვნებლ")


def compute_grounding_metrics(traces: list[Any]) -> dict[str, Any]:
    """Aggregate grounding health over completed traces.

    Each rate reports numerator/denominator so a dashboard reader can judge
    sample size, not just the percentage.
    """
    rag_traces = 0
    statute_grounded = 0
    with_citations = 0
    citations_clean = 0
    with_cases = 0
    cases_clean = 0
    action_advised = 0
    action_with_deadline = 0
    claim_paragraphs = 0
    unanchored = 0
    faithfulness_checked = 0
    faithfulness_unsupported = 0
    disclaimers = 0

    for trace in traces:
        steps = {s.get("step"): s.get("data", {}) for s in (trace.steps or [])}
        tool_data = [
            s.get("data", {}) for s in (trace.steps or [])
            if s.get("step") == "tool_executed"
        ]
        if "rag_final_selection" not in steps and "full_code_injected" not in steps:
            continue
        rag_traces += 1

        chunks = steps.get("rag_final_selection", {}).get("chunks", [])
        grounded = (
            any(c.get("collection") == "georgian_laws" for c in chunks)
            or "full_code_injected" in steps
            or any(
                t.get("tool") == "get_article" and t.get("result", {}).get("found")
                for t in tool_data
            )
        )
        statute_grounded += grounded

        cv = steps.get("citation_verification")
        if cv and (cv.get("extracted") or cv.get("verified")):
            with_citations += 1
            citations_clean += not cv.get("not_found")

        ccv = steps.get("case_citation_verification")
        if ccv:
            with_cases += 1
            cases_clean += not ccv.get("not_found")

        response = trace.response_text or ""
        if _ACTION_RE.search(response):
            action_advised += 1
            action_with_deadline += bool(_DEADLINE_RE.search(response))

        anchor = steps.get("anchoring_check")
        if anchor:
            claim_paragraphs += anchor.get("claim_paragraphs", 0)
            unanchored += anchor.get("unanchored", 0)

        fc = steps.get("faithfulness_check")
        if fc and not fc.get("failed"):
            faithfulness_checked += 1
            faithfulness_unsupported += len(fc.get("unsupported") or [])

        if "uncertainty_disclaimer_added" in steps:
            disclaimers += 1

    def rate(num: int, den: int) -> float | None:
        return round(num / den, 3) if den else None

    return {
        "traces_analyzed": len(traces),
        "rag_traces": rag_traces,
        "statute_grounding": {
            "rate": rate(statute_grounded, rag_traces),
            "grounded": statute_grounded,
            "total": rag_traces,
        },
        "citation_verification": {
            "rate": rate(citations_clean, with_citations),
            "clean": citations_clean,
            "with_citations": with_citations,
        },
        "case_attribution": {
            "rate": rate(cases_clean, with_cases),
            "clean": cases_clean,
            "with_cases": with_cases,
        },
        "deadline_coverage": {
            "rate": rate(action_with_deadline, action_advised),
            "with_deadline": action_with_deadline,
            "action_advised": action_advised,
        },
        "anchoring": {
            "unanchored_rate": rate(unanchored, claim_paragraphs),
            "unanchored": unanchored,
            "claim_paragraphs": claim_paragraphs,
        },
        "faithfulness": {
            "checked": faithfulness_checked,
            "unsupported_claims": faithfulness_unsupported,
        },
        "uncertainty_disclaimers": disclaimers,
    }
