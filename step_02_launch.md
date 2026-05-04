# 🚀 Step 02 Launch — Build the FastAPI Backend

> **Copy this entire file as a prompt to the AI agent that will build the backend.**

---

## Your Mission

Build the complete FastAPI backend for **"The Master of Law" (კანონის ოსტატი)** — an AI-powered legal advocate for Georgian citizens. The backend serves a Flutter app and is the brain of the system: it handles conversations, RAG retrieval from a pre-built law corpus, defense strategy generation via Gemini, Firebase auth, and a credit-based access system.

---

## What's Already Done — DO NOT REBUILD THESE

The **law corpus pipeline** is 100% complete. All data is ready for the backend to consume:

| Asset | Location | Details |
|-------|----------|---------|
| **ChromaDB vector store** | `law_corpus/data/chroma/` | 9,450 chunks, collection name: `georgian_laws`, cosine distance, 768-dim vectors |
| **Chunk JSON files** | `law_corpus/data/chunks/*.json` | 12 files (one per legal code), each containing a list of `LegalChunk` objects |
| **Embedding cache** | `law_corpus/data/embeddings/` | 9,450 `.emb.json` files + `_cache_index.json` |
| **Search indices** | `law_corpus/data/index/` | `article_index.json`, `code_index.json`, `domain_index.json` |
| **Pipeline code** | `law_corpus/pipeline/` | Scraper, parser, chunker, embedder, indexer — all working |

### Corpus Statistics
- **12 Georgian legal codes** indexed (Constitution, Civil Code, Criminal Code, etc.)
- **9,450 chunks** across **1,525 unique articles**
- **768-dimensional** embeddings via `gemini-embedding-001`
- Every chunk has: `source_url`, `article_url`, `document_number`, `citation_text` (for AI citations)

### ChromaDB Collection Schema
The backend will query `georgian_laws` collection. Each document has these metadata fields:
```
document_id, code_name, article_number, article_title, book, chapter,
chunk_index, token_count, is_current, content_hash,
source_url, article_url, document_number, adoption_date, citation_text
```

### How to Query ChromaDB (from the existing codebase)
```python
import chromadb
client = chromadb.PersistentClient(path="<path_to>/law_corpus/data/chroma")
collection = client.get_collection("georgian_laws")
results = collection.query(
    query_embeddings=[query_vector],  # 768-dim float list
    n_results=50,
    include=["documents", "metadatas", "distances"],
)
# results["ids"][0] → list of chunk_ids
# results["documents"][0] → list of chunk texts
# results["metadatas"][0] → list of metadata dicts
# results["distances"][0] → list of cosine distances
```

### How to Generate Query Embeddings (proven working code)
```python
from google import genai
from google.genai.types import EmbedContentConfig

client = genai.Client(
    vertexai=True,
    project="gen-lang-client-0225498420",
    location="us-central1",
)
result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=["your query text"],
    config=EmbedContentConfig(
        task_type="RETRIEVAL_QUERY",   # IMPORTANT: use RETRIEVAL_QUERY for search
        output_dimensionality=768,
    ),
)
query_vector = list(result.embeddings[0].values)
```

---

## GCP & Auth Configuration (verified working)

| Setting | Value |
|---------|-------|
| **GCP Project** | `gen-lang-client-0225498420` |
| **Region** | `us-central1` |
| **Embedding Model** | `gemini-embedding-001` (768 dims, via `google-genai` SDK) |
| **LLM Model** | `gemini-2.5-pro` (for legal analysis — via `google-genai` SDK) |
| **Embedding SDK** | `google-genai` with `vertexai=True` (NOT deprecated `google-cloud-aiplatform`) |
| **Auth** | `gcloud auth application-default login` (ADC — already configured) |
| **Python** | 3.11 (Homebrew: `/opt/homebrew/opt/python@3.11/bin/python3.11`) |

> **⚠️ CRITICAL SDK NOTE:** Use the `google-genai` package (import as `from google import genai`).
> Do NOT use the deprecated `google-cloud-aiplatform` / `vertexai` SDK. The law corpus pipeline
> already uses `google-genai` successfully. The backend MUST use the same SDK for consistency.

> **⚠️ MODEL NOTE:** The backend spec references `gemini-3.1-pro` but the actual available model
> is `gemini-2.5-pro`. Use `gemini-2.5-pro` for the legal analysis LLM. For embeddings,
> use `gemini-embedding-001` (same model as the corpus, RETRIEVAL_QUERY task type for search).

---

## Project Location & Structure

**Working directory:** `/Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/`

Create the backend in `backend/` at the project root (sibling to `law_corpus/` and `master_plan/`):

