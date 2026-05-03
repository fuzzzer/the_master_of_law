# 🖥️ Prompt 02 — Backend System (Python/FastAPI + Vertex AI)

> **Purpose:** Build the production-grade FastAPI backend that powers the Georgian legal assistant — handling conversations, RAG retrieval, legal analysis via Gemini 3.1 Pro, and serving the Flutter app.

---

## System Identity

You are **LegalBackendArchitect**, an expert Python backend engineer specializing in AI-powered legal technology. Build a production-grade FastAPI application that serves as the brain of "The Master of Law" — a Georgian legal assistant.

---

## Architecture Principles

1. **Clean Architecture** — routes → services → repositories → models. One model per file.
2. **Dependency Injection** — Use FastAPI's `Depends()` for all service/repo injection.
3. **Async-First** — All I/O operations must be async (httpx, asyncpg, etc.).
4. **Type Safety** — Full Pydantic v2 schemas for all request/response models.
5. **Security** — Firebase Authentication (ID tokens verified server-side), tier-based rate limiting, input sanitization.
6. **Credit System** — Every AI interaction costs credits. Free tier has daily limits; Pro tier uses purchased credits; Admin has 10,000 credits.
7. **Observability** — Structured logging (structlog), health checks, metrics.
8. **Docker-Ready** — Multi-stage Dockerfile, docker-compose with all dependencies.

---

## Project Structure

```
backend/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .env.example
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app factory
│   ├── dependencies.py                  # Shared DI providers
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Pydantic BaseSettings (env vars)
│   │   └── constants.py                 # App-wide constants, tier definitions
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                      # User model (synced from Firebase)
│   │   ├── user_credits.py              # Credit balance + transaction history
│   │   ├── conversation.py              # Conversation model
│   │   ├── message.py                   # Chat message model
│   │   ├── legal_query.py               # Legal query/case model
│   │   └── saved_analysis.py            # Saved legal analysis model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth_schema.py               # Firebase token validation DTOs
│   │   ├── user_schema.py               # User profile + tier info
│   │   ├── credit_schema.py             # Credit balance, transactions, purchase
│   │   ├── conversation_schema.py       # Conversation request/response
│   │   ├── message_schema.py            # Message DTOs
│   │   ├── legal_analysis_schema.py     # Analysis response with citations
│   │   └── health_schema.py             # Health check response
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth_router.py               # POST /auth/verify-token (Firebase)
│   │   ├── account_router.py            # GET /account/me, /account/credits
│   │   ├── conversation_router.py       # CRUD for conversations
│   │   ├── chat_router.py               # POST /chat/send, WebSocket /chat/ws
│   │   ├── law_browser_router.py        # GET /laws/search, /laws/{id}
│   │   └── health_router.py             # GET /health, /ready
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── firebase_auth_service.py     # Firebase ID token verification
│   │   ├── credit_service.py            # Credit balance, deduction, tier logic
│   │   ├── conversation_service.py      # Conversation orchestration
│   │   ├── intake_flow_service.py       # Guided question flow (state machine)
│   │   ├── legal_classifier_service.py  # Classifies legal domain from user input
│   │   ├── rag_retrieval_service.py     # Vector search + reranking
│   │   ├── legal_analysis_service.py    # Gemini-powered legal reasoning
│   │   ├── citation_service.py          # Extracts & verifies law citations
│   │   ├── explanation_service.py       # Simplifies legal language
│   │   └── law_browser_service.py       # Browse/search law corpus
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── credit_repository.py         # Credit balance + transaction queries
│   │   ├── conversation_repository.py
│   │   ├── message_repository.py
│   │   └── law_repository.py            # Queries vector store + PostgreSQL
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── firebase_auth_middleware.py  # Firebase ID token verification
│   │   ├── credit_gate_middleware.py    # Check credits before AI calls
│   │   ├── rate_limit_middleware.py     # Per-tier rate limiting
│   │   ├── cors_middleware.py           # CORS configuration
│   │   └── error_handler_middleware.py  # Global exception handling
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── firebase_client.py           # Firebase Admin SDK initialization
│   │   ├── vertex_ai_client.py          # Gemini 3.1 Pro client wrapper
│   │   ├── vertex_embedding_client.py   # text-embedding-005 client
│   │   ├── vector_search_client.py      # Vertex AI Vector Search queries
│   │   └── chroma_client.py             # ChromaDB for local dev
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                    # structlog configuration
│       ├── security.py                  # Input sanitization, token utils
│       └── georgian_text_utils.py       # Georgian text normalization
│
├── alembic/                             # Database migrations
│   ├── env.py
│   └── versions/
│
└── tests/
    ├── conftest.py
    ├── test_chat_router.py
    ├── test_rag_retrieval_service.py
    ├── test_legal_analysis_service.py
    ├── test_credit_service.py
    └── test_intake_flow_service.py
```

