# Task: Refactor Eval Pipeline — Test Real Backend System

> **Problem:** Current `run_eval.py` sends case facts directly to raw Gemini. It tests Google's model, NOT our system.
> Our system is: RAG (3 collections) → source-specific prompts → legal analysis → citations → defense strategy.
> We need the eval to test the actual product flow.

---

## What's Wrong Now

```
Current eval (BROKEN — tests nothing):
  case.situation → raw Gemini → AI response → judge scores

What our product actually does:
  user message → 5-stage RAG (expand → vector search 3 collections → fulltext → merge → rerank)
               → source-specific prompt injection (court practice / Grand Chamber rules)
               → Gemini + retrieved law context → citation verification → structured response
```

The eval should test the **second flow** — the real one.

---

## Correct Eval Flow

```
1. Start backend (Docker)
2. For each eval case:
   a. POST /api/v1/conversations → create conversation
   b. POST /api/v1/chat/{id}/send with situation text + rag_config
      → Backend runs full RAG pipeline
      → Returns: AI response + citations + retrieved_chunks
   c. AI Judge compares:
      - Did the system find the RIGHT laws? (from retrieved_chunks)
      - Did the system cite court practice that supports/contradicts? 
      - Did the defense strategy address the actual court outcome?
      - Would this case file help a citizen prepare for court?
   d. DELETE /api/v1/conversations/{id} (cleanup)
3. Save results with source attribution
```

---

## Three Eval Modes (Side-by-Side Comparison)

### Mode 1: `--mode baseline`
- Sends situation directly to Gemini (no RAG, no backend)
- Tests: "How much does Gemini know about Georgian law on its own?"
- `rag_config`: N/A

### Mode 2: `--mode laws-only`
- Calls the real backend API with **only legal codes**
- Tests: "How much do our law embeddings improve over raw Gemini?"
- `rag_config`: `{"legal_codes": true, "court_practice": false, "grand_chamber": false}`

### Mode 3: `--mode full` (DEFAULT)
- Calls the real backend API with **all 3 collections**
- Tests: "How much does court practice + Grand Chamber add on top of laws?"
- `rag_config`: `{"legal_codes": true, "court_practice": true, "grand_chamber": true}`

### What We Learn

```
baseline → laws-only  = value of our law corpus RAG
laws-only → full      = value of court practice + Grand Chamber
baseline → full       = total value of our entire system
```

| If... | It means... |
|-------|-------------|
| `full` > `laws-only` > `baseline` | Each layer adds value ✅ |
| `laws-only` ≈ `full` | Court practice / GC not helping (fix retrieval or prompts) |
| `baseline` ≈ `laws-only` | Law RAG not adding value (fix embeddings/retrieval) |
| `baseline` > `laws-only` | RAG is adding noise (fix prompt or reduce context) |

---

## Implementation

### 1. Backend Client for Eval

```python
# eval/test_cases/backend_client.py

import httpx
from typing import Any

class EvalBackendClient:
    """Calls the real backend API for evaluation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=120)  # Legal analysis can be slow
    
    def health_check(self) -> bool:
        """Verify backend is running."""
        try:
            r = self.client.get(f"{self.base_url}/api/v1/health/ready")
            return r.status_code == 200
        except Exception:
            return False
    
    def create_conversation(self, title: str) -> str:
        """Create a conversation, return its ID."""
        r = self.client.post(
            f"{self.base_url}/api/v1/conversations",
            json={"title": title},
        )
        r.raise_for_status()
        return r.json()["id"]
    
    def send_message(
        self, 
        conversation_id: str, 
        message: str,
        rag_config: dict | None = None,
    ) -> dict[str, Any]:
        """Send message through the full RAG pipeline.
        
        Returns:
            {
                "response": str,           # Full AI legal analysis
                "citations": [...],        # Verified citations
                "retrieved_chunks": [...], # What RAG found
            }
        """
        body = {"message": message}
        if rag_config:
            body["rag_config"] = rag_config
        
        r = self.client.post(
            f"{self.base_url}/api/v1/chat/{conversation_id}/send",
            json=body,
        )
        r.raise_for_status()
        return r.json()
    
    def delete_conversation(self, conversation_id: str):
        """Cleanup after eval."""
        self.client.delete(f"{self.base_url}/api/v1/conversations/{conversation_id}")
```

### 2. Updated `evaluate_case` in `run_eval.py`

