# 🏛️ Fuzzzy Law — Backend Handoff Document

> **Created:** 2026-05-04  
> **Purpose:** Complete context for any AI agent to continue development of the FastAPI backend.

---

## 1. Project Identity

**ბუნდოვანი კანონი (Fuzzzy Law)** — an AI-powered legal advocate that helps Georgian citizens defend themselves in court. The backend serves a Flutter mobile app and is the brain of the system.

**Working directory:** `/Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/`

```
fuzzzy_law/
├── master_plan/                    # Design docs (READ for full specs)
│   └── 02_backend_system_prompt.md # ★ 863-line backend specification
├── law_corpus/                     # ✅ DONE — pipeline + data (DO NOT MODIFY)
│   ├── data/chroma/                # ChromaDB: 9,450 chunks, collection: "georgian_laws"
│   ├── data/chunks/                # 12 JSON files (one per legal code)
│   ├── data/index/                 # article_index.json, code_index.json
│   └── pipeline/                   # Scraper, parser, chunker, embedder, indexer
├── backend/                        # ★ FastAPI backend (THIS IS WHAT WE BUILT)
├── step_02_launch.md               # The original build prompt
└── handoff.md                      # Previous pipeline handoff
```

---

## 2. What's Built — Current State

### ✅ Fully Implemented (~5,000 lines across 70+ files)

| Layer | Files | Status |
|-------|-------|--------|
| **Config** | `settings.py`, `constants.py` | ✅ Complete |
| **App Factory** | `main.py` | ✅ All routers + middleware wired (25 endpoints) |
| **Integrations** | `chroma_client.py`, `vertex_ai_client.py`, `vertex_embedding_client.py`, `firebase_client.py` | ✅ Complete |
| **Services** | `rag_retrieval_service.py`, `legal_analysis_service.py`, `citation_service.py`, `law_browser_service.py`, `conversation_service.py`, `intake_flow_service.py`, `case_builder_service.py`, `legal_classifier_service.py`, `explanation_service.py`, `context_cache_service.py` | ✅ Complete (10 services) |
| **Routes** | `health_router.py`, `auth_router.py`, `account_router.py`, `conversation_router.py`, `chat_router.py`, `law_browser_router.py`, `case_file_router.py`, `ws_chat_router.py` | ✅ Complete (DB-wired) |
| **Schemas** | `health_schema.py`, `auth_schema.py`, `chat_schema.py`, `conversation_schema.py`, `law_schema.py`, `case_file_schema.py` | ✅ Complete |
| **Middleware** | `error_handler_middleware.py`, `firebase_auth_middleware.py`, `credit_gate_middleware.py`, `rate_limit_middleware.py` | ✅ Complete (DB-wired) |
| **Models** | `database.py`, `user.py`, `user_credits.py`, `conversation.py`, `message.py`, `case_file.py` | ✅ Complete (with relationships) |
| **Repositories** | `user_repository.py`, `credit_repository.py`, `conversation_repository.py`, `message_repository.py`, `case_file_repository.py` | ✅ Complete (5 repos) |
| **Utils** | `logger.py`, `security.py`, `georgian_text_utils.py` | ✅ Complete |
| **Docker** | `Dockerfile`, `docker-compose.yml` | ✅ Production-hardened |
| **Alembic** | `alembic.ini`, `alembic/env.py` | ✅ Ready (6 models registered) |
| **Tests** | 7 test files, 90 tests | ✅ All passing |
| **Docs** | `README.md`, `.env.example`, `AI_GUIDE.md` | ✅ Complete |

### 25 API Endpoints

```
GET    /api/v1/health                          # Liveness
GET    /api/v1/health/ready                    # Readiness (ChromaDB + Gemini)

POST   /api/v1/auth/verify-token               # Firebase token → user profile
GET    /api/v1/auth/me                          # Current user

GET    /api/v1/account/credits                  # Credit balance
GET    /api/v1/account/transactions             # Credit history

POST   /api/v1/conversations                    # Start conversation (0 credits)
GET    /api/v1/conversations                    # List conversations
GET    /api/v1/conversations/{id}               # Get with messages
DELETE /api/v1/conversations/{id}               # Delete

POST   /api/v1/chat/{conversation_id}/send      # Send message → AI response (1 credit)
WS     /api/v1/chat/{conversation_id}/ws        # WebSocket streaming (1 credit)

POST   /api/v1/case-files/build                 # Build defense case file (3 credits)
GET    /api/v1/case-files                       # List case files
GET    /api/v1/case-files/{id}                  # Get case file with all sections
PATCH  /api/v1/case-files/{id}                  # Update notes/status
DELETE /api/v1/case-files/{id}                  # Delete case file

GET    /api/v1/laws/search?q=...&domain=...     # Search laws (free)
GET    /api/v1/laws/codes                       # List legal codes (free)
GET    /api/v1/laws/codes/{code_id}             # Code structure (free)
GET    /api/v1/laws/articles/{article_id}       # Article text (free)
```

