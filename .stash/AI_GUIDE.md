# 🤖 AI Agent Guide — The Master of Law

> **Read this first.** This document gives you everything you need to work on the codebase without reading every file. It's structured for fast onboarding.
> **Last updated:** 2026-05-05

---

## 1. What Is This Project?

**კანონის ოსტატი (The Master of Law)** — an AI-powered legal advocate that helps Georgian citizens defend themselves in court. The system consists of:

- **Law Corpus** (✅ DONE) — 9,450 chunks of Georgian legislation in ChromaDB
- **Backend** (✅ DONE) — FastAPI with 5-stage RAG pipeline, Gemini 3.1 Pro, 25 endpoints
- **Flutter App** (🔄 IN PROGRESS) — Mobile app with case-centric architecture
- **Design System** (🔄 IN PROGRESS) — Generating via open-design, injecting into Flutter ui_kit

**Working directory:** `/Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/`

---

## 2. Project Structure (What Goes Where)

```
the_master_of_law/
├── master_plan/                      # Design specs + roadmap
│   ├── 01_law_corpus_agent_prompt.md # ✅ Step 1 spec (DONE)
│   ├── 02_backend_system_prompt.md   # ✅ Step 2 spec (DONE)
│   ├── 03_design_system_prompt.md    # 🔄 Step 3 spec (IN PROGRESS)
│   ├── 04_feature_roadmap.md         # Feature roadmap (6 phases) + user needs
│   └── design/                       # Design assets + open-design brief
├── law_corpus/                       # ✅ DONE — DO NOT MODIFY
│   └── data/chroma/                  # ChromaDB: 9,450 chunks, "georgian_laws"
├── backend/                          # ✅ DONE — FastAPI backend
│   ├── app/
│   │   ├── main.py                   # App factory — entry point
│   │   ├── config/                   # settings.py, constants.py
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   ├── schemas/                  # Pydantic request/response DTOs
│   │   ├── routes/                   # FastAPI routers (REST + WebSocket)
│   │   ├── services/                 # Business logic layer (10 services)
│   │   ├── repositories/            # Data access layer (5 repos)
│   │   ├── middleware/               # Auth, credits, rate limit, errors
│   │   ├── integrations/            # Gemini, ChromaDB, Firebase
│   │   ├── prompts/                  # Typed prompt templates
│   │   └── utils/                    # Logger, security, Georgian text utils
│   ├── tests/                        # 124 tests passing
│   └── docker-compose.yml            # Production deployment
├── fuzzy_starter/                    # 🔄 Flutter app (package: master_of_law)
│   ├── lib/src/app/                  # MasterOfLawApp entry point
│   ├── lib/src/core/                 # DI, HTTP clients, l10n, extensions
│   ├── packages/ui_kit/              # Design system (colors, typography, themes)
│   └── packages/open-design/         # Open-design tool (cloned)
├── AI_GUIDE.md                       # ★ THIS FILE
├── current_steps.md                  # Overall progress tracker
├── RESUME_PROMPT.md                  # Session resume prompt
├── handoff.md                        # Backend handoff document
├── startup_handoff.md                # Backend startup guide
└── PRODUCTION_SETUP.md               # VPS deployment guide
```

---

## 3. Architecture — How Requests Flow

```
Flutter App → HTTP/WS with Firebase ID token
  → CORS Middleware
  → Firebase Auth Middleware (verify token, set request.state.user)
  → Credit Gate Middleware (check balance, return 402 if exhausted)
  → Rate Limit Middleware (per-tier: FREE=5/min, PRO=30/min, ADMIN=120/min)
  → Error Handler Middleware
  → Route Handler → Service → Repository → Response
```

### The RAG Pipeline (core feature)
```
User Message
  → [Stage 0] Gemini Query Expansion (5-10 formal legal terms in Georgian)
  → [Stage 1] Multi-Query Vector Search (ChromaDB, top-50 per query)
  → [Stage 2] Multi-Query Full-Text Search (JSON indices, top-50 per query)
  → [Stage 3] Merge & Deduplicate by chunk_id
  → [Stage 4] Gemini Rerank (select top-20 most relevant)
  → Legal Analysis (Gemini 3.1 Pro with system prompt + context)
  → Citation Verification (regex + corpus validation)
```

---

## 4. Key Patterns — Follow These When Adding Code

### 4.1 Layer Architecture
```
Route (thin) → Service (business logic) → Repository (DB) → Model (ORM)
```
- **Routes** only handle HTTP concerns — parsing request, calling service, returning response
- **Services** contain all business logic — never import SQLAlchemy in routes
- **Repositories** are the ONLY place that touches the database
- **Models** are pure SQLAlchemy ORM — no business logic

