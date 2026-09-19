"""
Tests for progress_service — the user-facing projection of pipeline steps.

The contract worth protecting is not "a message appears". It is:
  - stages only ever move FORWARD (a progress bar that goes backwards is
    worse than none),
  - the vocabulary stays in sync with the steps the pipeline actually emits,
  - and a broken sink can never take a user's request down with it.
"""

import sys

sys.path.insert(0, ".")

import pytest

from app.services.progress_service import (
    STAGES,
    _STEP_TO_STAGE,
    clear_progress_sink,
    emit_progress,
    set_progress_sink,
)


@pytest.fixture
def frames():
    got: list[dict] = []
    set_progress_sink(got.append)
    yield got
    clear_progress_sink()


class TestStageVocabulary:
    def test_stage_keys_are_unique(self):
        keys = [s.key for s in STAGES]
        assert len(keys) == len(set(keys))

    def test_every_mapped_step_points_at_a_real_stage(self):
        known = {s.key for s in STAGES}
        unknown = {v for v in _STEP_TO_STAGE.values()} - known
        assert not unknown, f"steps mapped to non-existent stages: {unknown}"

    def test_indexes_only_move_forward_through_the_pipeline(self):
        """The declared order IS the progress order, so a real request's steps
        must produce non-decreasing indexes."""
        order = {s.key: i for i, s in enumerate(STAGES)}
        # A full run, in the order agent_pipeline_service actually emits them.
        real_run = [
            "guardrail_decision", "phase_1_plan", "rag_vector_search",
            "rag_rerank", "rag_final_selection", "full_code_injected",
            "llm_generation_request", "llm_response", "citation_verification",
            "retrieval_repair", "citation_correction", "faithfulness_check",
            "anchoring_check", "anchoring_repair", "practice_attribution_guard",
        ]
        seen = [order[_STEP_TO_STAGE[s]] for s in real_run if s in _STEP_TO_STAGE]
        assert seen == sorted(seen), f"stage order regresses: {seen}"


class TestEmission:
    def test_unmapped_steps_are_silent(self, frames):
        emit_progress("request_received", {})
        emit_progress("rag_query_expansion", {})
        emit_progress("pipeline_result", {})
        assert frames == []

    def test_repeated_stage_without_new_detail_is_deduped(self, frames):
        emit_progress("rag_vector_search", {})
        emit_progress("rag_fulltext_search", {})
        emit_progress("rag_merge_dedup", {})
        assert len(frames) == 1, "three search steps must read as one stage"
        assert frames[0]["key"] == "search"

    def test_same_stage_re_fires_when_it_has_new_substance(self, frames):
        emit_progress("rag_rerank", {})
        emit_progress("rag_final_selection", {"result_count": 23})
        assert len(frames) == 2
        assert frames[1]["detail"] == "ნაპოვნია 23 მუხლი"

    def test_frame_carries_position_for_a_progress_indicator(self, frames):
        emit_progress("llm_generation_request", {})
        f = frames[0]
        assert f["type"] == "stage"
        assert f["key"] == "draft"
        assert f["total"] == len(STAGES)
        assert 0 <= f["index"] < f["total"]
        assert f["label"] and f["label_en"]

    def test_tool_calls_name_the_actual_tool(self, frames):
        emit_progress("tool_executed", {"tool": "add_fact"})
        assert frames[0]["key"] == "tools"
        assert frames[0]["detail"] == "ფაქტი დაემატა"

    def test_no_sink_installed_is_a_no_op(self):
        clear_progress_sink()
        emit_progress("llm_response", {})  # must not raise

    def test_a_throwing_sink_cannot_break_the_request(self):
        def boom(_frame):
            raise RuntimeError("client went away")

        set_progress_sink(boom)
        try:
            emit_progress("llm_response", {})  # swallowed, not raised
        finally:
            clear_progress_sink()

    def test_malformed_step_data_does_not_raise(self, frames):
        emit_progress("rag_final_selection", {"result_count": None})
        emit_progress("full_code_injected", {"codes": "not-a-list"})
        emit_progress("citation_verification", {"extracted": None})
        # No exception is the assertion; frames may or may not carry detail.


class TestRecordStepIntegration:
    def test_record_step_reports_progress_even_with_tracing_off(self, frames):
        """Progress and tracing are independent — a user watching a spinner
        should still see stages when TRACE_ENABLED is false."""
        from app.services.trace_service import record_step

        record_step("llm_generation_request", model="test-model")
        assert frames and frames[0]["key"] == "draft"


class TestMonotonicPosition:
    """The pipeline loops; the progress bar must not.

    verify -> repair -> verify runs up to twice, so the raw stage index really
    does go backwards. Observed live at 9/10 -> 8/10 before this was fixed.
    """

    def test_a_verify_loop_does_not_rewind_the_bar(self, frames):
        emit_progress("citation_verification", {"extracted": ["a", "b"]})
        emit_progress("retrieval_repair", {"repaired": ["a", "b"]})
        emit_progress("citation_verification", {"extracted": ["a", "b"]})  # loop
        indexes = [f["index"] for f in frames]
        assert indexes == sorted(indexes), f"progress went backwards: {indexes}"

    def test_the_label_still_tells_the_truth_while_looping(self, frames):
        emit_progress("retrieval_repair", {"repaired": ["a"]})
        emit_progress("citation_verification", {"extracted": ["a"]})
        # Position holds at the furthest point reached...
        assert frames[-1]["index"] == frames[-2]["index"]
        # ...but the user is told what is ACTUALLY happening now.
        assert frames[-1]["key"] == "verify"

    def test_high_water_resets_between_requests(self, frames):
        emit_progress("practice_attribution_guard", {})
        high = frames[-1]["index"]
        clear_progress_sink()

        fresh: list[dict] = []
        set_progress_sink(fresh.append)
        emit_progress("guardrail_decision", {})
        clear_progress_sink()
        assert fresh[0]["index"] < high, "a new request must start from the top"
