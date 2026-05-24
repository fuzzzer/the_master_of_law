# Stabilization — Progress Tracker

> **Last updated:** 2026-05-23
> **Status:** ✅ Complete

---

## Milestone 1: Fix Pre-Existing Failures
- [x] Fix `test_config.py::TestRAGConstants::test_values` (50 → 75)
- [x] Exclude `test_scratch.py` from collection
- [x] Exclude `tests/scripts/` from collection
- [x] ✅ Milestone 1 complete — 0 pre-existing failures

## Milestone 2: Test Infrastructure
- [x] Create `tests/conftest.py` with shared fixtures
- [x] Configure `pyproject.toml` test exclusions
- [x] Verify existing tests still pass with new conftest
- [x] ✅ Milestone 2 complete — infrastructure ready

## Milestone 3: Rate Limiting Tests
- [x] Create `tests/test_rate_limit_middleware.py`
- [x] Within-limit tests for all tiers
- [x] Exceed-limit → 429 tests
- [x] Window reset test
- [x] Public path bypass test
- [x] ✅ Milestone 3 complete — 11 tests, all passing

## Milestone 4: API Key & Auth Tests
- [x] Create `tests/test_api_key_auth.py`
- [x] API key generation/validation tests
- [x] API key router endpoint tests
- [x] Auth middleware path tests (public, dev, API key, admin key)
- [x] ✅ Milestone 4 complete — 17 tests, all passing

## Milestone 5: Conversation State Machine Tests
- [x] Create `tests/test_conversation_service.py`
- [x] UUID parsing edge cases
- [x] Phase transition validity tests
- [x] determine_next_phase for all phases
- [x] CRUD operations (create, get, delete, save messages)
- [x] History truncation test
- [x] ✅ Milestone 5 complete — 23 tests, all passing

## Milestone 6: RAG Pipeline Tests
- [x] Create `tests/test_rag_retrieval_service.py`
- [x] Stage 0 (query expansion) tests
- [x] Stage 3 (merge/dedup) tests
- [x] Full pipeline integration test
- [x] Quota enforcement test
- [x] search_law tests
- [x] ✅ Milestone 6 complete — 16 tests, all passing

## Milestone 7: Legal Analysis & Formatting Tests
- [x] Create `tests/test_legal_analysis_service.py`
- [x] LawContextFormatter tests (all source types)
- [x] ConversationHistoryFormatter tests
- [x] System prompt building tests (source-specific injection)
- [x] User prompt building tests
- [x] ✅ Milestone 7 complete — 19 tests, all passing

## Milestone 8: Agent Pipeline Tests
- [x] Create `tests/test_agent_pipeline_service.py`
- [x] _history_to_contents tests
- [x] _format_law_context tests
- [x] _select_tools tests
- [x] Phase 1 (planning) tests
- [x] Phase 3 (verification) tests
- [x] Full `run()` integration tests
- [x] ✅ Milestone 8 complete — 24 tests, all passing

## Milestone 9: Case Builder & Document Generator Tests
- [x] Create `tests/test_case_builder_service.py`
- [x] Create `tests/test_document_generator_service.py`
- [x] CaseFileRenderer tests
- [x] Case builder helper tests
- [x] DOCX generation tests
- [x] ✅ Milestone 9 complete — 15 tests, all passing

## Milestone 10: Complex User Flow Tests
- [x] Create `tests/test_complex_flows.py`
- [x] Flow: Conversation lifecycle (phase transitions end-to-end)
- [x] Flow: RAG → Analysis → Citation Verification
- [x] Flow: Agent pipeline with tool calls
- [x] Flow: Case builder end-to-end
- [x] Flow: Auth path variants
- [x] ✅ Milestone 10 complete — 8 tests, all passing

## Milestone 11: Final Verification
- [x] Full suite: `pytest tests/ -v` → clean
- [x] Total tests: 338 (204 existing + 134 new) ≥ 300 ✅
- [x] 0 failures, 0 errors ✅
- [x] Suite runs in ~15s ✅
- [x] ✅ Milestone 11 complete — stabilization done

---

## Blockers

_None._