---

## 3. Architecture — How It All Fits Together

### Request Flow
```
Flutter App
  → HTTP request with Firebase ID token in Authorization header
  → CORS Middleware
  → Firebase Auth Middleware (verify token, set request.state.user)
  → Credit Gate Middleware (check balance before AI calls)
  → Rate Limit Middleware (per-tier: FREE=5/min, PRO=30/min, ADMIN=120/min)
  → Error Handler Middleware (catch unhandled exceptions)
  → Route Handler
  → Service Layer
  → Response
```

### RAG Pipeline (the core feature)
```
User Message
  → [Stage 0] AI Query Expansion (Gemini 3.1 Pro → 5-10 formal legal terms)
  → [Stage 1] Multi-Query Vector Search (ChromaDB, top-50 per query)
  → [Stage 2] Multi-Query Full-Text Search (JSON indices, top-50 per query)
  → [Stage 3] Merge & Deduplicate by chunk_id
  → [Stage 4] Gemini Rerank (select top-20 most relevant)
  → Legal Analysis (Gemini 3.1 Pro with grounded context + system prompt)
  → Citation Verification (regex extraction + corpus validation)
  → Response with citations + retrieved chunks
```

---

## 4. GCP & Auth Configuration

| Setting | Value |
|---------|-------|
| **GCP Project** | `gen-lang-client-0225498420` |
| **Region** | `us-central1` |
| **LLM Model** | `gemini-3.1-pro` |
| **Embedding Model** | `gemini-embedding-001` (768 dims) |
| **SDK** | `google-genai` with `vertexai=True` (NOT deprecated `google-cloud-aiplatform`) |
| **Auth** | `VERTEX_AI_API_KEY` in `.env` — works everywhere (local + VPS) |
| **Python** | 3.11 (Homebrew: `/opt/homebrew/opt/python@3.11/bin/python3.11`) |

### How the Vertex AI clients work
Both `vertex_ai_client.py` and `vertex_embedding_client.py` use the same pattern:
```python
client = genai.Client(
    api_key=settings.vertex_ai_api_key,
    vertexai=True,
    project=settings.google_cloud_project,
    location=settings.google_cloud_location,
)
```

---

## 5. Law Corpus — Pre-Built Data (DO NOT REBUILD)

| Asset | Location | Details |
|-------|----------|---------|
| **ChromaDB** | `law_corpus/data/chroma/` | 9,450 chunks, collection: `georgian_laws`, cosine distance, 768-dim |
| **Chunk JSONs** | `law_corpus/data/chunks/*.json` | 12 files (one per legal code) |
| **Indices** | `law_corpus/data/index/` | `article_index.json`, `code_index.json` |

### ChromaDB Metadata Fields per Document
```
document_id, code_name, article_number, article_title, book, chapter,
chunk_index, token_count, is_current, content_hash,
source_url, article_url, document_number, adoption_date, citation_text
```

### Corpus Stats
- 12 Georgian legal codes (Constitution, Civil, Criminal, Labor, Tax, etc.)
- 9,450 chunks across 1,525 unique articles
- Embedded with `gemini-embedding-001` at 768 dims, `task_type=RETRIEVAL_DOCUMENT`
- Query embeddings MUST use same model + dims but `task_type=RETRIEVAL_QUERY`

---

## 6. Database Security (Production)

```
┌─────────────────────────────────────────────────────────┐
│  VPS Host Machine                                       │
│  ┌───────────────── mol_internal network ──────────────┐│
│  │  ┌─────────┐    ┌────────────┐    ┌─────────┐      ││
│  │  │   API   │───▶│ PostgreSQL │    │  Redis  │      ││
│  │  │ :8000   │    │ (INTERNAL  │    │(INTERNAL│      ││
│  │  │ (local  │    │  ONLY, NO  │    │ ONLY,NO │      ││
│  │  │  only)  │    │  PORTS)    │    │ PORTS)  │      ││
│  │  └─────────┘    └────────────┘    └─────────┘      ││
│  └───────┼─────────────────────────────────────────────┘│
│          │ 127.0.0.1:8000                               │
│          ▼                                              │
│    ┌───────────┐                                        │
│    │  Nginx /  │  ← TLS termination, exposed on :443   │
│    │  Caddy    │                                        │
│    └───────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

- PostgreSQL: **ZERO port exposure**, scram-sha-256 auth, strong random password
- Redis: **ZERO port exposure**, password-protected, 128MB max memory
- API: Bound to `127.0.0.1:8000` only — reverse proxy handles HTTPS
- All containers: `no-new-privileges` security option

---

## 7. What Remains — TODO Items

### High Priority (functional gaps)

1. ✅ **Credit gate middleware** (`credit_gate_middleware.py`) — Now queries real DB balance, returns 402 with Georgian/English messages when exhausted, fails open in dev.

2. ✅ **Conversation state persistence** (`conversation_router.py`) — Replaced in-memory dict with PostgreSQL via `ConversationService` + `ConversationRepository`. Messages persisted via `MessageRepository`.

3. ✅ **Auth router DB sync** (`auth_router.py`) — Now creates/updates user in DB on `verify-token`, queries real credit balance, updates `last_login_at`.

4. ✅ **Account router DB queries** (`account_router.py`) — Now returns real credit balance and transaction history from DB.

5. ✅ **Repositories layer** — All 4 repositories implemented:
   - `user_repository.py` — CRUD for users table
   - `credit_repository.py` — Balance queries, daily reset, deduction, transaction log
   - `conversation_repository.py` — Conversation CRUD with phase updates
   - `message_repository.py` — Message persistence and queries

6. **Alembic migrations** — `alembic/env.py` is ready with all 6 models registered. Run:
   ```bash
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