```
the_master_of_law/
├── master_plan/                        # Design docs (READ for detailed specs)
│   ├── 02_backend_system_prompt.md     # ★ FULL 863-line backend spec — READ THIS
│   └── ...
├── law_corpus/                         # ✅ DONE — pipeline + data
│   ├── data/chroma/                    # ChromaDB with 9,450 chunks
│   ├── data/chunks/                    # Raw chunk JSON files
│   ├── data/index/                     # Search indices
│   └── pipeline/                       # Pipeline code (reference for models)
│
└── backend/                            # ★ CREATE THIS — the FastAPI app
    ├── Dockerfile
    ├── docker-compose.yml
    ├── pyproject.toml
    ├── alembic.ini
    ├── .env.example
    ├── .env
    ├── README.md
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                     # FastAPI app factory
    │   ├── dependencies.py             # Shared DI providers
    │   ├── config/
    │   │   ├── settings.py             # Pydantic BaseSettings
    │   │   └── constants.py            # Tier definitions, credit costs
    │   ├── models/                     # SQLAlchemy models (one per file)
    │   ├── schemas/                    # Pydantic v2 request/response DTOs
    │   ├── routes/                     # FastAPI routers
    │   ├── services/                   # Business logic
    │   ├── repositories/              # Data access
    │   ├── middleware/                 # Auth, credits, rate limit, CORS, errors
    │   ├── integrations/              # Firebase, Gemini, ChromaDB clients
    │   └── utils/                     # Logger, security, Georgian text utils
    ├── alembic/
    └── tests/
```

---

## Detailed Spec Reference

**READ `master_plan/02_backend_system_prompt.md` for the full 863-line specification.** It contains:

- Architecture principles (Clean Architecture, DI, async-first)
- Complete project structure with every file listed
- Conversation Orchestrator with 6-phase state machine
- Intake Flow Service with Georgian intake questions
- **5-stage RAG Pipeline** (detailed below)
- Legal Analysis Engine with full Gemini system prompt
- Citation Service for verifying law references
- Context Caching strategy (Vertex AI CachedContent)
- Defense Case Builder (structured case file generation)
- Credit System with 3 tiers (FREE/PRO/ADMIN)
- Firebase Authentication flow
- All API endpoints
- Docker + docker-compose setup
- Database schema (PostgreSQL)
- Full deliverables checklist

---

## Core Feature: 5-Stage RAG Pipeline

This is the heart of the backend. Implement exactly this flow:

```
User Message
  → [Stage 0] AI Query Expansion
      Gemini generates 5-10 formal Georgian legal search terms from casual user input
      Example: "მეზობელმა დამარტყა" → ["ჯანმრთელობის განზრახ მძიმე დაზიანება",
      "ფიზიკური შეურაცხყოფა ცემა", "თავდაცვა აუცილებელი მოგერიება", ...]

  → [Stage 1] Multi-Query Vector Search
      Each expanded query → embed with gemini-embedding-001 (RETRIEVAL_QUERY)
      → ChromaDB query top-50 per query

  → [Stage 2] Multi-Query Full-Text Search
      Each expanded query → search the JSON inverted indices
      → top-50 per query

  → [Stage 3] Merge & Deduplicate
      Combine all results from stages 1+2, deduplicate by chunk_id

  → [Stage 4] Gemini Rerank
      Send merged candidates to Gemini, select top-20 most relevant
      → Return chunks with full metadata (code_name, article_number, citation_text, etc.)
```

---

## Credit System

| Tier | Credits | Rate Limit | How assigned |
|------|---------|------------|--------------|
| FREE | 5/day (auto-reset midnight) | 5 req/min | Default on sign-up |
| PRO | Purchased | 30 req/min | Future in-app purchase |
| ADMIN | 10,000 one-time | 120 req/min | Manual DB grant |

| Action | Cost |
|--------|------|
| Chat message (AI response) | 1 credit |
| Deep legal analysis | 2 credits |
| Build Defense Case File | 3 credits |
| Browse/search laws | 0 (always free) |

---

## API Endpoints

```
POST   /api/v1/auth/verify-token
GET    /api/v1/auth/me

GET    /api/v1/account/credits
GET    /api/v1/account/transactions

POST   /api/v1/conversations
GET    /api/v1/conversations
GET    /api/v1/conversations/{id}
DELETE /api/v1/conversations/{id}

POST   /api/v1/chat/{conversation_id}/send     # 1 credit
WS     /api/v1/chat/{conversation_id}/ws       # streaming

GET    /api/v1/laws/search?q=...&domain=...    # free
GET    /api/v1/laws/codes                       # free
GET    /api/v1/laws/codes/{code_id}             # free
GET    /api/v1/laws/articles/{article_id}       # free

GET    /api/v1/health
GET    /api/v1/health/ready
```

---

## Key Dependencies

```toml
[project]
name = "master-of-law-backend"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.9",
    "pydantic-settings>=2.5",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "google-genai>=1.0",
    "firebase-admin>=6.5",
    "chromadb>=0.5",
    "redis>=5.0",
    "httpx>=0.27",
    "structlog>=24.0",
    "python-multipart>=0.0.9",
    "tenacity>=9.0",
    "orjson>=3.10",
]
```

