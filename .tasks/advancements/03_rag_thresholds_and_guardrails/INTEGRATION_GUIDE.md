# Integration Guide: Task 03 — Legal Thresholds + Hard Guardrails

## What Changed

### New Files (safe — no merge conflicts)

| File | Purpose |
|------|---------|
| `law_corpus/data/thresholds/threshold_catalog.json` | 21 structured legal threshold entries from Georgian Criminal Code, Civil Code, Labor Code, Tax Code, and Administrative Code |
| `law_corpus/ingest_thresholds.py` | Standalone script to embed thresholds and upsert into ChromaDB `georgian_laws` collection |
| `backend/app/schemas/guardrail_schema.py` | Pydantic schemas: `GuardrailCategory`, `GuardrailDecision`, `GuardrailLogEntry` |
| `backend/app/services/guardrail_service.py` | `GuardrailService` — Gemini Flash classification with Georgian responses |
| `backend/app/services/threshold_rerank_service.py` | `ThresholdRerankService` — heuristic detection + 1.5x score boost for threshold chunks |
| `backend/tests/test_guardrail_service.py` | 19 unit tests for guardrail classification, bypass, logging |
| `backend/tests/test_threshold_retrieval.py` | 14 unit tests for threshold detection and rerank boost |
| `backend/tests/test_guardrail_integration.py` | 7 integration tests for end-to-end guardrail + threshold flow |
| `backend/tests/fixtures/guardrail_test_messages.json` | 20 test messages (10 legal, 5 off-topic, 3 greeting, 2 harmful) |

### Modified Files (minimal — review carefully)

| File | Change | Lines |
|------|--------|-------|
| `backend/app/config/constants.py` | Added 3 guardrail constants: `GUARDRAIL_ENABLED`, `GUARDRAIL_CONFIDENCE_THRESHOLD`, `GUARDRAIL_MODEL` | ~93–95 |
| `backend/app/services/rag_retrieval_service.py` | Injected `ThresholdRerankService`; added `apply_threshold_boost()` call between Stage 3 merge and Stage 4 rerank | Import + property + pipeline call |
| `backend/app/services/legal_analysis_service.py` | Added `threshold` source-specific instructions to `_RAG_INSTRUCTIONS` | ~28–39 |
| `backend/app/routes/chat_router.py` | Added guardrail classification BEFORE RAG; ADMIN bypass; 0-credit responses for blocked messages | Import + pre-filter block |
| `backend/tests/test_prompts.py` | Updated expected prompt count from 7 → 9 (unrelated fix for Task 02 prompts) | Line 109 |

## How to Run

### 1. Ingest thresholds into ChromaDB
```bash
cd law_corpus
python ingest_thresholds.py --dry-run   # Preview
python ingest_thresholds.py             # Actually write
```

Requires `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` env vars (or `.env`).

### 2. Run tests
```bash
cd backend
pytest tests/test_guardrail_service.py tests/test_threshold_retrieval.py tests/test_guardrail_integration.py -v
```

### 3. Verify no regressions
```bash
cd backend
pytest tests/ -v
```

## Integration Points for Other Agents

### If you modify `chat_router.py`
The guardrail pre-filter is inserted right after `conv_svc.get_conversation_history()` and before RAG retrieval. Look for the comment:
```python
# ── Guardrail pre-filter (Task 03) ────────────────────────
```

**Do not remove** this block unless guardrails are being redesigned.

### If you modify `rag_retrieval_service.py`
The `ThresholdRerankService` is injected similarly to `ChromaClient` and `VertexAIClient`. The boost is applied between Stage 3 (merge/dedup) and Stage 4 (rerank). If you refactor pipeline stages, preserve this ordering.

### If you modify `legal_analysis_service.py`
The `_RAG_INSTRUCTIONS` dict now has a `"threshold"` key. If you change how source-specific instructions are assembled, ensure `"threshold"` is still included when threshold chunks are present.

## Configuration

Guardrails can be tuned via environment variables or by editing `backend/app/config/constants.py`:

- `GUARDRAIL_ENABLED` — set `False` to disable all guardrails (emergency switch)
- `GUARDRAIL_CONFIDENCE_THRESHOLD` — minimum confidence to block off-topic/harmful (default `0.7`)
- `GUARDRAIL_MODEL` — Gemini model for classification (default `gemini-2.0-flash`)

## Georgian Response Messages

| Category | Message |
|----------|---------|
| `greeting` | "გამარჯობა! 👋 მე ვარ კანონის ოსტატი — თქვენი იურიდიული ასისტენტი. აღწერეთ თქვენი სამართლებრივი სიტუაცია და დაგეხმარებით." |
| `off_topic` | "ბოდიში, მე მხოლოდ სამართლებრივ საკითხებში შემიძლია დახმარება. გთხოვთ, აღწერეთ თქვენი იურიდიული სიტუაცია." |
| `harmful` | "ბოდიში, ამ ტიპის მოთხოვნაზე პასუხის გაცემა არ შემიძლია." |

## Design Decisions

1. **Option A for thresholds**: Thresholds live in the existing `georgian_laws` collection with `"chunk_type": "threshold"` metadata. No new collection, no schema migrations.
2. **Fail-open guardrails**: If Gemini Flash fails or returns garbage, the message is treated as `legal` so users are never accidentally blocked.
3. **Low-confidence off-topic/harmful → legal**: Reduces false positives below the 5% target.
4. **ADMIN bypass**: Users with `tier == "ADMIN"` skip guardrails entirely; this is checked before any Gemini call.
5. **Privacy-preserving logs**: Only `message_hash` (SHA-256) is logged, never the raw user message text.
