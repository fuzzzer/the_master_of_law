# Task 03 Integration Guide — Legal Thresholds + Hard Guardrails

> **Goal**: Wire guardrails and threshold boosting into the existing chat/RAG flow without modifying `backend/app/main.py` or generating Alembic migrations.
> **Agent**: Task 03 — Legal Thresholds in RAG + Hard Guardrails

---

## 1. HARD GUARDRAILS — Integration Points

### 1.1 Constants (`backend/app/config/constants.py`)

The following constants were added (or already exist) in `constants.py`:

```python
GUARDRAIL_ENABLED: bool = True
GUARDRAIL_CONFIDENCE_THRESHOLD: float = 0.7
GUARDRAIL_MODEL: str = "gemini-2.0-flash"
```

If they are missing, add them to `backend/app/config/constants.py`.

### 1.2 GuardrailService — Singleton

**File**: `backend/app/services/guardrail_service.py`

Already implemented. Retrieves configuration from `constants.py` via `get_guardrail_service()`.

### 1.3 Where to inject the guardrail check

#### A. HTTP Chat Router — `backend/app/routes/chat_router.py`

**Location**: Inside `send_message()`, **before** the RAG retrieval call (`rag.retrieve(...)`).

**Current code block** (lines 75–78):
```python
    # Step 1: RAG Retrieval
    rag = get_rag_service()
    collections = body.rag_config.to_collection_names() if body.rag_config else None
    chunks = await rag.retrieve(body.message, collections=collections)
```

**Integration code** (insert immediately before the above block):
```python
    # ── Guardrail Pre-Filter ─────────────────────────────
    from app.services.guardrail_service import get_guardrail_service
    from app.config.constants import UserTier

    guardrail = get_guardrail_service()
    user_info = getattr(request.state, "user", None)
    user_tier = user_info.get("tier", "FREE") if user_info else "FREE"
    user_id = user_info.get("uid", "anonymous") if user_info else "anonymous"

    bypass = guardrail.should_bypass(user_tier)
    decision = await guardrail.classify(body.message)
    guardrail.log_decision(user_id, body.message, decision, bypassed=bypass)

    if not bypass and not decision.is_legal:
        # Return a polite Georgian response without spending credits or calling RAG
        return ChatSendResponse(
            response=guardrail.get_response(decision),
            citations=[],
            retrieved_chunks=[],
            credits_remaining=None,
        )
    # ── End Guardrail ────────────────────────────────────
```

**Why here?**  
- Runs **before** RAG → saves embedding + ChromaDB costs  
- Runs **before** Gemini analysis → saves the expensive Pro model call  
- Skips credit deduction for blocked messages (credit cost = 0 for guardrails)  
- `bypass` lets ADMIN users skip the check entirely

#### B. WebSocket Chat Router — `backend/app/routes/ws_chat_router.py`

**Location**: Inside `chat_websocket()`, after receiving the message and **before** the RAG retrieval call.

**Current code block** (lines 64–70):
```python
            # Send processing status
            await websocket.send_json({"type": "status", "message": "Searching laws..."})

            try:
                # Step 1: RAG retrieval
                rag = get_rag_service()
                chunks = await rag.retrieve(user_message, collections=collections)
```

**Integration code** (insert immediately before the `try:` block):
```python
            # ── Guardrail Pre-Filter (WS) ────────────────────────
            from app.services.guardrail_service import get_guardrail_service

            guardrail = get_guardrail_service()
            # NOTE: For WS, user tier is not easily available without auth middleware
            # integration. If available, pass it; otherwise default to no bypass.
            decision = await guardrail.classify(user_message)
            guardrail.log_decision("ws-anonymous", user_message, decision, bypassed=False)

            if not decision.is_legal:
                await websocket.send_json({
                    "type": "done",
                    "full_response": guardrail.get_response(decision),
                    "citations": [],
                    "chunk_count": 0,
                })
                continue
            # ── End Guardrail ────────────────────────────────────
```

