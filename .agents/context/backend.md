# Backend Context — The Master of Law

> FastAPI backend with multi-source RAG pipeline + Gemini 3.1 Pro legal analysis.
> **Last verified:** 2026-05-12

---

## Architecture

```
Flutter App → HTTP/WS with Firebase ID token (or API key)
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

## Codebase Stats

| Metric | Count |
|--------|-------|
| Python files | 90 |
| Lines of code | ~10,261 |
| Router files | 14 |
| Endpoints | 38 |
| Services | 15 |
| Repositories | 7 |
| Models | 8 |
| Schemas | 9 |
| Test files | 24 |
| Test functions | 204 |

---

## API Endpoints (36 total, 13 routers)

### health_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/health` | 0 | Liveness |
| GET | `/api/v1/health/ready` | 0 | Readiness (reports collection count) |

### auth_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/auth/verify-token` | 0 | Firebase token → user |
| GET | `/api/v1/auth/me` | 0 | Current user |

### account_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/account/credits` | 0 | Credit balance |
| GET | `/api/v1/account/transactions` | 0 | Credit history |

### conversation_router (4)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/conversations` | 0 | Start conversation |
| GET | `/api/v1/conversations` | 0 | List conversations |
| GET | `/api/v1/conversations/{id}` | 0 | Get with messages |
| DELETE | `/api/v1/conversations/{id}` | 0 | Delete |

### chat_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/chat/{id}/send` | **1** | Send → AI response (accepts `rag_config`) |

### ws_chat_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| WS | `/api/v1/chat/{id}/ws` | 1 | WebSocket streaming (accepts `rag_config`) |

### case_file_router (6)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/case-files/build` | **3** | Build defense case (accepts `rag_config`) |
| GET | `/api/v1/case-files` | 0 | List case files |
| GET | `/api/v1/case-files/{id}` | 0 | Get case file |
| PATCH | `/api/v1/case-files/{id}` | 0 | Update notes/status |
| DELETE | `/api/v1/case-files/{id}` | 0 | Delete case file |
| POST | `/api/v1/case-files/{id}/generate-document` | **5** | Generate official DOCX document |

### case_agent_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/chat/{id}/agent` | — | AI agent interaction |
| POST | `/api/v1/chat/{id}/confirm-tool` | — | Tool confirmation |

### questionnaire_router (5)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/questionnaire/{id}/generate` | — | Generate questionnaire |
| GET | `/api/v1/questionnaire/{id}` | 0 | Get questionnaire state |
| POST | `/api/v1/questionnaire/{id}/answer` | — | Submit answer |
| POST | `/api/v1/questionnaire/{id}/skip` | — | Skip question |
| POST | `/api/v1/questionnaire/{id}/extract` | — | Extract case data |

### law_browser_router (4)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/laws/search?q=...` | 0 | Search laws (free) |
| GET | `/api/v1/laws/codes` | 0 | List codes |
| GET | `/api/v1/laws/codes/{id}` | 0 | Code structure |
| GET | `/api/v1/laws/articles/{id}` | 0 | Article text |

### feedback_router (5)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/feedback` | 0 | Submit feedback |
| GET | `/api/v1/feedback/summary` | 0 | Aggregated dashboard (ADMIN) |
| GET | `/api/v1/feedback/{target_id}` | 0 | Get feedback for target |
| PATCH | `/api/v1/feedback/{id}` | 0 | Update own feedback |
| DELETE | `/api/v1/feedback/{id}` | 0 | Delete own feedback |

### rag_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/rag/collections` | 0 | List RAG sources + availability |

### api_key_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/api-keys/check` | 0 | Check API key validity |
| POST | `/api/v1/api-keys` | 0 | Create API key (ADMIN) |

### contacts_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/contacts` | 0 | List beneficial official contacts |

---

## Services (15)

| Service | Purpose |
|---------|---------|
| rag_retrieval_service | 5-stage RAG pipeline |
| legal_analysis_service | Gemini system prompt + grounded analysis |
| citation_service | Extract `მუხლი N` patterns, verify against corpus |
| case_builder_service | 8-section defense case (3 credits) |
| case_tool_executor | Tool execution for case agent |
| conversation_service | State machine + message persistence |
| intake_flow_service | 6 guided questions in Georgian |
| questionnaire_service | Structured case intake questionnaire |
| legal_classifier_service | 9 legal domains classification |
| explanation_service | Simplify legal language |
| context_cache_service | 30-min TTL per conversation |
| law_browser_service | Search/browse corpus (free) |
| guardrail_service | Input/output safety checks |
| threshold_service | Credit threshold management |
| document_generator_service | AI drafts official documents to DOCX |

---

## Key Patterns

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

## Config

| Setting | Value |
|---------|-------|
| GCP Project | `gen-lang-client-0225498420` |
| Region | `us-central1` |
| LLM | `gemini-3.1-pro` |
| Embeddings | `gemini-embedding-001` (768 dims) |
| ChromaDB | 3 collections: `georgian_laws`, `court_practice`, `grand_chamber` |
| DB | PostgreSQL 16 (8 models: user, user_credits, conversation, message, case_file, feedback, questionnaire, database) |

---

## Running

```bash
# Local
cd backend && source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Docker
cd backend && docker compose up --build -d
docker compose exec api alembic upgrade head

# Tests
.venv/bin/python -m pytest tests/ -v  # 204 tests
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