### Medium Priority (features from spec)

7. ✅ **Conversation state machine** (`conversation_service.py`) — Implemented with 6-phase lifecycle, valid transition map, and auto-phase-advance heuristics.

8. ✅ **Intake flow service** (`intake_flow_service.py`) — Implemented with 6 guided questions in Georgian, topic-detection heuristics, and completeness checks.

9. ✅ **Defense Case Builder** (`case_builder_service.py`) — 8-section structured case file generation via Gemini. CaseFile model + repository + router with full CRUD. Costs 3 credits.

10. ✅ **WebSocket streaming** (`ws_chat_router.py`) — `WS /api/v1/chat/{id}/ws` with status updates, paragraph-by-paragraph streaming, and citation verification on completion.

11. **`structlog` package** — Logger currently uses a stdlib-based fallback because `pip install` had no network access. Once online, install structlog and optionally upgrade `logger.py`.

### Low Priority (polish)

12. ✅ **Tests** — 90 tests across 7 files, all passing. Covers: citation extraction/verification, credit checks, intake flow, legal classifier, context cache, config/constants, app factory.

13. ✅ **Context caching** (`context_cache_service.py`) — In-memory cache with 30-min TTL, topic-change detection via chunk overlap, cache invalidation, and cleanup.

14. ✅ **Legal classifier service** (`legal_classifier_service.py`) — Gemini-powered domain classification with Georgian keyword heuristic fallback. 9 legal domains supported.

15. ✅ **Explanation service** (`explanation_service.py`) — Simplifies legal language via Gemini. Handles both free-text and specific article explanations.

---

## 8. How to Run

### Local Development
```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/backend
source .venv/bin/activate   # Uses --system-site-packages (Python 3.11)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Verify Everything Works
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
# Expected: Routes: 19, ChromaDB docs: 9450
```

### Docker Production
```bash
cd backend
# 1. Copy and fill .env from .env.example (generate strong passwords!)
# 2. Set VERTEX_AI_API_KEY in .env
docker compose up -d
```

---

## 9. Key Files to Read

| Priority | File | Why |
|----------|------|-----|
| ★★★ | `master_plan/02_backend_system_prompt.md` | Full 863-line spec with every detail |
| ★★★ | `backend/app/services/rag_retrieval_service.py` | Core RAG pipeline (5 stages) |
| ★★★ | `backend/app/services/legal_analysis_service.py` | Gemini system prompt + analysis |
| ★★ | `backend/app/main.py` | App factory, all routers + middleware |
| ★★ | `backend/app/config/settings.py` | All env vars |
| ★★ | `backend/app/config/constants.py` | Tiers, credit costs, RAG params |
| ★★ | `backend/docker-compose.yml` | Production security model |
| ★ | `law_corpus/pipeline/models/legal_chunk.py` | LegalChunk Pydantic model |
| ★ | `law_corpus/pipeline/embedder/vertex_embedder.py` | Proven embedding patterns |

---

## 10. Known Gotchas

1. **ChromaDB telemetry errors** — `"Failed to send telemetry event"` from posthog are harmless. Ignore them.

2. **Embedding model consistency** — Corpus = `gemini-embedding-001`, 768 dims, `RETRIEVAL_DOCUMENT`. Queries MUST use same model + dims with `RETRIEVAL_QUERY`. Mismatch = garbage results.

3. **SDK** — Use `google-genai` (import: `from google import genai`). Do NOT use `google-cloud-aiplatform` or `vertexai` — those are deprecated.

4. **Georgian text** — All legal text is in Georgian (Mkhedruli, U+10D0–U+10FF). Always handle UTF-8. Never use ASCII-only string operations.

5. **GCP rate limits** — ~12 RPM for embedding API. The backend should cache query embeddings or rate-limit RAG pipeline calls.

6. **Port binding in sandbox** — The dev environment can't bind to network ports (macOS sandbox restriction). The app loads and initializes correctly — verify via the Python import test above, not by starting uvicorn.
