"""
Progress Service — turns internal pipeline steps into user-facing stages.

WHY THIS IS DRIVEN OFF record_step: the pipeline ALREADY announces every
stage it enters, for the trace. Adding a second, parallel set of progress
calls would mean two things to keep in sync and one of them would rot — the
usual outcome being a progress bar that describes a pipeline the code no
longer runs. So the trace recorder is the single source of "where are we",
and this module is a projection of it for humans.

The two have different jobs and the mapping is deliberately lossy:

    trace     every step, verbatim data, for reconstructing what happened
    progress  ~10 named stages, deduped, for someone watching a spinner

Usage (WebSocket):
    queue = asyncio.Queue()
    set_progress_sink(queue.put_nowait)
    ...                       # run the pipeline; stages arrive on the queue
    clear_progress_sink()
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Stage:
    """One user-facing stage of the pipeline."""
    key: str
    label_ka: str
    label_en: str


# The ORDER here is the order a user sees, and `index` is derived from it —
# so a stage added in the wrong position produces a progress bar that goes
# backwards. Stages a given request skips (no tools, no repair) simply never
# fire; the client shows position, not a promise that all of them will run.
STAGES: tuple[Stage, ...] = (
    Stage("guard",   "შემოწმება",                    "Checking the question"),
    Stage("plan",    "კითხვის გაანალიზება",          "Working out what to look up"),
    Stage("search",  "კანონების ძიება",              "Searching the law corpus"),
    Stage("rank",    "მუხლების შერჩევა",             "Picking the most relevant articles"),
    Stage("code",    "კოდექსის სრულად ჩატვირთვა",    "Loading the full code"),
    Stage("draft",   "პასუხის მომზადება",            "Drafting the answer"),
    Stage("tools",   "საქმის განახლება",             "Updating your case file"),
    Stage("verify",  "მუხლების გადამოწმება",         "Verifying every citation"),
    Stage("repair",  "წყაროებთან შედარება",          "Re-checking against the source text"),
    Stage("polish",  "საბოლოო შემოწმება",            "Final checks"),
)

_STAGE_BY_KEY = {s.key: (i, s) for i, s in enumerate(STAGES)}

# Internal step name -> stage key. Steps absent from this map are trace-only
# noise (request_received, rag_query_expansion, pipeline_result) and are
# deliberately NOT surfaced: a progress line that changes faster than it can
# be read is worse than one that sits still.
_STEP_TO_STAGE: dict[str, str] = {
    "guardrail_decision": "guard",
    "guardrail_unavailable": "guard",
    "rag_vector_search": "search",
    "rag_fulltext_search": "search",
    "rag_merge_dedup": "search",
    "phase_1_plan": "plan",
    "phase_1_plan_failed": "plan",
    "rag_rerank": "rank",
    "rag_final_selection": "rank",
    "full_code_injected": "code",
    "llm_generation_request": "draft",
    "llm_response": "draft",
    "llm_requested_tools": "tools",
    "tool_executed": "tools",
    "citation_verification": "verify",
    "case_citation_verification": "verify",
    "subarticle_verification": "verify",
    "retrieval_repair": "repair",
    "citation_correction": "repair",
    "faithfulness_check": "polish",
    "faithfulness_correction": "polish",
    "anchoring_check": "polish",
    "anchoring_repair": "polish",
    "practice_attribution_guard": "polish",
    "uncertainty_disclaimer_added": "polish",
    "deadline_guard_added": "polish",
}

_TOOL_LABELS_KA: dict[str, str] = {
    "add_fact": "ფაქტი დაემატა",
    "edit_fact": "ფაქტი განახლდა",
    "add_argument": "არგუმენტი დაემატა",
    "link_article": "მუხლი მიებმა საქმეს",
    "set_strategy": "სტრატეგია განისაზღვრა",
    "add_action_item": "დავალება დაემატა",
    "complete_action_item": "დავალება შესრულდა",
    "add_risk": "რისკი დაფიქსირდა",
    "get_case_summary": "საქმის მიმოხილვა",
    "create_case": "საქმე შეიქმნა",
    "build_case_analysis": "საქმის ანალიზი",
    "search_law": "კანონის ძიება",
    "get_article": "მუხლის ამოღება",
    "browse_code": "კოდექსის დათვალიერება",
}


def _detail_ka(step: str, data: dict[str, Any]) -> str | None:
    """A short, CONCRETE line for stages that have a real number to show.

    Substance beats reassurance: "23 articles found" tells the user the search
    worked, where "searching…" for forty seconds tells them nothing. Only
    values already present in the step data are used — this never computes
    anything, so it cannot become a second source of truth.
    """
    try:
        if step == "rag_final_selection":
            n = data.get("result_count")
            return f"ნაპოვნია {n} მუხლი" if n else None
        if step == "full_code_injected":
            codes = data.get("codes") or []
            arts = sum(c.get("articles", 0) for c in codes if isinstance(c, dict))
            return f"{arts} მუხლი სრულად" if arts else None
        if step == "citation_verification":
            n = len(data.get("extracted") or [])
            return f"{n} მუხლი მოწმდება" if n else None
        if step == "retrieval_repair":
            n = len(data.get("repaired") or [])
            return f"{n} წყარო ზუსტდება" if n else None
        if step == "tool_executed":
            return _TOOL_LABELS_KA.get(str(data.get("tool", "")))
        if step == "llm_requested_tools":
            calls = data.get("calls") or []
            if len(calls) > 1:
                return f"{len(calls)} მოქმედება"
            if calls and isinstance(calls[0], dict):
                return _TOOL_LABELS_KA.get(str(calls[0].get("tool", "")))
    except Exception:  # noqa: BLE001 — progress must never break a request
        return None
    return None


ProgressSink = Callable[[dict], None]

_sink: ContextVar[ProgressSink | None] = ContextVar("progress_sink", default=None)
_last_key: ContextVar[str | None] = ContextVar("progress_last_key", default=None)
_high_water: ContextVar[int] = ContextVar("progress_high_water", default=-1)


def set_progress_sink(sink: ProgressSink) -> None:
    """Install a sink for this request. Must be a NON-blocking callable.

    The pipeline reports progress from synchronous code deep inside itself, so
    the sink cannot be awaited — pass something like ``asyncio.Queue.put_nowait``
    and drain it from the transport.
    """
    _sink.set(sink)
    _last_key.set(None)
    _high_water.set(-1)


def clear_progress_sink() -> None:
    _sink.set(None)
    _last_key.set(None)
    _high_water.set(-1)


def emit_progress(step: str, data: dict[str, Any]) -> None:
    """Project one trace step onto a user-facing stage, if it maps to one."""
    sink = _sink.get()
    if sink is None:
        return

    key = _STEP_TO_STAGE.get(step)
    if key is None:
        return

    index, stage = _STAGE_BY_KEY[key]
    detail = _detail_ka(step, data or {})

    # Dedupe by stage, but let a stage re-fire when it has NEW detail —
    # "23 articles found" after "searching" is worth the second frame, while
    # three consecutive vector-search steps are not.
    if key == _last_key.get() and detail is None:
        return
    _last_key.set(key)

    # The pipeline LOOPS: verify -> repair -> verify runs up to twice, so the
    # raw stage index really does go backwards (observed live, 9/10 -> 8/10).
    # The LABEL follows the work honestly — the user is genuinely back on
    # verification — but the reported POSITION is a high-water mark, because a
    # bar that retreats reads as failure and there is no way for the user to
    # tell a second verification pass from a lost first one.
    high = max(_high_water.get(), index)
    _high_water.set(high)

    try:
        sink({
            "type": "stage",
            "key": stage.key,
            "label": stage.label_ka,
            "label_en": stage.label_en,
            "detail": detail,
            "index": high,
            "total": len(STAGES),
        })
    except Exception as e:  # noqa: BLE001
        logger.warning("progress_emit_failed", step=step, error=str(e))
