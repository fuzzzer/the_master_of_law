# Backend Context — The Master of Law

> FastAPI backend with multi-source RAG pipeline + Gemini 3.1 Pro legal analysis.
> **Status:** ✅ Complete (32 endpoints, 10 services, 179 tests)
> **Last updated:** 2026-05-07

---

## Architecture

```
Flutter App → HTTP/WS with Firebase ID token
  → CORS → Firebase Auth → Credit Gate → Rate Limit → Error Handler
  → Route Handler → Service → Repository → Response
```

### RAG Pipeline (core feature)
```
User Message + RAGCollectionConfig (feature flags)
  → [Stage 0] Gemini Query Expansion (5-10 formal Georgian legal terms)
  → [Stage 1] Multi-Query Vector Search (ChromaDB, top-50 per query × N collections)
  → [Stage 2] Multi-Query Full-Text Search (JSON indices, top-50 per query)
  → [Stage 3] Merge & Deduplicate by chunk_id
  → [Stage 4] Gemini Rerank (select top-20 most relevant)
  → Legal Analysis (Gemini 3.1 Pro + source-specific system prompt + context)
  → Citation Verification (regex + corpus validation)
```

### RAG Collection Feature Flags
```python
# Per-request control of which knowledge sources to search
class RAGCollectionConfig(BaseModel):
    legal_codes: bool = True       # georgian_laws (15,338 chunks)
    court_practice: bool = True    # court_practice (5,197 chunks)
    grand_chamber: bool = True     # grand_chamber (177 chunks)
    
# Usage in chat request:
{"message": "...", "rag_config": {"legal_codes": true, "court_practice": false}}
```

**Source-specific prompt injection:** When court_practice/grand_chamber chunks are retrieved,
source-specific instructions are appended to the system prompt (e.g., "Grand Chamber
decisions are BINDING and override all lower court interpretations").

---

## API Endpoints (32 total)

| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/health` | 0 | Liveness |
| GET | `/api/v1/health/ready` | 0 | Readiness (reports collection count) |
| POST | `/api/v1/auth/verify-token` | 0 | Firebase token → user |
| GET | `/api/v1/auth/me` | 0 | Current user |
| GET | `/api/v1/account/credits` | 0 | Credit balance |
| GET | `/api/v1/account/transactions` | 0 | Credit history |
| POST | `/api/v1/conversations` | 0 | Start conversation |
| GET | `/api/v1/conversations` | 0 | List conversations |
| GET | `/api/v1/conversations/{id}` | 0 | Get with messages |
| DELETE | `/api/v1/conversations/{id}` | 0 | Delete |
| POST | `/api/v1/chat/{id}/send` | **1** | Send → AI response (accepts `rag_config`) |
| WS | `/api/v1/chat/{id}/ws` | 1 | WebSocket streaming (accepts `rag_config`) |
| **GET** | **`/api/v1/rag/collections`** | 0 | **List RAG sources + availability** |
| POST | `/api/v1/case-files/build` | **3** | Build defense case (accepts `rag_config`) |
| GET | `/api/v1/case-files` | 0 | List case files |
| GET | `/api/v1/case-files/{id}` | 0 | Get case file |
| PATCH | `/api/v1/case-files/{id}` | 0 | Update notes/status |
| DELETE | `/api/v1/case-files/{id}` | 0 | Delete case file |
| GET | `/api/v1/laws/search?q=...` | 0 | Search laws (free) |
| GET | `/api/v1/laws/codes` | 0 | List codes (free) |
| GET | `/api/v1/laws/codes/{id}` | 0 | Code structure |
| GET | `/api/v1/laws/articles/{id}` | 0 | Article text |
| POST | `/api/v1/feedback` | 0 | Submit feedback (auth optional) |
| GET | `/api/v1/feedback/{target_id}` | 0 | Get feedback for a case/conversation |
| GET | `/api/v1/feedback/summary` | 0 | Aggregated dashboard (ADMIN only) |
| PATCH | `/api/v1/feedback/{id}` | 0 | Update own feedback (24h window) |
| DELETE | `/api/v1/feedback/{id}` | 0 | Delete own feedback |

---

## Key Patterns

### Layer Architecture
```
Route (thin) → Service (logic) → Repository (DB) → Model (ORM)
```

### Dependency Injection
```python
@router.post("/endpoint")
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    repo = MyRepository(db)
```

### Gemini API (google-genai SDK)
```python
from google import genai
client = genai.Client(api_key=settings.vertex_ai_api_key, vertexai=True,
                      project=settings.google_cloud_project, location=settings.google_cloud_location)
```

**CRITICAL:** Use `google-genai` only. NOT `google-cloud-aiplatform` or `vertexai`.

---

## Credit System

| Tier | Credits | Rate Limit |
|------|---------|------------|
| FREE | 5/day (auto-reset) | 5 req/min |
| PRO | Purchased | 30 req/min |
| ADMIN | 10,000 | 120 req/min |

---

## Services

| Service | Purpose |
|---------|---------|
| RAG Retrieval | 5-stage pipeline |
| Legal Analysis | Gemini system prompt + grounded analysis |
| Citation | Extract `მუხლი N` patterns, verify against corpus |
| Case Builder | 8-section defense case (3 credits) |
| Conversation | State machine + message persistence |
| Intake Flow | 6 guided questions in Georgian |
| Legal Classifier | 9 legal domains |
| Explanation | Simplify legal language |
| Context Cache | 30-min TTL per conversation |
| Law Browser | Search/browse corpus (free) |

---

## Config

| Setting | Value |
|---------|-------|
| GCP Project | `gen-lang-client-0225498420` |
| Region | `us-central1` |
| LLM | `gemini-3.1-pro` |
| Embeddings | `gemini-embedding-001` (768 dims) |
| ChromaDB | 3 collections: `georgian_laws` (15,338), `court_practice` (5,197), `grand_chamber` (177) |
| DB | PostgreSQL 16 (7 tables: users, credits, conversations, messages, case_files, credit_transactions, feedback) |
| State Machine | GREETING → INTAKE → CLARIFICATION → ANALYSIS → ADVICE → FOLLOW_UP |

---

## Running

```bash
# Local
cd backend && source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Docker
cd backend && docker compose up -d
docker compose exec api alembic upgrade head

# Tests
.venv/bin/python -m pytest tests/ -v  # 179 tests
```

---

## File Reference

| Task | Files |
|------|-------|
| Add endpoint | `routes/`, `schemas/`, register in `main.py` |
| Business logic | `services/` |
| DB queries | `repositories/` |
| Add DB table | `models/` → `alembic/env.py` → run migration |
| Change auth | `middleware/firebase_auth_middleware.py` |
| Change credits | `config/constants.py` → `CreditAction` |
| Change RAG | `config/constants.py` → `RAG_*` |
| Gemini prompts | `app/prompts/` |

---

## Gotchas

1. ChromaDB telemetry errors from posthog — harmless, ignore
2. Embedding consistency — corpus uses `RETRIEVAL_DOCUMENT`, queries MUST use `RETRIEVAL_QUERY`
3. Georgian text — always UTF-8 (Mkhedruli U+10D0–U+10FF)
4. Dev mode — no Firebase token needed, mock ADMIN user
5. Credit gate — fails open in dev, closed in production
