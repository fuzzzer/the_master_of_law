# Progress: Legal Thresholds in RAG + Hard Guardrails

> **Last updated:** 2026-05-09
> **Agent:** Antigravity (Claude Opus 4.6)

---

## Milestone 1: Audit Threshold Data Needs
- [x] Review Criminal Code for structured threshold data
- [x] Identify drug quantity thresholds
- [x] Identify statute of limitations values
- [x] Identify fine ranges and sentencing thresholds
- [x] Identify filing deadlines and jurisdictional limits
- [x] Create catalog with at least 20 threshold entries (21 entries)
- [x] **Milestone complete:** Threshold catalog documented ✅

## Milestone 2: Design Threshold Data Format
- [x] Design structured chunk JSON format
- [x] Decide storage: enriched `georgian_laws` (Option A selected)
- [x] Design embedding strategy for threshold chunks
- [x] Create 5 sample threshold entries (21 total)
- [x] **Milestone complete:** Format validated with samples ✅

## Milestone 3: Ingest Threshold Data into ChromaDB
- [x] Write `law_corpus/ingest_thresholds.py`
- [x] Parse threshold data from catalog
- [x] Generate embeddings with `gemini-embedding-001`
- [x] Add to ChromaDB (enriched chunks in `georgian_laws`)
- [x] No `RAGCollectionConfig` changes needed (Option A)
- [x] Verify vector search retrieves threshold chunks
- [x] **Milestone complete:** Thresholds searchable in ChromaDB ✅

## Milestone 4: Update RAG Pipeline for Threshold Awareness
- [x] Add threshold detection heuristic (keyword + numeric detection)
- [x] Implement rerank boost for threshold chunks (1.5x distance reduction)
- [x] Update system prompt for exact threshold usage
- [x] Test with quantity-related queries
- [x] **Milestone complete:** Threshold data appears in AI answers ✅

## Milestone 5: Implement Hard Guardrails
- [x] Create `GuardrailService` (`backend/app/services/guardrail_service.py`)
- [x] Implement Gemini Flash classification
- [x] Define classification categories and prompts (`backend/app/prompts/guardrail.py`)
- [x] Integrate into chat flow before RAG (both HTTP and WebSocket)
- [x] Add Georgian response messages
- [x] Test with off-topic and legal prompts
- [x] **Milestone complete:** Off-topic blocked, legal proceeds ✅

## Milestone 6: Guardrail Configuration & Logging
- [x] Add config constants (enabled, threshold, model) to `constants.py`
- [x] Implement decision logging (SHA-256 message hash for privacy)
- [x] Add ADMIN bypass (skips classification entirely)
- [x] Verify logging for 10 test messages
- [x] **Milestone complete:** Config and audit logging operational ✅

## Milestone 7: Tests
- [x] Unit tests for `GuardrailService` (14 tests)
- [x] Unit tests for threshold retrieval (11 tests)
- [x] Integration tests for end-to-end flow (prompt registry)
- [x] Georgian language edge case tests (fixture-based)
- [x] No regressions in existing tests (149 total pass)
- [x] **Milestone complete:** All tests pass ✅

---

## Blockers / Notes

_All milestones completed. 149 tests pass (0 regressions)._

### Files Created
- `law_corpus/ingest_thresholds.py` — Threshold ingestion script
- `backend/app/services/guardrail_service.py` — Guardrail classification service
- `backend/app/prompts/guardrail.py` — Guardrail classification prompt
- `backend/tests/test_guardrail_service.py` — 14 guardrail tests
- `backend/tests/test_threshold_service.py` — 11 threshold tests
- `backend/tests/fixtures/guardrail_test_messages.json` — 20 test messages

### Files Modified
- `backend/app/config/constants.py` — Added guardrail config constants
- `backend/app/prompts/registry.py` — Registered guardrail prompt
- `backend/app/services/rag_retrieval_service.py` — Added threshold boost
- `backend/app/services/legal_analysis_service.py` — Added threshold system prompt
- `backend/app/routes/chat_router.py` — Integrated guardrail pre-filter
- `backend/app/routes/ws_chat_router.py` — Integrated guardrail pre-filter
- `backend/tests/test_prompts.py` — Updated prompt count
- `backend/tests/test_config.py` — Fixed pre-existing phase count bug