### 1.4 ADMIN Bypass

**Implementation**: `GuardrailService.should_bypass()` already checks `user_tier == UserTier.ADMIN`.

**Usage in routers**:
```python
if guardrail.should_bypass(user_tier):
    decision = GuardrailDecision.legal(confidence=1.0)
    bypassed = True
else:
    decision = await guardrail.classify(body.message)
    bypassed = False
```

### 1.5 Logging Schema

Every guardrail decision is logged via `GuardrailService.log_decision()`:

| Field            | Type   | Description                                      |
|------------------|--------|--------------------------------------------------|
| `user_id`        | str    | Firebase UID or `"anonymous"` / `"ws-anonymous"` |
| `message_hash`   | str    | SHA-256 hex digest of the raw message text       |
| `decision`       | str    | `"legal"`, `"greeting"`, `"off_topic"`, `"harmful"` |
| `confidence`     | float  | Model confidence, rounded to 4 decimals          |
| `timestamp`      | str    | ISO-8601 UTC timestamp                           |
| `bypassed`       | bool   | `True` if ADMIN bypass was applied               |

**Example log line**:
```json
{"event": "guardrail_decision", "user_id": "abc123", "message_hash": "a3f5...", "decision": "off_topic", "confidence": 0.92, "timestamp": "2026-05-09T02:00:00+00:00", "bypassed": false}
```

**Privacy note**: The full message text is **never** logged — only its SHA-256 hash.

---

## 2. LEGAL THRESHOLDS — Integration Points

### 2.1 Data Format

**File**: `law_corpus/data/thresholds/threshold_catalog.json`

Already populated with 20 threshold entries covering:
- Drug quantity thresholds (marijuana, heroin, cocaine)
- Statute of limitations (Article 76)
- Fine ranges (Article 40)
- Minimum/maximum sentences (murder, extortion, theft)
- Filing deadlines (appeal, preliminary inquiry, labor notice)
- Monetary limits (VAT registration, small claims, bail, inheritance tax)
- Age limits (criminal responsibility)
- Alcohol limits for driving (Article 276)

Each entry follows this schema:
```json
{
  "id": "unique_id",
  "type": "legal_threshold",
  "code_name": "სისხლის სამართლის კოდექსი",
  "article_number": "მუხლი 260",
  "threshold_type": "drug_quantity",
  "description_ka": "...",
  "substance": "მარიხუანა",
  "values": {"small": "≤ 70 გრამი", "large": "> 70 გრამი"},
  "consequence_ka": "...",
  "source_url": "https://matsne.gov.ge/ka/document/view/16426",
  "last_verified": "2026-05-01"
}
```

### 2.2 Ingestion Script

**File**: `law_corpus/ingest_thresholds.py`

Already implemented. Run with:
```bash
cd law_corpus
python ingest_thresholds.py
```

Or dry-run:
```bash
python ingest_thresholds.py --dry-run
```

What it does:
1. Loads `data/thresholds/threshold_catalog.json`
2. Generates embeddings with `gemini-embedding-001` (`RETRIEVAL_DOCUMENT` task type)
3. Upserts into the existing `georgian_laws` ChromaDB collection
4. Sets metadata `"chunk_type": "threshold"`
5. Deletes existing threshold chunks before re-insert to avoid duplicates

### 2.3 Threshold Detection Heuristic

**File**: `backend/app/services/threshold_rerank_service.py`

Already implemented. `ThresholdRerankService.is_threshold_query()` scans for:
- Numbers followed by units (`გრამი`, `კგ`, `ლარი`, `წელი`, `თვე`, `დღე`, `პრომილი`)
- Quantity keywords (`რამდენი`, `ოდენობა`, `ზღვარი`, `ვადა`)
- Legal consequence keywords (`ჯარიმა`, `სასჯელი`, `გირავნობა`)
- Monetary amounts (`10,000 ლარი`)
- Percentage / promille expressions (`50%`, `0.5 პრომილი`)

### 2.4 Rerank Boost — Where to inject

