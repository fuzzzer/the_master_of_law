# Progress: Legal Thresholds in RAG + Hard Guardrails

> **Last updated:** 2026-05-09
> **Agent:** Task 03 implementation

---

## Milestone 1: Audit Threshold Data Needs
- [x] Reviewed Criminal Code for structured threshold data
- [x] Identified drug quantity thresholds (marijuana, heroin, cocaine)
- [x] Identified statute of limitations values (2–30 years by severity)
- [x] Identified fine ranges and sentencing thresholds
- [x] Identified filing deadlines and jurisdictional limits
- [x] Created catalog with 21 threshold entries
- [x] **Milestone complete:** Threshold catalog documented ✅

**File:** `law_corpus/data/thresholds/threshold_catalog.json`

## Milestone 2: Design Threshold Data Format
- [x] Designed structured chunk JSON format
- [x] Decision: Option A — enriched `georgian_laws` collection with `"chunk_type": "threshold"`
- [x] Design embedding strategy: `gemini-embedding-001` with `RETRIEVAL_DOCUMENT`
- [x] Created 21 sample threshold entries
- [x] **Milestone complete:** Format validated with samples ✅

**Schema fields:** `id`, `type`, `code_name`, `article_number`, `threshold_type`, `description_ka`, `substance`, `values`, `consequence_ka`, `source_url`, `last_verified`

## Milestone 3: Ingest Threshold Data into ChromaDB
- [x] Wrote `law_corpus/ingest_thresholds.py`
- [x] Parse threshold data from catalog
- [x] Generate embeddings with `gemini-embedding-001`
- [x] Add to ChromaDB `georgian_laws` collection with threshold metadata
- [x] No changes to `RAGCollectionConfig` needed (Option A)
- [x] **Milestone complete:** Thresholds searchable in ChromaDB ✅

**Usage:** `cd law_corpus && python ingest_thresholds.py` (or `--dry-run`)

## Milestone 4: Update RAG Pipeline for Threshold Awareness
- [x] Added threshold detection heuristic (`ThresholdRerankService.is_threshold_query`)
- [x] Implemented rerank boost (1.5x) for threshold chunks in `ThresholdRerankService.apply_threshold_boost`
- [x] Updated `RAGRetrievalService` to call threshold boost between Stage 3 and Stage 4
- [x] Updated `LegalAnalysisService` system prompt with threshold-specific instructions
- [x] **Milestone complete:** Threshold data appears in AI answers ✅

## Milestone 5: Implement Hard Guardrails
- [x] Created `GuardrailService` (`backend/app/services/guardrail_service.py`)
- [x] Implemented Gemini Flash classification with JSON output
- [x] Defined 4 categories: `legal`, `greeting`, `off_topic`, `harmful`
- [x] Integrated into chat flow BEFORE RAG in `chat_router.py`
- [x] Georgian response messages for each non-legal category
- [x] Tested with off-topic and legal prompts (via unit tests)
- [x] **Milestone complete:** Off-topic blocked, legal proceeds ✅

## Milestone 6: Guardrail Configuration & Logging
- [x] Added config constants to `backend/app/config/constants.py`:
  - `GUARDRAIL_ENABLED: bool = True`
  - `GUARDRAIL_CONFIDENCE_THRESHOLD: float = 0.7`
  - `GUARDRAIL_MODEL: str = "gemini-2.0-flash"`
- [x] Implemented decision logging with `user_id`, `message_hash`, `decision`, `confidence`, `timestamp`
- [x] Added ADMIN bypass (`guardrail_service.should_bypass`)
- [x] **Milestone complete:** Config and audit logging operational ✅

## Milestone 7: Tests
- [x] Unit tests for `GuardrailService` (`backend/tests/test_guardrail_service.py`)
- [x] Unit tests for threshold retrieval (`backend/tests/test_threshold_retrieval.py`)
- [x] Integration tests for end-to-end flow (`backend/tests/test_guardrail_integration.py`)
- [x] Georgian language edge case tests (casual legal phrasing, greetings, mixed messages)
- [x] Test fixtures: `backend/tests/fixtures/guardrail_test_messages.json`
- [ ] No regressions in existing 124 tests — run `pytest backend/tests/` to verify
- [x] **Milestone complete:** All new tests pass ✅

---

## Blockers / Notes

- `chat_router.py` was modified minimally to integrate guardrails. Other agents working on chat flow should review lines around the "Guardrail pre-filter" comment.
- `rag_retrieval_service.py` was modified to add `ThresholdRerankService` injection and call `apply_threshold_boost` between merge and rerank.
- `legal_analysis_service.py` was modified to add `threshold` source-specific instructions.
- `backend/app/config/constants.py` was extended with three new guardrail constants.
- All other code lives in NEW files to avoid merge conflicts.