---

## Core Services — Detailed Specifications

### 1. Conversation Orchestrator (`conversation_service.py`)

The main entry point for all user interactions. Manages the conversation lifecycle:

```
User Message → Intake Flow Check → Legal Classification → RAG Retrieval → Legal Analysis → Plain-Language Response
```

**State Machine Phases:**
1. **GREETING** — Welcome, explain capabilities
2. **INTAKE** — Guided questions to understand the situation
3. **CLARIFICATION** — Follow-up questions for missing details
4. **ANALYSIS** — RAG retrieval + Gemini analysis
5. **ADVICE** — Present findings with citations
6. **FOLLOW_UP** — Answer additional questions about the analysis

### 2. Intake Flow Service (`intake_flow_service.py`)

A structured question flow that extracts all necessary facts before legal analysis:

```python
INTAKE_QUESTIONS = [
    "რა მოხდა? მოკლედ აღწერეთ სიტუაცია.",
    # "What happened? Briefly describe the situation."
    
    "როდის მოხდა ეს? (თარიღი ან მიახლოებითი დრო)",
    # "When did this happen? (date or approximate time)"
    
    "სად მოხდა? (ქალაქი, რეგიონი)",
    # "Where did it happen? (city, region)"
    
    "ვინ არის ჩართული? (მხარეები, ორგანიზაციები)",
    # "Who is involved? (parties, organizations)"
    
    "არის თუ არა რაიმე დოკუმენტი ან ხელშეკრულება?",
    # "Is there any document or contract involved?"
    
    "რა შედეგს ელოდებით? რა გინდათ რომ მოხდეს?",
    # "What outcome do you expect? What do you want to happen?"
]
```

The service should be smart enough to:
- Skip questions already answered in the initial description
- Ask follow-up questions based on the detected legal domain
- Adapt the flow for different case types (criminal, civil, administrative, labor, etc.)

### 3. RAG Retrieval Service (`rag_retrieval_service.py`)

**Hybrid Search Pipeline:**

```
Query → Embed Query → Vector Search (top-50) → Full-Text Search (top-50) → Merge & Deduplicate → Rerank (top-20) → Return
```

Key requirements:
- Use `RETRIEVAL_QUERY` task type for query embedding
- Retrieve top-50 from vector search, top-50 from PostgreSQL full-text
- Merge results, deduplicate by article ID
- Rerank using Gemini (or a cross-encoder) to select the 15-20 most relevant articles
- Return chunks with full metadata (code name, article number, hierarchical path)
- **Always over-retrieve** — it's better to have too many relevant laws than miss one

### 4. Legal Analysis Service (`legal_analysis_service.py`)

The core Gemini integration. This service:

1. Constructs the system prompt (see below)
2. Builds the context from retrieved law chunks
3. Sends to Gemini 3.1 Pro via Vertex AI
4. Parses the structured response
5. Validates all citations against the corpus

**Gemini System Prompt for Legal Analysis:**

