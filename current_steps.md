# Current Steps — Law Corpus Pipeline Setup

> GCP project is **NOT needed** until Step 5 (embed). Steps 1–4 are fully local.

---

## Task 1 — Install dependencies ✅

```bash
cd law_corpus
pip install -e ".[dev]"
```

---

## Task 2 — Start PostgreSQL + set up `.env` ✅

**Step A:** Copy the env file:
```bash
cd law_corpus
cp .env.example .env
```

The defaults work out of the box. No edits needed yet.

**Step B:** Start PostgreSQL:
```bash
docker compose up -d postgres
```

**Step C:** Verify it's running:
```bash
docker compose ps
```
Should show `postgres` as `Up (healthy)`.

**Step D (optional):** Test the connection:
```bash
docker compose exec postgres psql -U corpus -d law_corpus -c "SELECT 1;"
```

> All credentials come from `.env` → `docker-compose.yml` reads them automatically.
> PostgreSQL is bound to `127.0.0.1` (localhost only) — not exposed to the internet.

**Status:** ✅ Done

---

## Task 3 — Scrape P0 + P1 laws ✅

```bash
cd law_corpus
python -m pipeline.main scrape --source matsne --priority P0
python -m pipeline.main scrape --priority P1
```

**What to expect:** ~19 requests, ~40 seconds, ~50–80 MB in `data/raw/`

**Status:** ✅ Done — 12 documents scraped from matsne.gov.ge

---

## Task 4 — Parse + Chunk (local, no GCP) ✅

```bash
python -m pipeline.main parse
python -m pipeline.main chunk
```

**What to expect:** ~30 sec parse, ~10 sec chunk → `data/parsed/` and `data/chunks/`

**Status:** ✅ Done — 9,450 chunks across 12 legal documents

---

## Task 5 — Set up GCP + Embed + Index

> ⚠️ This is the first step that needs GCP.

**Step A:** Set up GCP: ✅
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create or select a project
3. Enable **Vertex AI API**
4. Run: `gcloud auth application-default login`

**Step B:** Update `.env`: ✅
```bash
GOOGLE_CLOUD_PROJECT=gen-lang-client-0225498420
GOOGLE_CLOUD_LOCATION=us-central1
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768
```

**Step C:** Embed: ✅ DONE
```bash
python -m pipeline.main embed
```
- Model: `gemini-embedding-001` via `google-genai` SDK (Vertex AI ADC auth)
- 9,450 chunks × 968 avg tokens = 9.15M tokens → **~$1.37 cost**
- Completed: 2026-05-04 ~07:15 Tbilisi time

**Step D:** Index: ✅ DONE
```bash
python -m pipeline.main index --backend chroma
```
- Fixed bug: index command now loads embeddings from `EmbeddingCache` (chunk JSON excludes embedding field)
- 9,450 chunks upserted to ChromaDB (`data/chroma/`), 768-dim vectors, cosine distance
- Search indices built: 1,525 unique articles, 12 codes

**Status:** ✅ Done

---

## Task 6 — Validate ✅

```bash
python -m pipeline.main validate
python -m pipeline.main stats
```

**Results:**
- All P0 laws present ✅
- 2 P1 laws missing (entrepreneurial_law, consumer_rights_law) — not available on matsne.gov.ge scrape
- Stats: 12 raw docs, 12 parsed, 9,450 chunks, 9,450 cached embeddings

**Status:** ✅ Done

---

## Task 7 — Verify citation data ✅

All 12 document chunk files verified — every chunk has:
- `source_url` ✅ (matsne.gov.ge canonical URL)
- `article_url` ✅ (deep-link with `#article_N` anchor)
- `document_number` ✅ (official registration number)
- `citation_text` ✅ (pre-formatted Georgian citation string)

**Status:** ✅ Done

---

## ★ Step 8 — Build the FastAPI Backend ✅ (In Progress)

**Status:** Core backend built + DB wired — 58 files, ~3,500 lines, 15 endpoints, repositories + services complete.

**What's done:**
- ✅ FastAPI app factory with full middleware stack (auth, credits, rate limit, errors, CORS)
- ✅ 5-stage RAG pipeline (query expansion → vector search → full-text → merge → rerank)
- ✅ Gemini 3.1 Pro legal analysis with Georgian system prompt
- ✅ Citation extraction & verification service
- ✅ ChromaDB integration (9,450 docs connected)
- ✅ Firebase auth middleware (dev mode: mock user, prod: DB-enriched tier)
- ✅ SQLAlchemy models with relationships (user, credits, conversation, message)
- ✅ Vertex AI auth: `GOOGLE_API_KEY` + `vertexai=True` (GCP Console credits)
- ✅ Docker (PostgreSQL internal-only, Redis internal-only, API on localhost)
- ✅ Law browser endpoints (free, no credits)
- ✅ **Repositories layer** — user, credit, conversation, message (all DB-wired)
- ✅ **Credit gate middleware** — real DB balance check, 402 with Georgian/English messages
- ✅ **Auth router** — syncs user to DB on verify-token, returns real credit balance
- ✅ **Account router** — returns real credit balance + transaction history from DB
- ✅ **Conversation router** — PostgreSQL-backed (replaces in-memory dict)
- ✅ **Chat router** — persists messages, loads conversation history, deducts credits after success
- ✅ **Conversation state machine** — 6-phase lifecycle with valid transitions
- ✅ **Intake flow service** — 6 guided questions in Georgian with topic detection

**What's remaining (see `handoff.md` for full details):**
- [ ] Run Alembic migrations (env.py is ready, needs `alembic revision --autogenerate`)
- [ ] Defense Case Builder service
- [ ] WebSocket streaming
- [ ] Tests
- [ ] Install `structlog` when network available