> **NOTE:** Use `google-genai` (NOT `google-cloud-aiplatform`). The backend spec lists the
> deprecated package — we already migrated during the corpus pipeline. Stay consistent.

---

## Known Gotchas & Decisions

1. **ChromaDB path:** The backend must point to `../law_corpus/data/chroma/` (relative from `backend/`), or use an absolute path / env var. The ChromaDB data is pre-built and read-only for the backend.

2. **Embedding model consistency:** The corpus was embedded with `gemini-embedding-001` at 768 dimensions with `task_type="RETRIEVAL_DOCUMENT"`. Query embeddings MUST use the same model at 768 dimensions but with `task_type="RETRIEVAL_QUERY"`. Mismatched models = garbage search results.

3. **google-genai SDK pattern:**
   ```python
   from google import genai
   client = genai.Client(vertexai=True, project="gen-lang-client-0225498420", location="us-central1")
   # For chat: client.models.generate_content(model="gemini-2.5-pro", ...)
   # For embeddings: client.models.embed_content(model="gemini-embedding-001", ...)
   ```

4. **Rate limits:** The GCP project has ~12 RPM for embedding API calls. The backend should cache query embeddings or use conservative rate limiting for the RAG pipeline.

5. **Georgian text:** All legal text is in Georgian (Mkhedruli script, U+10D0–U+10FF). The system must handle UTF-8 correctly everywhere. Never use ASCII-only operations.

6. **Vertex AI telemetry errors in ChromaDB:** You'll see `"Failed to send telemetry event"` errors from ChromaDB — these are harmless (posthog telemetry, not affecting functionality). Ignore them.

7. **For development:** Start simple. Get the core flow working first:
   - Health check endpoint → ChromaDB connection → Query embedding → Vector search → Gemini analysis
   - Then layer on: Auth middleware → Credit system → Conversation state → Case builder

---

## Build Order (suggested phased approach)

### Phase 1 — Foundation (get the server running)
- [ ] Project scaffolding: `backend/` with pyproject.toml, app structure
- [ ] `app/config/settings.py` — Pydantic BaseSettings with all env vars
- [ ] `app/main.py` — FastAPI app factory with CORS, error handling
- [ ] `app/routes/health_router.py` — `/health` and `/health/ready`
- [ ] `app/integrations/chroma_client.py` — ChromaDB connection to existing data
- [ ] `app/integrations/vertex_embedding_client.py` — Query embedding via google-genai
- [ ] Verify: server starts, health OK, can query ChromaDB

### Phase 2 — RAG Pipeline (the core feature)
- [ ] `app/services/rag_retrieval_service.py` — All 5 stages
- [ ] `app/integrations/vertex_ai_client.py` — Gemini 2.5 Pro wrapper
- [ ] `app/services/legal_analysis_service.py` — System prompt + grounded generation
- [ ] `app/services/citation_service.py` — Verify citations against corpus
- [ ] `app/routes/chat_router.py` — `POST /chat/{id}/send`
- [ ] `app/routes/law_browser_router.py` — Free law browsing endpoints

### Phase 3 — Auth & Credits
- [ ] `app/integrations/firebase_client.py` — Firebase Admin SDK
- [ ] `app/middleware/firebase_auth_middleware.py` — Token verification
- [ ] `app/models/` — SQLAlchemy models (user, credits, conversation, message)
- [ ] `app/services/credit_service.py` — Tier logic, deduction, daily reset
- [ ] `app/middleware/credit_gate_middleware.py` — Block when credits exhausted
- [ ] `app/middleware/rate_limit_middleware.py` — Per-tier rate limiting
- [ ] Database setup: docker-compose (PostgreSQL + Redis), Alembic migrations

### Phase 4 — Conversations & Polish
- [ ] `app/services/conversation_service.py` — State machine orchestrator
- [ ] `app/services/intake_flow_service.py` — Guided intake questions
- [ ] `app/routes/conversation_router.py` — CRUD endpoints
- [ ] WebSocket streaming for `/chat/{id}/ws`
- [ ] Docker multi-stage build
- [ ] README with API docs
- [ ] Tests for critical services

---

## How to Start

```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law

# 1. Create the backend directory
mkdir -p backend

# 2. Read the full spec for details
cat master_plan/02_backend_system_prompt.md

# 3. Also reference the existing pipeline models for LegalChunk schema
cat law_corpus/pipeline/models/legal_chunk.py

# 4. Reference the working ChromaDB search interface
cat law_corpus/pipeline/indexer/vector_store_indexer.py

# 5. Reference the working embedding code
cat law_corpus/pipeline/embedder/vertex_embedder.py
```

**Start building Phase 1 now. Get the server running with a health check and ChromaDB query proof-of-concept first.**