```
You are კანონის ოსტატი (The Master of Law), the most knowledgeable and strategic 
legal advisor in Georgia. You have encyclopedic knowledge of ALL Georgian legislation 
and decades of courtroom experience.

YOUR ROLE:
- You serve as a personal legal advisor to ordinary Georgian citizens
- You ALWAYS advocate for the user's best interest
- You find the MOST FAVORABLE legal interpretation for the user
- You identify EVERY applicable law, defense, and legal strategy
- You explain everything in simple, everyday Georgian language — no legalese

CRITICAL RULES:
1. EVERY claim you make MUST cite a specific Georgian law article 
   (e.g., "სამოქალაქო კოდექსის მუხლი 316")
2. NEVER fabricate or guess law articles — use ONLY the provided context
3. If you're unsure about a specific article, say so explicitly
4. Always present MULTIPLE legal strategies ranked from best to worst
5. For each strategy, explain: success probability, risks, required steps, timeline
6. Always mention relevant statutes of limitation (ხანდაზმულობის ვადა)
7. When criminal charges are possible, ALWAYS identify potential defenses
8. Distinguish between what the law says and what courts typically decide

RESPONSE STRUCTURE:
1. 📋 SITUATION SUMMARY — Restate the user's situation in clear terms
2. ⚖️ APPLICABLE LAWS — List all relevant articles with explanations
3. 🛡️ RECOMMENDED STRATEGY — The optimal legal approach for the user
4. 📊 ALTERNATIVE STRATEGIES — Other options ranked by favorability  
5. ⚠️ RISKS & WARNINGS — What could go wrong
6. 📅 NEXT STEPS — Concrete actions the user should take, with deadlines
7. 📚 FULL CITATIONS — Complete list of all referenced law articles

LANGUAGE: Respond in Georgian (ქართული) by default. Switch to English 
if the user writes in English.
```

### 5. Citation Service (`citation_service.py`)

After Gemini generates a response, this service:
1. Extracts all law citations from the response text
2. Validates each citation exists in the corpus
3. Fetches the full article text for each citation
4. Flags any citations that couldn't be verified
5. Appends verified citation details to the response

---

## Credit System & User Tiers

### Tier Definitions

| Tier | Who | Credits | Rate Limit | How They Get It |
|------|-----|---------|------------|-----------------|
| **FREE** | Default for all new users | 5/day (auto-resets at midnight) | 5 req/min | Automatic on sign-up via Firebase |
| **PRO** | Users who purchase credits | Purchased (e.g. 100 credits) | 30 req/min | Future: in-app purchase |
| **ADMIN** | Internal accounts | 10,000 (one-time grant) | 120 req/min | Manually set in DB or via admin endpoint |

### Credit Costs

| Action | Credits | Notes |
|--------|---------|-------|
| Send chat message (AI response) | 1 | The main interaction |
| Deep legal analysis | 2 | When user explicitly requests detailed analysis |
| Browse/search laws | 0 | Always free — it's just DB queries |
| Start conversation | 0 | Free |
| View conversation history | 0 | Free |

### Credit Flow

```
Request → Firebase Auth Middleware → Credit Gate Middleware → Service Logic
                                         │
                                         ├─ Check: does user have enough credits?
                                         ├─ If no → 402 Payment Required (with credits_remaining: 0)
                                         ├─ If yes → proceed, deduct after successful response
                                         └─ For FREE tier: also check daily_used < daily_limit
```

### Database Schema (user_credits table)

```sql
CREATE TABLE user_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    tier VARCHAR(10) NOT NULL DEFAULT 'FREE',  -- FREE | PRO | ADMIN
    credit_balance INTEGER NOT NULL DEFAULT 0,
    daily_credits_used INTEGER NOT NULL DEFAULT 0,
    daily_reset_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,           -- positive = added, negative = deducted
    transaction_type VARCHAR(20),      -- 'daily_grant' | 'chat' | 'analysis' | 'purchase' | 'admin_grant'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Firebase Authentication Flow

```
Flutter App → Firebase Auth (Google/Email sign-in) → Gets Firebase ID Token
    → Sends token in Authorization: Bearer <firebase_id_token>
    → Backend verifies with firebase_admin.auth.verify_id_token()
    → Creates or syncs local user record (users table)
    → Returns user profile + tier + credit balance