### 4.2 Dependency Injection Pattern
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db

@router.post("/endpoint")
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    repo = MyRepository(db)
    # ... use repo ...
    await db.commit()
```

### 4.3 Service Singleton Pattern
```python
_my_service = None

def get_my_service():
    global _my_service
    if _my_service is None:
        _my_service = MyService()
    return _my_service
```

### 4.4 Logging Pattern
```python
from app.utils.logger import get_logger
logger = get_logger(__name__)
logger.info("event_name", key="value", count=42)
```

### 4.5 Gemini API Pattern (google-genai SDK)
```python
from app.integrations.vertex_ai_client import get_vertex_ai_client

client = get_vertex_ai_client()
# Text generation:
response = await client.generate(prompt="...", system_instruction="...", temperature=0.1)
# JSON generation:
data = await client.generate_json(prompt="...", temperature=0.1)
```

---

## 5. API Endpoints (25 total)

| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/health` | 0 | Liveness |
| GET | `/api/v1/health/ready` | 0 | Readiness (ChromaDB + Gemini) |
| POST | `/api/v1/auth/verify-token` | 0 | Firebase token → user profile |
| GET | `/api/v1/auth/me` | 0 | Current user |
| GET | `/api/v1/account/credits` | 0 | Credit balance |
| GET | `/api/v1/account/transactions` | 0 | Credit history |
| POST | `/api/v1/conversations` | 0 | Start conversation |
| GET | `/api/v1/conversations` | 0 | List conversations |
| GET | `/api/v1/conversations/{id}` | 0 | Get with messages |
| DELETE | `/api/v1/conversations/{id}` | 0 | Delete |
| POST | `/api/v1/chat/{id}/send` | **1** | Send message → AI response |
| WS | `/api/v1/chat/{id}/ws` | 1 | WebSocket streaming |
| POST | `/api/v1/case-files/build` | **3** | Build defense case file |
| GET | `/api/v1/case-files` | 0 | List case files |
| GET | `/api/v1/case-files/{id}` | 0 | Get case file |
| PATCH | `/api/v1/case-files/{id}` | 0 | Update notes/status |
| DELETE | `/api/v1/case-files/{id}` | 0 | Delete case file |
| GET | `/api/v1/laws/search?q=...` | 0 | Search laws (free) |
| GET | `/api/v1/laws/codes` | 0 | List legal codes (free) |
| GET | `/api/v1/laws/codes/{id}` | 0 | Code structure (free) |
| GET | `/api/v1/laws/articles/{id}` | 0 | Article text (free) |

---

## 6. Credit System

| Tier | Credits | Rate Limit | Reset |
|------|---------|------------|-------|
| FREE | 5/day | 5 req/min | Midnight UTC |
| PRO | Purchased balance | 30 req/min | Never (depletes) |
| ADMIN | 10,000 | 120 req/min | N/A |

**Credit deduction happens AFTER successful response** (not before).
The credit gate middleware checks balance BEFORE processing.

---

## 7. Database

6 tables: `users`, `user_credits`, `credit_transactions`, `conversations`, `messages`, `case_files`

- **Engine**: PostgreSQL via asyncpg
- **ORM**: SQLAlchemy 2.x async
- **Migrations**: Alembic (env.py ready, run `alembic revision --autogenerate`)
- **Session**: `get_db()` dependency yields async sessions

---

## 8. GCP / Vertex AI Configuration

| Setting | Value |
|---------|-------|
| GCP Project | `gen-lang-client-0225498420` |
| Region | `us-central1` |
| LLM Model | `gemini-3.1-pro` |
| Embedding Model | `gemini-embedding-001` (768 dims) |
| SDK | `google-genai` with `vertexai=True` |
| Local auth | `gcloud auth application-default login` |
| Auth | `VERTEX_AI_API_KEY` in `.env` |

**CRITICAL**: Use `from google import genai`. Never use `google-cloud-aiplatform` or `vertexai`.

---

## 9. Running & Testing

### Local Development
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Quick Verification
```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from app.main import create_app
from app.integrations.chroma_client import get_chroma_client
app = create_app()
chroma = get_chroma_client()
routes = [r.path for r in app.routes if hasattr(r, 'path')]
print(f'Routes: {len(routes)}, ChromaDB docs: {chroma.count()}')
"
# Expected: Routes: 25, ChromaDB docs: 9450
```