**File**: `backend/app/services/rag_retrieval_service.py`

**Location**: Inside `retrieve()`, **after** Stage 3 (merge/dedup) and **before** Stage 4 (Gemini rerank).

**Current code block** (lines 102–109):
```python
        merged = self._stage_3_merge_and_dedup(vector_hits, fulltext_hits)
        logger.info("rag_stage_3_done", merged_count=len(merged))

        if len(merged) > top_k:
            reranked = await self._stage_4_rerank(user_message, merged, top_k)
        else:
            reranked = merged
```

**Integration code** (insert after `merged = ...` and before the `if len(merged) > top_k:` block):
```python
        # ── Threshold Boost ──────────────────────────────────
        from app.services.threshold_rerank_service import get_threshold_rerank_service

        threshold_svc = get_threshold_rerank_service()
        merged = threshold_svc.apply_threshold_boost(merged, user_message, boost=1.5)
        # ── End Threshold Boost ──────────────────────────────
```

**Why here?**  
- Stage 3 produces a unified, deduplicated candidate list  
- Boosting at this point affects both vector and full-text hits uniformly  
- Stage 4 (Gemini rerank) then operates on the boosted ordering, increasing the chance threshold chunks appear in the final top-k

### 2.5 System Prompt Update

**File**: `backend/app/prompts/legal_analysis.py`

**Location**: Append to the `LEGAL_ANALYSIS_SYSTEM` template string.

**Add the following paragraph** inside the template (after the existing "CRITICAL RULES" section, as rule #11):

```text
11. When threshold data is present in the retrieved context, use the EXACT
    quantitative values (grams, liters, lari, years, days, promille) in your
    answer. Do not round or approximate statutory thresholds. Cite the exact
    article and the precise boundary that applies to the user's situation.
```

**Rationale**: This instructs Gemini Pro (the analysis model) to treat threshold chunks with high fidelity and surface exact numbers to the user.

---

## 3. MODELS & SCHEMAS — New Files

| File                                      | Purpose                                          |
|-------------------------------------------|--------------------------------------------------|
| `backend/app/models/threshold_chunk.py`   | `ThresholdChunk` Pydantic model — catalog → ChromaDB mapping |
| `backend/app/schemas/threshold.py`        | `ThresholdResponse`, `ThresholdQueryResult` — API schemas |
| `backend/app/schemas/guardrail_schema.py` | `GuardrailCategory`, `GuardrailDecision`, `GuardrailLogEntry` |

These are **already created** and do not require additional integration steps.

---

## 4. TESTS

| File                                                | Coverage                              |
|-----------------------------------------------------|---------------------------------------|
| `backend/tests/test_guardrail_service.py`           | 22 tests — classification, bypass, logging, responses |
| `backend/tests/test_threshold_retrieval.py`         | 19 tests — heuristic detection, boost math, reordering |
| `backend/tests/fixtures/guardrail_test_messages.json` | 20 labeled messages (10 legal, 5 off-topic, 3 greeting, 2 harmful) |

Run:
```bash
cd backend
pytest tests/test_guardrail_service.py tests/test_threshold_retrieval.py -v
```

---

## 5. CHECKLIST

- [ ] `GUARDRAIL_ENABLED`, `GUARDRAIL_CONFIDENCE_THRESHOLD`, `GUARDRAIL_MODEL` added to `constants.py`
- [ ] Guardrail check inserted into `chat_router.py` before RAG retrieval
- [ ] Guardrail check inserted into `ws_chat_router.py` before RAG retrieval
- [ ] Threshold boost inserted into `rag_retrieval_service.py` after Stage 3
- [ ] System prompt updated in `legal_analysis.py` with threshold exact-value rule
- [ ] Ingestion script run: `python law_corpus/ingest_thresholds.py`
- [ ] `chunk_type: "threshold"` visible in ChromaDB metadata for ingested entries
- [ ] Tests pass: `pytest tests/test_guardrail_service.py tests/test_threshold_retrieval.py`