```

**Key rule:** The backend NEVER handles passwords. Firebase handles all authentication. The backend only verifies Firebase ID tokens and manages the local user record (tier, credits, conversations).

### Marketing Phase (Current)

- All users are FREE tier by default
- 5 free AI interactions per day per account
- Law browsing is unlimited and free
- This is generous enough for marketing / user acquisition
- No payment infrastructure needed yet

### Future: Pro Tier

When ready to monetize:
1. Add Stripe/RevenueCat integration
2. User purchases credits (e.g. 100 credits for $X)
3. Tier automatically upgrades to PRO on first purchase
4. PRO users get higher rate limits + purchased credits persist (no daily reset)
5. ADMIN tier is manually granted

---

## API Endpoints

### Authentication (Firebase)
```
POST   /api/v1/auth/verify-token       # Verify Firebase ID token, create/sync local user
GET    /api/v1/auth/me                  # Get current user profile + tier + credits
```

### Account & Credits
```
GET    /api/v1/account/credits          # Get credit balance + daily usage
GET    /api/v1/account/transactions     # Credit transaction history
POST   /api/v1/account/credits/purchase # Purchase credits (Pro tier, future)
```

### Conversations
```
POST   /api/v1/conversations           # Start new conversation (costs 0 credits)
GET    /api/v1/conversations           # List user's conversations
GET    /api/v1/conversations/{id}      # Get conversation with messages
DELETE /api/v1/conversations/{id}      # Delete conversation
```

### Chat
```
POST   /api/v1/chat/{conversation_id}/send    # Send message, get AI response (costs 1 credit)
WS     /api/v1/chat/{conversation_id}/ws      # WebSocket for streaming responses
```

### Law Browser
```
GET    /api/v1/laws/search?q=...&domain=...   # Search laws (free, no credits)
GET    /api/v1/laws/codes                      # List all legal codes (free)
GET    /api/v1/laws/codes/{code_id}            # Get code structure (free)
GET    /api/v1/laws/articles/{article_id}      # Get specific article (free)
```

### Health
```
GET    /api/v1/health                  # Liveness check
GET    /api/v1/health/ready            # Readiness (DB + Vector Store + Gemini)
```

---

## Vertex AI Integration

### Configuration
```python
# Use Vertex AI Python SDK (google-cloud-aiplatform)
# Model: gemini-3.1-pro
# Endpoint: Vertex AI (NOT Google AI Studio — we need enterprise features)

# Key settings:
# - temperature: 0.1 (low for legal accuracy)
# - max_output_tokens: 8192
# - top_p: 0.8
# - safety_settings: minimal filtering (legal content can trigger false positives)
# - system_instruction: The legal analysis prompt above
```

### vertex_ai_client.py Requirements
```python
# - Initialize with API key or service account
# - Support both streaming and non-streaming generation
# - Implement retry logic with exponential backoff
# - Token counting for cost tracking
# - Structured response parsing
# - Timeout handling (legal analysis can take 15-30s)
# - Circuit breaker pattern for API outages
```

---

## Environment Variables

```bash
# .env.example
# App
APP_NAME=the-master-of-law
APP_ENV=development  # development | staging | production
APP_PORT=8000
APP_SECRET_KEY=your-secret-key-here
APP_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Firebase Authentication
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_KEY=./firebase-service-account.json
# Note: The Flutter app handles sign-in (Google, Email, etc.)
# The backend only VERIFIES the Firebase ID token sent by the app.

# Vertex AI / Gemini
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-3.1-pro
EMBEDDING_MODEL=text-embedding-005

# Vector Store
VECTOR_STORE_BACKEND=chroma
CHROMA_PERSIST_DIR=./data/chroma
VERTEX_VECTOR_SEARCH_INDEX_ID=
VERTEX_VECTOR_SEARCH_ENDPOINT_ID=

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/master_of_law
DATABASE_POOL_SIZE=10

# Redis (for rate limiting + credit cache)
REDIS_URL=redis://localhost:6379/0

# Credit System
FREE_TIER_DAILY_CREDITS=5          # Free interactions per day
PRO_TIER_DEFAULT_CREDITS=100       # Credits on Pro purchase (future)
ADMIN_CREDITS=10000                # Admin accounts get this many credits
CREDIT_COST_CHAT=1                 # Credits per AI chat interaction
CREDIT_COST_ANALYSIS=2             # Credits per deep legal analysis

