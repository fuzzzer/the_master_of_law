# Stabilization — Progress Tracker

> **Last updated:** 2026-05-23
> **Status:** Not started

---

## Milestone 1: Fix Pre-Existing Failures
- [ ] Fix `test_config.py::TestRAGConstants::test_values` (50 → 75)
- [ ] Exclude `test_scratch.py` from collection
- [ ] Exclude `tests/scripts/` from collection
- [ ] ✅ Milestone 1 complete — 0 pre-existing failures

## Milestone 2: Test Infrastructure
- [ ] Create `tests/conftest.py` with shared fixtures
- [ ] Configure `pyproject.toml` test exclusions
- [ ] Verify existing tests still pass with new conftest
- [ ] ✅ Milestone 2 complete — infrastructure ready

## Milestone 3: Rate Limiting Tests
- [ ] Create `tests/test_rate_limit_middleware.py`
- [ ] Within-limit tests for all tiers
- [ ] Exceed-limit → 429 tests
- [ ] Window reset test
- [ ] Public path bypass test
- [ ] ✅ Milestone 3 complete — rate limiting tested

## Milestone 4: API Key & Auth Tests
- [ ] Create `tests/test_api_key_auth.py`
- [ ] API key generation/validation tests
- [ ] API key router endpoint tests
- [ ] Auth middleware path tests (public, dev, API key, admin key)
- [ ] ✅ Milestone 4 complete — auth tested

## Milestone 5: Conversation State Machine Tests
- [ ] Create `tests/test_conversation_service.py`
- [ ] UUID parsing edge cases
- [ ] Phase transition validity tests
- [ ] determine_next_phase for all phases
- [ ] CRUD operations (create, get, delete, save messages)
- [ ] History truncation test
- [ ] ✅ Milestone 5 complete — state machine tested

## Milestone 6: RAG Pipeline Tests
- [ ] Create `tests/test_rag_retrieval_service.py`
- [ ] Stage 0 (query expansion) tests
- [ ] Stage 1 (vector search) tests
- [ ] Stage 2 (fulltext search) tests
- [ ] Stage 3 (merge/dedup) tests
- [ ] Full pipeline integration test
- [ ] Quota enforcement test
- [ ] search_law tests
- [ ] ✅ Milestone 6 complete — RAG tested

## Milestone 7: Legal Analysis & Formatting Tests
- [ ] Create `tests/test_legal_analysis_service.py`
- [ ] LawContextFormatter tests (all source types)
- [ ] ConversationHistoryFormatter tests
- [ ] System prompt building tests (source-specific injection)
- [ ] User prompt building tests
- [ ] ✅ Milestone 7 complete — legal analysis tested

## Milestone 8: Agent Pipeline Tests
- [ ] Create `tests/test_agent_pipeline_service.py`
- [ ] _history_to_contents tests
- [ ] _format_law_context tests
- [ ] _select_tools tests
- [ ] Phase 1 (planning) tests
- [ ] Phase 2 (execute with tools) tests
- [ ] Phase 3 (verification) tests
- [ ] Full `run()` integration tests
- [ ] ✅ Milestone 8 complete — agent pipeline tested

## Milestone 9: Case Builder & Document Generator Tests
- [ ] Create `tests/test_case_builder_service.py`
- [ ] Create `tests/test_document_generator_service.py`
- [ ] CaseFileRenderer tests
- [ ] Case builder helper tests
- [ ] DOCX generation tests
- [ ] ✅ Milestone 9 complete — case builder/doc gen tested

## Milestone 10: Complex User Flow Tests
- [ ] Create `tests/test_complex_flows.py`
- [ ] Flow: Conversation lifecycle (phase transitions end-to-end)
- [ ] Flow: RAG → Analysis → Citation Verification
- [ ] Flow: Agent pipeline with tool calls
- [ ] Flow: Case builder end-to-end
- [ ] Flow: WebSocket authentication paths
- [ ] ✅ Milestone 10 complete — flows tested

## Milestone 11: Final Verification
- [ ] Full suite: `pytest tests/ --ignore=tests/scripts -v`
- [ ] Total tests ≥ 300
- [ ] 0 failures, 0 errors
- [ ] ✅ Milestone 11 complete — stabilization done

---

## Blockers

_None yet._
