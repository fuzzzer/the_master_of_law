# Task: Legal Thresholds in RAG + Hard Guardrails

> **Covers:** Task 4 (Specific Legal Thresholds in RAG) + Task 5 (Hard Guardrails — Pre-Answer Routing)
> **Why combined:** Both are pre-processing layers that run before the AI generates its answer. Guardrails filter out off-topic prompts; thresholds ensure specialized legal data is available when on-topic prompts pass through. Both are backend-only with no Flutter UI changes.

---

## Purpose

### Legal Thresholds in RAG
Inject highly specific, structured legal data into the RAG knowledge base — data that doesn't live in statute text but is critical for accurate legal advice. Examples:
- **Drug quantity thresholds** (Criminal Code): amounts that determine misdemeanor vs. felony charges
- **Statute of limitations** by crime/civil category
- **Fine amounts and ranges** per offense type
- **Minimum/maximum sentences** per criminal article
- **Filing deadlines** (court procedures, appeals)
- **Monetary thresholds** for jurisdictional limits (which court hears the case)

This data is often embedded in tables, footnotes, or government decrees — not easily retrievable via standard text chunking.

### Hard Guardrails
Add a fast, cheap pre-filter before the AI processes a user's message. A lightweight model (Gemini Flash or equivalent) checks whether the prompt is law-related. If not, the system returns a polite redirect without burning expensive RAG + Gemini Pro credits.

---

## Multi-Step Guide

### Milestone 1: Audit Threshold Data Needs
1. Review all 12 legal codes to identify structured threshold data
2. Focus on the Criminal Code (სისხლის სამართლის კოდექსი) first — highest impact
3. Create a catalog of threshold types: quantities, timelines, amounts, ranges
4. Identify data sources: code text, government decrees, Supreme Court clarifications
5. **Verify:** Catalog with at least 20 specific threshold entries documented

### Milestone 2: Design Threshold Data Format
1. Design a structured chunk format for thresholds:
   ```json
   {
     "type": "legal_threshold",
     "code": "criminal_code",
     "article": "260",
     "threshold_type": "drug_quantity",
     "substance": "მარიხუანა",
     "values": {"small": "<=70g", "large": ">70g", "extra_large": ">10kg"},
     "consequence": {"small": "მუხლი 273 (misdemeanor)", "large": "მუხლი 260.2", "extra_large": "მუხლი 260.3"},
     "source_url": "https://matsne.gov.ge/...",
     "last_verified": "2026-05-01"
   }
   ```
2. Decide storage: new ChromaDB collection (`legal_thresholds`) vs. enriched metadata in existing `georgian_laws`
3. Design embedding strategy: should threshold chunks use different embedding templates?
4. **Verify:** 5 sample thresholds formatted and validated

### Milestone 3: Ingest Threshold Data into ChromaDB
1. Write an ingestion script: `law_corpus/ingest_thresholds.py`
2. Parse threshold data from the structured catalog
3. Generate embeddings using `gemini-embedding-001` with `RETRIEVAL_DOCUMENT` task type
4. Add to ChromaDB (new collection or enriched chunks in `georgian_laws`)
5. Update `RAGCollectionConfig` if a new collection is added
6. **Verify:** Vector search for "რა რაოდენობის მარიხუანა" returns the drug threshold chunk

### Milestone 4: Update RAG Pipeline for Threshold Awareness
1. Modify the rerank stage to boost threshold chunks when the query involves quantities, deadlines, or limits
2. Add a threshold detection heuristic: if the query mentions numbers, amounts, or time periods, prioritize threshold chunks
3. Update the system prompt to instruct Gemini to use exact threshold values when available
4. **Verify:** Chat query "How much marijuana triggers a felony charge?" returns exact gram thresholds with article citations

### Milestone 5: Implement Hard Guardrails (Pre-Answer Routing)
1. Create `GuardrailService` in `backend/app/services/guardrail_service.py`
2. Use Gemini Flash (cheapest, fastest) for classification:
   - Input: user's message (raw text)
   - Output: `{"is_legal": true/false, "confidence": 0.0-1.0, "category": "legal|greeting|off_topic|harmful"}`
3. Classification categories:
   - `legal` — proceed normally
   - `greeting` — respond with a greeting, don't run RAG
   - `off_topic` — polite redirect: "I can only help with legal questions"
   - `harmful` — block: illegal requests, threats, etc.
4. Integrate into the chat flow BEFORE RAG pipeline:
   ```
   User message → Guardrail (Flash, ~200ms) → if legal → RAG + Gemini Pro
                                             → if off_topic → static response
                                             → if harmful → block + log
   ```
5. **Verify:** Off-topic prompt "What's the weather?" returns redirect. Legal prompt proceeds normally.

### Milestone 6: Guardrail Configuration & Logging
1. Add guardrail config to `backend/app/config/constants.py`:
   - `GUARDRAIL_ENABLED: bool = True`
   - `GUARDRAIL_CONFIDENCE_THRESHOLD: float = 0.7`
   - `GUARDRAIL_MODEL: str = "gemini-2.0-flash"`
2. Log all guardrail decisions for audit: `user_id`, `message_hash`, `decision`, `confidence`, `timestamp`
3. Add bypass for ADMIN users (always skip guardrails)
4. **Verify:** Logs show correct classification for 10 test messages (5 legal, 5 off-topic)

### Milestone 7: Tests
1. Unit tests for `GuardrailService` with mocked Gemini Flash
2. Unit tests for threshold retrieval
3. Integration tests: end-to-end chat with guardrails + thresholds
4. Test Georgian language edge cases (legal terms that look off-topic to English models)
5. **Verify:** All tests pass, no regressions in existing 124 tests