### Run Tests
```bash
.venv/bin/python -m pytest tests/ -v
# Expected: 90 passed
```

### Docker Production
```bash
cd backend
# 1. Fill .env from .env.example with strong passwords
# 2. Set VERTEX_AI_API_KEY in .env
docker compose up -d
```

---

## 10. Law Corpus (DO NOT MODIFY)

- **Location**: `law_corpus/data/chroma/`
- **Collection**: `georgian_laws`, 9,450 chunks, 768-dim vectors, cosine distance
- **Content**: 12 Georgian legal codes (Constitution, Criminal, Civil, Labor, Tax, etc.)
- **Metadata per chunk**: `code_name`, `article_number`, `article_title`, `citation_text`, `article_url`, `source_url`
- **Query embedding**: Same model (`gemini-embedding-001`), same dims (768), but `task_type=RETRIEVAL_QUERY`

---

## 11. Known Gotchas

1. **ChromaDB telemetry errors** — `"Failed to send telemetry event"` from posthog are harmless
2. **Embedding consistency** — Corpus uses `gemini-embedding-001` 768-dim `RETRIEVAL_DOCUMENT`. Queries MUST match
3. **SDK** — `google-genai` only. NOT `google-cloud-aiplatform` or `vertexai`
4. **Georgian text** — UTF-8 always (Mkhedruli U+10D0–U+10FF). Never ASCII-only ops
5. **GCP rate limits** — ~12 RPM for embedding API
6. **Dev sandbox** — Can't bind to ports. Verify via Python import test, not uvicorn
7. **Credit gate** — Fails open in dev (no DB needed), fails closed in production
8. **State machine** — Phase transitions are advisory, not blocking (prevents deadlocks)

---

## 12. File Reference (Quick Lookup)

### When you need to...

| Task | Read/Edit These Files |
|------|----------------------|
| Add a new API endpoint | `routes/`, `schemas/`, then register in `main.py` |
| Add business logic | `services/` — create new or extend existing |
| Add DB queries | `repositories/` — one repo per model |
| Add a DB table | `models/` → update `alembic/env.py` imports → run migration |
| Change auth rules | `middleware/firebase_auth_middleware.py` |
| Change credit costs | `config/constants.py` → `CreditAction` + `_ACTION_COSTS` |
| Change rate limits | `config/constants.py` → `TIER_RATE_LIMITS` |
| Change RAG params | `config/constants.py` → `RAG_*` constants |
| Change Gemini settings | `config/constants.py` → `GEMINI_*` + `config/settings.py` |
| Add environment vars | `config/settings.py` → add field + update `.env.example` |
| Modify Gemini prompts | `services/legal_analysis_service.py` (system prompt) |
| Change RAG pipeline | `services/rag_retrieval_service.py` |
| Change credit gating | `middleware/credit_gate_middleware.py` → `CREDIT_ROUTES` |

---

## 13. Conversation State Machine

```
GREETING → INTAKE → CLARIFICATION → ANALYSIS → ADVICE → FOLLOW_UP
                ↗                       ↗                    ↩
```

- **GREETING**: Welcome, first message
- **INTAKE**: Guided questions (6 questions in Georgian)
- **CLARIFICATION**: Follow-ups for missing details
- **ANALYSIS**: RAG retrieval + Gemini analysis
- **ADVICE**: Present findings with citations
- **FOLLOW_UP**: Additional questions about the analysis

Managed by `ConversationService.transition_phase()` and `determine_next_phase()`.

---

## 14. Services Overview

| Service | File | Purpose |
|---------|------|---------|
| RAG Retrieval | `rag_retrieval_service.py` | 5-stage pipeline: expand → vector → fulltext → merge → rerank |
| Legal Analysis | `legal_analysis_service.py` | Gemini system prompt + grounded analysis |
| Citation | `citation_service.py` | Extract `მუხლი N` patterns, verify against corpus |
| Case Builder | `case_builder_service.py` | 8-section defense case file generation (3 credits) |
| Conversation | `conversation_service.py` | State machine + message persistence |
| Intake Flow | `intake_flow_service.py` | 6 guided questions in Georgian |
| Legal Classifier | `legal_classifier_service.py` | Detect legal domain (9 domains, Gemini + heuristic) |
| Explanation | `explanation_service.py` | Simplify legal language for laypersons |
| Context Cache | `context_cache_service.py` | Cache law chunks per conversation (30-min TTL) |
| Law Browser | `law_browser_service.py` | Search/browse law corpus (free, no credits) |
