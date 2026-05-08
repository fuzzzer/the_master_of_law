# Progress: Legal Thresholds in RAG + Hard Guardrails

> **Last updated:** _not started_
> **Agent:** _unassigned_

---

## Milestone 1: Audit Threshold Data Needs
- [ ] Review Criminal Code for structured threshold data
- [ ] Identify drug quantity thresholds
- [ ] Identify statute of limitations values
- [ ] Identify fine ranges and sentencing thresholds
- [ ] Identify filing deadlines and jurisdictional limits
- [ ] Create catalog with at least 20 threshold entries
- [ ] **Milestone complete:** Threshold catalog documented ✅

## Milestone 2: Design Threshold Data Format
- [ ] Design structured chunk JSON format
- [ ] Decide storage: enriched `georgian_laws` vs. new collection
- [ ] Design embedding strategy for threshold chunks
- [ ] Create 5 sample threshold entries
- [ ] **Milestone complete:** Format validated with samples ✅

## Milestone 3: Ingest Threshold Data into ChromaDB
- [ ] Write `law_corpus/ingest_thresholds.py`
- [ ] Parse threshold data from catalog
- [ ] Generate embeddings with `gemini-embedding-001`
- [ ] Add to ChromaDB
- [ ] Update `RAGCollectionConfig` if needed
- [ ] Verify vector search retrieves threshold chunks
- [ ] **Milestone complete:** Thresholds searchable in ChromaDB ✅

## Milestone 4: Update RAG Pipeline for Threshold Awareness
- [ ] Add threshold detection heuristic
- [ ] Implement rerank boost for threshold chunks
- [ ] Update system prompt for exact threshold usage
- [ ] Test with quantity-related queries
- [ ] **Milestone complete:** Threshold data appears in AI answers ✅

## Milestone 5: Implement Hard Guardrails
- [ ] Create `GuardrailService`
- [ ] Implement Gemini Flash classification
- [ ] Define classification categories and prompts
- [ ] Integrate into chat flow before RAG
- [ ] Add Georgian response messages
- [ ] Test with off-topic and legal prompts
- [ ] **Milestone complete:** Off-topic blocked, legal proceeds ✅

## Milestone 6: Guardrail Configuration & Logging
- [ ] Add config constants (enabled, threshold, model)
- [ ] Implement decision logging
- [ ] Add ADMIN bypass
- [ ] Verify logging for 10 test messages
- [ ] **Milestone complete:** Config and audit logging operational ✅

## Milestone 7: Tests
- [ ] Unit tests for `GuardrailService`
- [ ] Unit tests for threshold retrieval
- [ ] Integration tests for end-to-end flow
- [ ] Georgian language edge case tests
- [ ] No regressions in existing 124 tests
- [ ] **Milestone complete:** All tests pass ✅

---

## Blockers / Notes

_None yet._
