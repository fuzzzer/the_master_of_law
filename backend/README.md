# 🏛️ The Master of Law — Backend API

**კანონის ოსტატი** — AI-powered legal advocate backend for Georgian citizens.

## Overview

FastAPI backend that serves the Flutter app. Powers conversations, RAG retrieval from a pre-built Georgian law corpus (9,450 chunks across 12 legal codes), defense strategy generation via Gemini 3.1 Pro, Firebase auth, and a credit-based access system.

## Architecture

```
User Message
  → [Stage 0] AI Query Expansion (Gemini generates legal search terms)
  → [Stage 1] Multi-Query Vector Search (ChromaDB, top-50 per query)
  → [Stage 2] Multi-Query Full-Text Search (JSON indices, top-50 per query)
  → [Stage 3] Merge & Deduplicate
  → [Stage 4] Gemini Rerank (select top-20 most relevant)
  → Legal Analysis (Gemini 3.1 Pro with grounded context)
  → Citation Verification
  → Response to user
```

## Quick Start (Development)

```bash
cd backend

# Create virtual environment
python3.11 -m venv .venv --system-site-packages
source .venv/bin/activate

# Copy env and edit as needed
cp .env.example .env

# Run the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Docker (Production)

```bash
# Set strong passwords in .env first
docker compose up -d
```

## API Endpoints

### Health
| Method | Path | Auth | Credits | Description |
|--------|------|------|---------|-------------|
| GET | `/api/v1/health` | ❌ | 0 | Liveness probe |
| GET | `/api/v1/health/ready` | ❌ | 0 | Readiness probe (checks ChromaDB, Gemini) |

### Authentication
| Method | Path | Auth | Credits | Description |
|--------|------|------|---------|-------------|
| POST | `/api/v1/auth/verify-token` | ❌ | 0 | Verify Firebase ID token |
| GET | `/api/v1/auth/me` | ✅ | 0 | Get current user profile |

### Account & Credits
| Method | Path | Auth | Credits | Description |
|--------|------|------|---------|-------------|
| GET | `/api/v1/account/credits` | ✅ | 0 | Get credit balance |
| GET | `/api/v1/account/transactions` | ✅ | 0 | Credit transaction history |

### Conversations
| Method | Path | Auth | Credits | Description |
|--------|------|------|---------|-------------|
| POST | `/api/v1/conversations` | ✅ | 0 | Start new conversation |
| GET | `/api/v1/conversations` | ✅ | 0 | List conversations |
| GET | `/api/v1/conversations/{id}` | ✅ | 0 | Get conversation with messages |
| DELETE | `/api/v1/conversations/{id}` | ✅ | 0 | Delete conversation |

### Chat (AI-Powered)
| Method | Path | Auth | Credits | Description |
|--------|------|------|---------|-------------|
| POST | `/api/v1/chat/{id}/send` | ✅ | 1 | Send message, get AI response |

### Law Browser (Always Free)
| Method | Path | Auth | Credits | Description |
|--------|------|------|---------|-------------|
| GET | `/api/v1/laws/search?q=...` | ❌ | 0 | Search laws |
| GET | `/api/v1/laws/codes` | ❌ | 0 | List all legal codes |
| GET | `/api/v1/laws/codes/{id}` | ❌ | 0 | Get code structure |
| GET | `/api/v1/laws/articles/{id}` | ❌ | 0 | Get article text |

## Credit System

| Tier | Credits | Rate Limit |
|------|---------|------------|
| FREE | 5/day (auto-reset) | 5 req/min |
| PRO | Purchased | 30 req/min |
| ADMIN | 10,000 | 120 req/min |

| Action | Cost |
|--------|------|
| Chat message | 1 credit |
| Deep analysis | 2 credits |
| Case file | 3 credits |
| Browse/search | Free |

## Tech Stack

- **Framework:** FastAPI (Python 3.11)
- **LLM:** Gemini 3.1 Pro via `google-genai` SDK
- **Embeddings:** `gemini-embedding-001` (768 dims)
- **Vector Store:** ChromaDB (pre-built, 9,450 chunks)
- **Database:** PostgreSQL 16 + Alembic migrations
- **Cache:** Redis 7
- **Auth:** Firebase Admin SDK
- **Logging:** Structured logging (structlog-compatible)

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config/              # Settings, constants
│   ├── routes/              # API routers
│   ├── services/            # Business logic (RAG, analysis, citations)
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic v2 DTOs
│   ├── middleware/          # Auth, credits, rate limit, CORS, errors
│   ├── integrations/        # Firebase, Gemini, ChromaDB clients
│   └── utils/               # Logger, security, Georgian text utils
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── Dockerfile               # Multi-stage Docker build
└── docker-compose.yml       # API + PostgreSQL + Redis
```
