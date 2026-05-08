# Architecture Documentation

> **Last updated:** 2026-05-09

---

## High-Level System Diagram

```mermaid
flowchart TB
    subgraph Client["📱 Client Layer"]
        Flutter["Flutter App\n(master_of_law / themasteroflaw)\n5 tabs: Chat | Cases | Laws | Notes | Profile"]
    end

    subgraph Edge["🌐 Edge Layer"]
        CORS["CORS Middleware"]
        FBAuth["Firebase Auth Middleware"]
        Credit["Credit Gate Middleware"]
        RateLimit["Rate Limit Middleware"]
        ErrorHandler["Error Handler Middleware"]
    end

    subgraph API["⚡ API Layer — FastAPI (Port 8000)"]
        Routes["Route Handlers\n(9 routers, 27+ endpoints)"]
        Services["Services\n(10 business logic services)"]
        Repositories["Repositories\n(5 data access layers)"]
        Models["SQLAlchemy Models\n(7 tables)"]
    end

    subgraph RAG["🔍 RAG Pipeline"]
        QE["Stage 0: Query Expansion\n(Gemini generates legal terms)"]
        VS["Stage 1: Vector Search\n(ChromaDB, top-50 per query)"]
        FTS["Stage 2: Full-Text Search\n(JSON indices, top-50 per query)"]
        Merge["Stage 3: Merge & Deduplicate\n(by chunk_id)"]
        Rerank["Stage 4: Gemini Rerank\n(top-20 most relevant)"]
    end

    subgraph AI["🤖 AI Layer"]
        Gemini["Gemini 3.1 Pro\n(via Vertex AI / google-genai SDK)"]
        Embeddings["gemini-embedding-001\n(768-dim vectors)"]
    end

    subgraph Data["💾 Data Layer"]
        PG[("PostgreSQL 16\n6 tables + transactions")]
        Chroma[("ChromaDB\n3 collections\n20,712 chunks")]
        Redis[("Redis 7\nRate limit + credit cache")]
    end

    Flutter -->|"HTTPS / WebSocket\n+ Firebase ID Token"| CORS
    CORS --> FBAuth
    FBAuth --> Credit
    Credit --> RateLimit
    RateLimit --> ErrorHandler
    ErrorHandler --> Routes
    Routes --> Services
    Services --> Repositories
    Repositories --> Models
    Models --> PG

    Services --> RAG
    RAG --> Chroma
    RAG --> Gemini
    Gemini --> Embeddings

    RateLimit --> Redis
    Credit --> Redis
```

---

## Data Flow: User → Response

```mermaid
sequenceDiagram
    participant U as User
    participant F as Flutter App
    participant API as FastAPI Backend
    participant RAG as RAG Pipeline
    participant DB as ChromaDB
    participant AI as Gemini 3.1 Pro

    U->>F: "ჩემს მეზობელს სახლი დავანგრიე..."
    F->>API: POST /chat/{id}/send<br/>+ Firebase ID Token + RAGCollectionConfig

    API->>API: Firebase Auth → verify token<br/>Credit Gate → deduct 1 credit<br/>Rate Limit → check tier

    API->>RAG: retrieve(message, collections)
    RAG->>AI: Query Expansion:<br/>"Generate 5-10 formal Georgian legal terms"
    AI-->>RAG: ["ჯანმრთელობის დაზიანება", "საპროცესო შეთანხმება", ...]

    loop For each expanded query
        RAG->>DB: Vector search (top-50)
        RAG->>DB: Full-text search (top-50)
    end

    RAG->>RAG: Merge & deduplicate by chunk_id
    RAG->>AI: Rerank: "Select top-20 most relevant"
    AI-->>RAG: Ranked chunks with relevance scores
    RAG-->>API: Top-20 chunks with metadata

    API->>AI: Legal Analysis:<br/>user message + retrieved chunks + system prompt
    AI-->>API: Structured legal response

    API->>API: Citation Verification:<br/>Extract "მუხლი N" patterns → validate against corpus

    API-->>F: {response, citations, retrieved_chunks, credits_remaining}
    F-->>U: Formatted analysis with tappable citations
```

---

## Backend Layer Architecture

```
Route (thin) → Service (logic) → Repository (DB) → Model (ORM)
```

