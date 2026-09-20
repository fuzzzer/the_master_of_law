# Handoff: Start & Test Fuzzzy Law Backend

## For the new AI model

**Read these files first for full context:**
1. `AI_GUIDE.md` (root) — architecture, patterns, all 25 endpoints, gotchas
2. `backend/.env` — already configured, user just needs to add their `VERTEX_AI_API_KEY`

**Do NOT read:** `handoff.md`, `master_plan/` — those are historical, everything relevant is in AI_GUIDE.md.

---

## Current State: Backend is 100% complete

- **124 tests passing** — run with `cd backend && .venv/bin/python -m pytest tests/ -q`
- **25 API endpoints**, 10 services, 7 structured prompts, 5 repositories
- **ChromaDB corpus**: 9,450 Georgian law documents pre-embedded
- **All prompts** extracted to `app/prompts/` (typed `PromptTemplate` classes, no hardcoded strings in services)

---

## Task: Help the user START the server and TEST it

### Prerequisites the user needs:
1. **VERTEX_AI_API_KEY** — must be set in `backend/.env` line 11
2. **PostgreSQL** running locally (for conversations, credits, case files)
3. Python venv already exists at `backend/.venv/`

### Step-by-step startup:

```bash
# 1. Start PostgreSQL (if not running)
#    Option A: Homebrew
brew services start postgresql@16
createdb fuzzzy_law
createuser fuzzzy_user -s

#    Option B: Docker (one container, just the DB)
docker run -d --name mol-postgres \
  -e POSTGRES_DB=fuzzzy_law \
  -e POSTGRES_USER=fuzzzy_user \
  -e POSTGRES_PASSWORD=corpus_dev_pw \
  -p 5432:5432 \
  postgres:16-alpine

# 2. Run Alembic migrations (creates tables)
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "initial"
alembic upgrade head

# 3. Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Testing endpoints (in a separate terminal):

```bash
# Health check (no auth, no DB needed)
curl http://localhost:8000/api/v1/health

# Search Georgian laws (free, no auth)
curl "http://localhost:8000/api/v1/laws/search?q=მუხლი&top_k=3"

# List legal codes (free)
curl http://localhost:8000/api/v1/laws/codes

# Swagger docs (open in browser)
open http://localhost:8000/docs

# Create a conversation (dev mode = auto-authenticated as ADMIN)
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "Test case"}'

# Send a chat message (use the conversation_id from above)
# This triggers the full RAG pipeline + Gemini analysis
curl -X POST http://localhost:8000/api/v1/chat/CONVERSATION_ID_HERE/send \
  -H "Content-Type: application/json" \
  -d '{"message": "მეზობელმა ცემა მომახდინა, რა უნდა გავაკეთო?"}'
```

### Key dev-mode behavior:
- `APP_ENV=development` → requests without auth headers get a mock ADMIN user automatically
- No Firebase token needed for testing
- All endpoints work, credits are unlimited for the dev user

### If something fails:
- **"Connection refused" on DB endpoints** → PostgreSQL not running or migration not done
- **Gemini errors** → check `VERTEX_AI_API_KEY` is set in `.env`
- **ChromaDB warnings** → harmless PostHog telemetry noise, ignore them
- **Law search returns 0 results** → check `CHROMA_PERSIST_DIR` path points to the corpus

### Full production deploy (Docker):
```bash
cd backend
# Edit .env: set lines marked "PROD:" to production values
docker compose up -d
docker compose exec api alembic revision --autogenerate -m "initial"
docker compose exec api alembic upgrade head
```