```python
def evaluate_case_system(backend: EvalBackendClient, case: dict, ...) -> dict:
    """Evaluate using the real backend system."""
    case_id = case["case_id"]
    situation = case["situation"]
    
    # Step 1: Create conversation
    conv_id = backend.create_conversation(f"eval-{case_id}")
    
    try:
        # Step 2: Send through full RAG pipeline
        result = backend.send_message(conv_id, situation)
        
        ai_response = result["response"]
        citations = result.get("citations", [])
        chunks = result.get("retrieved_chunks", [])
        
        # Step 3: Judge — now also evaluates RAG quality
        # Judge gets: AI response, court ruling, AND what sources were retrieved
        judge_prompt = SYSTEM_JUDGE_PROMPT.format(
            situation=situation,
            ai_response=ai_response,
            court_reasoning=case["court_reasoning"],
            court_resolution=case["court_resolution"],
            citations_found=len(citations),
            chunks_retrieved=len(chunks),
            # Show which collections contributed
            sources_used=summarize_sources(chunks),
        )
        
        scores = call_judge(judge_prompt)
        
        return {
            "case_id": case_id,
            "mode": "system",
            "status": "ok",
            "ai_response": ai_response,
            "citations": citations,
            "chunks_retrieved": len(chunks),
            "sources_used": summarize_sources(chunks),
            "scores": scores,
        }
    finally:
        backend.delete_conversation(conv_id)
```

### 3. Updated Judge Prompt

The judge should now also evaluate RAG-specific quality:

```python
SYSTEM_JUDGE_PROMPT = """
შეაფასეთ AI სამართლებრივი ასისტენტის პასუხი, რომელიც დაფუძნებულია
RAG სისტემაზე (კანონების, სასამართლო პრაქტიკის და დიდი პალატის ბაზებიდან).

შეფასების კრიტერიუმები:

1. **verdict_alignment** — AI-მ სწორად იწინასწარმეტყველა შედეგი?
2. **legal_reasoning** — AI-ს სამართლებრივი მსჯელობა სწორია?
3. **article_accuracy** — AI-მ სწორი მუხლები მოიძია და მიუთითა?
4. **rag_quality** — RAG-მა სწორი წყაროები მოიძია? (NEW)
   - 5 = მოიძია ზუსტად ის კანონები და პრაქტიკა, რაც სასამართლომ გამოიყენა
   - 3 = მოიძია ნაწილი, ზოგი არელევანტური
   - 1 = ვერ მოიძია რელევანტური წყაროები
5. **practical_value** — მოქალაქეს გამოადგებოდა?
6. **defense_strategy** — სწორი დაცვის სტრატეგია შესთავაზა? (NEW)
   - 5 = სტრატეგია ემთხვევა იმას, რაც სასამართლოში წარმატებული აღმოჩნდა
   - 1 = სტრატეგია სრულად არასწორი იყო

წყაროები რომელიც RAG-მა მოიძია: {sources_used}
ციტირებული მუხლების რაოდენობა: {citations_found}
"""
```

### 4. CLI Update

```bash
# Test all three modes on specific cases
python3 run_eval.py --mode full --cases "CRIM-1051ap-24" --output eval_full.json
python3 run_eval.py --mode laws-only --cases "CRIM-1051ap-24" --output eval_laws.json
python3 run_eval.py --mode baseline --cases "CRIM-1051ap-24" --output eval_baseline.json

# Full comparison run (all 50 cases, each mode)
python3 run_eval.py --mode full --output eval_full_v1.json
python3 run_eval.py --mode laws-only --output eval_laws_v1.json
python3 run_eval.py --mode baseline --output eval_baseline_v1.json

# Side-by-side comparison report
python3 compare_modes.py eval_baseline_v1.json eval_laws_v1.json eval_full_v1.json
```

---

## Prerequisites

- Backend running in Docker: `cd backend && docker compose up --build -d`
- Migrations done: `docker compose exec api alembic upgrade head`
- ChromaDB holdout completed: `python3 holdout_eval.py holdout`
- Dev mode (no auth required)

---

## New Scoring Criteria

| Criterion | What it measures | Baseline | Laws-Only | Full |
|-----------|-----------------|----------|-----------|------|
| `verdict_alignment` | Predicted correct outcome? | ✅ | ✅ | ✅ |
| `legal_reasoning` | Logic matches court? | ✅ | ✅ | ✅ |
| `article_accuracy` | Right law articles cited? | ✅ | ✅ | ✅ |
| `rag_quality` | Right sources retrieved? | N/A | ✅ | ✅ |
| `defense_strategy` | Correct defense approach? | ✅ | ✅ | ✅ |
| `practical_value` | Useful for citizen? | ✅ | ✅ | ✅ |
| `overall_score` | Weighted composite | ✅ | ✅ | ✅ |

---

## Implementation Order

1. Create `backend_client.py` (30 min)
2. Add `--mode` flag to `run_eval.py` (30 min)
3. Refactor `evaluate_case` into `evaluate_case_baseline` + `evaluate_case_system` (1 hr)
4. Write updated judge prompt with RAG-aware scoring (30 min)
5. Add source summary extraction from retrieved chunks (30 min)
6. Add `compare_modes.py` script for side-by-side comparison (30 min)
7. Test with 3 cases, then full run (1 hr)

**Total: ~4-5 hours**

---

## Key Insight

> The current eval answers: "How good is Gemini at Georgian law?"
> The new eval answers: "How good is **our product** at helping Georgian citizens?"
> 
> That's the question that actually matters.