### Philosophy

- **Routes** handle HTTP concerns only: parsing requests, calling services, returning responses. Max 15 lines.
- **Services** contain all business logic. Singleton pattern. Never import SQLAlchemy.
- **Repositories** contain all database queries. One per model. Inject `AsyncSession`.
- **Models** are pure SQLAlchemy ORM definitions. One model per file.

### Example: Adding a new endpoint

See [`DEVELOPMENT.md`](./DEVELOPMENT.md) for the full workflow. The dependency chain is:

```python
# Route depends on Service
@router.post("/example")
async def example_endpoint(db: AsyncSession = Depends(get_db)):
    svc = MyService(db)  # Service receives db, creates Repository internally
    result = await svc.do_something()
    return result

# Service depends on Repository
class MyService:
    def __init__(self, db: AsyncSession):
        self.repo = MyRepository(db)

    async def do_something(self):
        return await self.repo.find_all()

# Repository depends on Model
class MyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self):
        result = await self.db.execute(select(MyModel))
        return result.scalars().all()
```

---

## Database Schema

```mermaid
erDiagram
    USER ||--o{ CONVERSATION : has
    USER ||--o{ USER_CREDITS : has
    USER ||--o{ CREDIT_TRANSACTION : has
    USER ||--o{ CASE_FILE : owns
    CONVERSATION ||--o{ MESSAGE : contains
    CONVERSATION ||--o{ QUESTIONNAIRE_ITEM : has
    CONVERSATION ||--o| CASE_FILE : generates

    USER {
        uuid id PK
        string firebase_uid UK
        string email
        string display_name
        string photo_url
        string tier "FREE|PRO|ADMIN"
        datetime created_at
        datetime updated_at
        datetime last_login_at
    }

    USER_CREDITS {
        uuid id PK
        uuid user_id FK
        string tier
        int credit_balance
        int daily_credits_used
        datetime daily_reset_at
        datetime created_at
        datetime updated_at
    }

    CREDIT_TRANSACTION {
        uuid id PK
        uuid user_id FK
        int amount
        string transaction_type
        string description
        datetime created_at
    }

    CONVERSATION {
        uuid id PK
        string user_id "Firebase UID"
        string title
        string phase "GREETING|INTAKE|..."
        string legal_domain
        datetime created_at
        datetime updated_at
    }

    MESSAGE {
        uuid id PK
        uuid conversation_id FK
        string role "user|assistant"
        text content
        jsonb citations
        jsonb retrieved_chunk_ids
        int credit_cost
        datetime created_at
    }

    CASE_FILE {
        uuid id PK
        string user_id "Firebase UID"
        uuid conversation_id FK
        string title
        jsonb facts
        jsonb evidence
        jsonb applicable_laws
        jsonb defense_strategies
        jsonb prosecution_args
        jsonb action_checklist
        jsonb lawyer_brief
        jsonb citations
        text rendered_text
        string status "draft|active|resolved"
        text user_notes
        datetime created_at
        datetime updated_at
    }

    QUESTIONNAIRE_ITEM {
        uuid id PK
        uuid conversation_id FK
        string question_id
        text question_text_ka
        string question_type
        jsonb options
        boolean required
        text purpose
        text legal_relevance
        int sort_order
        text answer_value
        boolean skipped
        datetime answered_at
        datetime created_at
    }
```

### Table Summary

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | Synced from Firebase Auth | `firebase_uid` (unique), `tier` |
| `user_credits` | Credit balance per user | `credit_balance`, `daily_credits_used`, `daily_reset_at` |
| `credit_transactions` | Audit log of all credit changes | `amount` (±), `transaction_type` |
| `conversations` | Chat sessions | `phase` (state machine), `legal_domain` |
| `messages` | Individual chat messages | `role`, `citations`, `retrieved_chunk_ids` |
| `case_files` | Structured defense documents | 8 JSONB sections + `rendered_text` |
| `questionnaire_items` | Dynamic intake questions | `question_text_ka`, `answer_value`, `skipped` |

---

## RAG Pipeline: 5 Stages

