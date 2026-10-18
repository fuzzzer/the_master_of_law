# Task: Eval Pipeline Refactor — Three-Mode Comparison

> **Goal:** Refactor `eval/test_cases/run_eval.py` so it tests **our actual product**, not raw Gemini.
> Compare three modes side-by-side to measure the value of each RAG layer.

---

## The Problem

Current `run_eval.py` sends case facts directly to raw Gemini and judges the response.
This tests Google's model — NOT our system (RAG + source-specific prompts + citations).

```
Current (broken):  situation → raw Gemini → judge
Our product:       situation → 5-stage RAG (3 collections) → source prompts → Gemini + context → citations
```

---

## Three Eval Modes

### Mode 1: `--mode baseline`
- Sends situation directly to Gemini (no RAG, no backend)
- Measures: "How much does Gemini know about Georgian law on its own?"
- Uses existing `evaluate_case()` logic (direct Gemini call)

### Mode 2: `--mode laws-only`
- Calls real backend API with **only legal codes** enabled
- `rag_config: {"legal_codes": true, "court_practice": false, "grand_chamber": false}`
- Measures: "How much do our law embeddings improve over raw Gemini?"

### Mode 3: `--mode full` (DEFAULT)
- Calls real backend API with **all 3 collections** enabled
- `rag_config: {"legal_codes": true, "court_practice": true, "grand_chamber": true}`
- Measures: "How much does court practice + Grand Chamber add on top?"

### What We Learn

```
baseline → laws-only  = value of our law corpus RAG
laws-only → full      = value of court practice + Grand Chamber
baseline → full       = total value of our entire system
```

| If... | It means... |
|-------|-------------|
| `full` > `laws-only` > `baseline` | Each layer adds value ✅ |
| `laws-only` ≈ `full` | Court practice / GC not helping — fix retrieval or prompts |
| `baseline` ≈ `laws-only` | Law RAG not adding value — fix embeddings/retrieval |
| `baseline` > `laws-only` | RAG is adding noise — fix prompt or reduce context |

---

## Eval Flow (modes 2 & 3 — backend modes)

```
1. Verify backend is running (health check)
2. For each eval case:
   a. POST /api/v1/conversations  →  create conversation
   b. POST /api/v1/chat/{id}/send  with situation text + rag_config
      → Backend runs full RAG pipeline
      → Returns: { response, citations, retrieved_chunks }
   c. AI Judge scores response vs actual court ruling
   d. DELETE /api/v1/conversations/{id}  (cleanup)
3. Save results with mode label and source attribution
```

---

## Implementation Steps

### 1. Backend Client ✅ DONE
- File: `eval/test_cases/backend_client.py`
- `EvalBackendClient` with: `health_check()`, `create_conversation()`, `send_message(rag_config)`, `delete_conversation()`
- Retry logic for rate limits and server errors

### 2. Add `--mode` flag to `run_eval.py`
- Add `--mode {baseline,laws-only,full}` argument (default: `full`)
- Add `--backend-url` argument (default: `http://localhost:8000`)
- Route to `evaluate_case_baseline()` or `evaluate_case_system()` based on mode

### 3. `evaluate_case_baseline()` — Keep existing logic
- Rename current `evaluate_case()` → `evaluate_case_baseline()`
- Direct Gemini call, same as now

### 4. `evaluate_case_system()` — New, calls backend
```python
def evaluate_case_system(backend, case, rag_config, ...):
    conv_id = backend.create_conversation(f"eval-{case_id}")
    try:
        result = backend.send_message(conv_id, situation, rag_config=rag_config)
        ai_response = result["response"]
        citations = result.get("citations", [])
        chunks = result.get("retrieved_chunks", [])
        # Judge scores (same judge, but with extra RAG metadata)
        scores = call_judge(...)
        return {
            "case_id": ..., "mode": ..., "status": "ok",
            "ai_response": ai_response,
            "citations": citations,
            "chunks_retrieved": len(chunks),
            "sources_used": summarize_sources(chunks),
            "scores": scores,
        }
    finally:
        backend.delete_conversation(conv_id)
```

### 5. Updated Judge Prompt (RAG-aware)
Add two new scoring criteria for backend modes:

| Criterion | What it measures | Baseline | Backend |
|-----------|-----------------|----------|---------|
| `verdict_alignment` | Predicted correct outcome? | ✅ | ✅ |
| `legal_reasoning` | Logic matches court? | ✅ | ✅ |
| `article_accuracy` | Right law articles cited? | ✅ | ✅ |
| `rag_quality` | Right sources retrieved? | N/A | ✅ |
| `defense_strategy` | Correct defense approach? | ✅ | ✅ |
| `practical_value` | Useful for citizen? | ✅ | ✅ |
| `overall_score` | Weighted composite | ✅ | ✅ |

### 6. Source Summary Helper
```python
def summarize_sources(chunks: list[dict]) -> dict:
    """Count chunks by collection/code_name."""
    summary = {}
    for c in chunks:
        source = c.get("code_name", "unknown")
        summary[source] = summary.get(source, 0) + 1
    return summary
```

### 7. `compare_modes.py` — Side-by-Side Report
```bash
python3 compare_modes.py eval_baseline.json eval_laws.json eval_full.json
```
Output: per-case deltas, average improvement per layer, worst regressions.

### 8. Save mode in results JSON
Each result includes `"mode": "baseline|laws-only|full"` so results are distinguishable.

---

## CLI Usage

```bash
# Single case, all three modes
python3 run_eval.py --mode baseline --cases "CRIM-1051ap-24" --output eval_baseline.json
python3 run_eval.py --mode laws-only --cases "CRIM-1051ap-24" --output eval_laws.json
python3 run_eval.py --mode full     --cases "CRIM-1051ap-24" --output eval_full.json

# Full 50-case runs
python3 run_eval.py --mode baseline  --output results/eval_baseline_v1.json
python3 run_eval.py --mode laws-only --output results/eval_laws_v1.json
python3 run_eval.py --mode full      --output results/eval_full_v1.json

# Compare
python3 compare_modes.py results/eval_baseline_v1.json results/eval_laws_v1.json results/eval_full_v1.json
```

---

## Prerequisites

- Backend running: `cd backend && docker compose up --build -d`
- Migrations done: `docker compose exec api alembic upgrade head`
- Dev mode (no auth required)
- ChromaDB holdout completed if testing without contamination:
  `python3 holdout_eval.py holdout` → run eval → `python3 holdout_eval.py restore`

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `eval/test_cases/backend_client.py` | ✅ Created |
| `eval/test_cases/run_eval.py` | Refactor — add `--mode`, split evaluate functions |
| `eval/test_cases/compare_modes.py` | Create — side-by-side comparison script |