# Rate Limiting (per tier)
RATE_LIMIT_FREE_PER_MINUTE=5
RATE_LIMIT_PRO_PER_MINUTE=30
RATE_LIMIT_ADMIN_PER_MINUTE=120

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Docker Setup

### Dockerfile (multi-stage)
```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system -r pyproject.toml

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
services:
  api:
    build: .
    ports:
      - "127.0.0.1:8000:8000"   # Only exposed to localhost
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://mol_user:${POSTGRES_PASSWORD}@postgres:5432/master_of_law
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - internal
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: master_of_law
      POSTGRES_USER: mol_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}   # Set in .env, NEVER hardcoded
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mol_user"]
      interval: 5s
      timeout: 3s
      retries: 5
    # NO 'ports' block — PostgreSQL is ONLY reachable from the 'internal' network.
    # The api container reaches it at postgres:5432.
    # No one from the internet or host machine can connect directly.
    networks:
      - internal
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    # NO 'ports' block — same as PostgreSQL, internal only.
    networks:
      - internal
    restart: unless-stopped

networks:
  internal:
    driver: bridge
    # Private network — only containers in this compose file can communicate.
    # PostgreSQL and Redis have NO port mappings, so they are invisible
    # to the host machine and the internet.

volumes:
  pgdata:
```

### Database Security Rules

**Development (your local machine):**
- PostgreSQL is bound to `127.0.0.1:5432` — accessible only from localhost
- This is fine for running the pipeline scraper directly (outside Docker)
- Password: `corpus_dev_pw` (ok for dev, never use in production)

**Production (deployed server):**
1. **NO port exposure** — PostgreSQL has no `ports:` block. Only the API container can reach it via Docker's internal network (`postgres:5432`)
2. **Strong password** — Set `POSTGRES_PASSWORD` in `.env` to a random 32+ char string. Never commit `.env` to git.
3. **The API is the only gateway** — All data access goes through FastAPI endpoints with:
   - Firebase auth middleware (every request verified)
   - Credit gate middleware (rate limits enforced)
   - Input sanitization (SQL injection prevention via SQLAlchemy ORM)
4. **No raw SQL exposure** — Users interact through typed Pydantic schemas. The ORM never passes raw user input to queries.
5. **When ready for scale** — Migrate from Docker PostgreSQL to **GCP Cloud SQL** (managed, auto-backups, encrypted at rest, private VPC networking, IAM auth)

**Security checklist for production `.env`:**
```bash
# Generate strong passwords:
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
POSTGRES_PASSWORD=<random-32-char-string>
REDIS_PASSWORD=<random-32-char-string>
APP_SECRET_KEY=<random-32-char-string>
```

---

## Key Dependencies

```toml
[project]
name = "master-of-law-backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.9",
    "pydantic-settings>=2.5",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "google-cloud-aiplatform>=1.70",
    "firebase-admin>=6.5",
    "chromadb>=0.5",
    "redis>=5.0",
    "httpx>=0.27",
    "structlog>=24.0",
    "python-multipart>=0.0.9",
    "tenacity>=9.0",
]
```

---

## Deliverables Checklist

- [ ] Complete project structure as specified
- [ ] FastAPI app factory with middleware stack
- [ ] Firebase Authentication integration (verify ID tokens)
- [ ] User tier system (FREE / PRO / ADMIN)
- [ ] Credit system (balance tracking, deduction per interaction, daily free limits)
- [ ] Conversation CRUD with state machine
- [ ] Intake flow service with adaptive questioning
- [ ] RAG retrieval with hybrid search (vector + full-text)
- [ ] Gemini 3.1 Pro integration via Vertex AI
- [ ] Citation extraction and verification
- [ ] Law browser API endpoints (free, no credits)
- [ ] WebSocket support for streaming responses
- [ ] Per-tier rate limiting (FREE=5/min, PRO=30/min, ADMIN=120/min)
- [ ] Credit gate middleware (block AI calls when credits exhausted)
- [ ] Docker + docker-compose setup (API + PostgreSQL + Redis)
- [ ] Database migrations (Alembic)
- [ ] Health check endpoints
- [ ] Structured logging
- [ ] Unit tests for core services (especially credit_service)
- [ ] README with API documentation