```mermaid
flowchart LR
    A["User Message + RAGCollectionConfig"] --> B["Stage 0:<br/>Query Expansion"]
    B --> C["Stage 1:<br/>Vector Search"]
    B --> D["Stage 2:<br/>Full-Text Search"]
    C --> E["Stage 3:<br/>Merge & Deduplicate"]
    D --> E
    E --> F["Stage 4:<br/>Gemini Rerank"]
    F --> G["Top-20 Chunks<br/>→ Legal Analysis"]
```

### Stage 0: Query Expansion
Users describe situations in everyday language. Gemini generates 5-10 formal Georgian legal search terms. Example:
- User: "მეზობელმა დამარტყა" (My neighbor hit me)
- Expanded: "ჯანმრთელობის განზრახ მძიმე დაზიანება", "თავდაცვა აუცილებელი მოგერიება", "ზიანის ანაზღაურება სამოქალაქო"

### Stage 1: Multi-Query Vector Search
Each expanded query is embedded with `gemini-embedding-001` (task_type=`RETRIEVAL_QUERY`) and searched against ChromaDB. Top-50 results per query per collection.

### Stage 2: Multi-Query Full-Text Search
Each expanded query is also searched via PostgreSQL full-text indices (where applicable) and JSON metadata indices. Top-50 results per query.

### Stage 3: Merge & Deduplicate
All results from Stage 1 and 2 are merged and deduplicated by `chunk_id`. This produces a broad candidate set (~100-200 unique chunks).

### Stage 4: Gemini Rerank
Gemini evaluates the candidate chunks against the user's original message and selects the top-20 most relevant. Counter-laws (articles against the user) are intentionally included.

### Source-Specific Prompt Injection
When `court_practice` or `grand_chamber` chunks are retrieved, additional instructions are injected into the system prompt:
- Court practice: "Supreme Court rulings show how courts have interpreted these laws"
- Grand Chamber: "Grand Chamber decisions are BINDING and override all lower court interpretations"

---

## ChromaDB: Collections and Querying

| Collection | Chunks | Description | Metadata Fields |
|------------|--------|-------------|-----------------|
| `georgian_laws` | 15,338 | 12 legal codes from matsne.gov.ge | `code_name`, `article_number`, `article_title`, `citation_text`, `source_url`, `article_url`, `document_number` |
| `court_practice` | 5,197 | Supreme Court rulings (2022–2026) | `case_id`, `category`, `year`, `section`, `chunk_index` |
| `grand_chamber` | 177 | Grand Chamber binding decisions | `case_id`, `category`, `year`, `norm_interpreted`, `binding_rule`, `section` |

### Querying via RAGCollectionConfig

Clients control which collections are searched per-request:

```python
# Default: all collections enabled
{"rag_config": {"legal_codes": true, "court_practice": true, "grand_chamber": true}}

# Criminal case — include court practice for precedent
{"rag_config": {"legal_codes": true, "court_practice": true, "grand_chamber": false}}

# Constitutional question — prioritize Grand Chamber
{"rag_config": {"legal_codes": true, "court_practice": false, "grand_chamber": true}}
```

> **Gotcha:** Query embeddings MUST use `RETRIEVAL_QUERY` task type. Corpus embeddings were built with `RETRIEVAL_DOCUMENT`. Mismatched task types severely degrade retrieval quality.

---

## Credit System

### Tiers

| Tier | Credits | Rate Limit | Source |
|------|---------|------------|--------|
| FREE | 5/day (auto-reset at midnight) | 5 req/min | Automatic on sign-up |
| PRO | Purchased (no daily reset) | 30 req/min | In-app purchase (future) |
| ADMIN | 10,000 (one-time) | 120 req/min | Manually granted |

### Credit Costs

| Action | Credits | Endpoint |
|--------|---------|----------|
| Chat message | 1 | `POST /chat/{id}/send` |
| Deep analysis | 2 | (future endpoint) |
| Build case file | 3 | `POST /case-files/build` |
| Update case file | 1 | `PATCH /case-files/{id}` |
| Browse/search laws | 0 | `GET /laws/*` |
| View conversation | 0 | `GET /conversations/*` |

### Flow

```
Request → Firebase Auth → Credit Gate → Rate Limit → Service Logic
                  │              │
                  │              └─ Check: enough credits? → 402 if no
                  └─ Verify token → 401 if invalid
```

> **Gotcha:** Credit gate fails OPEN in development (allows through if DB unavailable) and CLOSED in production (returns 503 if DB unavailable).

---

## Authentication: Firebase Auth → JWT → Middleware

```mermaid
sequenceDiagram
    participant F as Flutter App
    participant FB as Firebase Auth
    participant API as FastAPI Backend
    participant DB as PostgreSQL

    F->>FB: Sign in (Google / Email)
    FB-->>F: Firebase ID Token (JWT)
    F->>API: Authorization: Bearer <id_token>

    API->>API: FirebaseAuthMiddleware<br/>verify_id_token()<br/>→ decoded JWT
    API->>DB: Lookup user by firebase_uid<br/>→ get tier
    API->>API: request.state.user = {uid, email, tier}

    API->>API: CreditGateMiddleware<br/>check credits
    API->>API: RateLimitMiddleware<br/>check tier limit

    API-->>F: Protected response
```

### Public Endpoints (No Auth)

- `GET /api/v1/health`
- `GET /api/v1/health/ready`
- `GET /api/v1/laws/search`
- `GET /api/v1/laws/codes`
- `GET /api/v1/laws/codes/{id}`
- `GET /api/v1/laws/articles/{id}`
- `GET /docs` and `/redoc` (development only)

### Development Mode

When `APP_ENV=development`, unauthenticated requests are allowed with a mock user:
```python
{"uid": "dev-user-001", "email": "dev@masteroflaw.ge", "tier": "ADMIN"}
```

---

## Decision Logs

### Why FastAPI + SQLAlchemy (async)?
**Decision:** Use FastAPI with async SQLAlchemy + asyncpg.  
**Why:** All I/O operations (DB, ChromaDB, Vertex AI) are blocking. Async prevents the event loop from stalling during 15-30s Gemini calls. SQLAlchemy 2.0's async support is production-ready.

### Why ChromaDB (not Vertex AI Vector Search) for local/dev?
**Decision:** ChromaDB for development; Vertex AI Vector Search spec'd for production.  
**Why:** ChromaDB requires zero cloud infrastructure for local development. The pre-built corpus (`law_corpus/data/chroma/`) is portable and version-controllable. Production can switch to Vertex AI via `VECTOR_STORE_BACKEND` env var.

### Why 5-Stage RAG?
**Decision:** Query expansion → vector → full-text → merge → rerank.  
**Why:** Georgian legal terminology is highly formalized. Users describe situations colloquially. Query expansion bridges this gap. Vector search finds semantically similar articles. Full-text catches exact keyword matches. Reranking by Gemini ensures the final context is maximally relevant. Each stage addresses a different failure mode.

### Why Firebase Authentication?
**Decision:** Firebase Auth for user identity; backend only verifies tokens.  
**Why:** The backend NEVER handles passwords, email verification, or OAuth flows. Firebase handles all auth UI and security. The backend only validates JWTs and syncs user metadata (tier, credits).

### Why Credit System Instead of Subscriptions?
**Decision:** Per-action credit costs with a free daily allowance.  
**Why:** Georgian legal problems vary wildly in complexity. A simple question costs 1 credit; a full defense case file costs 3. Credits align cost with value. Free tier (5/day) is generous enough for user acquisition without requiring payment infrastructure for MVP.

### Why Case-Centric Architecture?
**Decision:** Everything links to a "case" (case file).  
**Why:** Users don't come to chat — they come to solve legal problems. The case file is the central organizing unit: facts, evidence, laws, strategies, deadlines. Everything connects to everything. See `master_plan/04_feature_roadmap.md` for the full vision.

### Why Gemini 3.1 Pro?
**Decision:** Gemini 3.1 Pro via Vertex AI.  
**Why:** Gemini has strong multilingual capabilities, including Georgian. Vertex AI provides enterprise features (caching, monitoring, SLAs) not available via the consumer AI Studio API. Temperature 0.1 ensures consistent, deterministic legal analysis.

### Why `google-genai` SDK (not `google-cloud-aiplatform`)?
**Decision:** Use `google-genai` exclusively.  
**Why:** The `google-genai` SDK is the modern, unified client for Gemini. `google-cloud-aiplatform` and `vertexai` are legacy packages with conflicting dependencies. The project standardizes on `google-genai>=1.0`.
