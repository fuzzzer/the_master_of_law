# კანონის ოსტატი — The Master of Law

> Georgian AI Legal Assistant — from raw legislation to production app.

---

## What This Project Is

A three-part system that lets any Georgian citizen ask legal questions in plain language and get accurate, cited answers:

1. **`law_corpus/`** — Pipeline that downloads all Georgian laws from matsne.gov.ge, parses them, and indexes them into a searchable vector store ✅ **BUILT**
2. **`backend/`** — FastAPI server that takes user questions, retrieves relevant laws (RAG), sends them to Gemini 3.1 Pro, and returns cited legal advice ⬜ **NEXT**
3. **Flutter App** — Mobile chat UI where citizens interact with the system ⬜ **LATER**

---

## Step 1 — Set Up the Law Corpus Pipeline

### 1.1 Prerequisites

- Python 3.11+
- PostgreSQL 16+ (or use Docker)
- A Google Cloud project with Vertex AI API enabled
- ~**2 GB free disk space** (see data size estimates below)

### 1.2 Install

```bash
cd law_corpus

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -e ".[dev]"
```

### 1.3 Configure

```bash
cp .env.example .env
```

Edit `.env` — the critical values:

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project-id    # For Vertex AI embeddings
GOOGLE_CLOUD_LOCATION=us-central1
VECTOR_STORE_BACKEND=chroma                  # Use "chroma" for local dev
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/law_corpus
```

> **No GCP yet?** You can still run scrape → parse → chunk without Vertex AI. Embedding/indexing will fail, but you'll have all the parsed law data locally.

### 1.4 Start PostgreSQL (Docker method)

```bash
docker compose up -d postgres
```

Or use your existing PostgreSQL and create a `law_corpus` database.

### 1.5 Scrape the Laws

**Start with P0 only** (the 8 most critical codes — Constitution, Civil, Criminal, etc.):

```bash
python -m pipeline.main scrape --source matsne --priority P0
```

Then add P1 (Tax, Labour, Entrepreneurial, Consumer):

```bash
python -m pipeline.main scrape --priority P1
```

> ⚠️ **Server respect**: The scraper enforces a **minimum 2-second delay** between every request to matsne.gov.ge. If matsne responds with errors, it backs off exponentially (4s → 8s → 16s → 60s max). This is hardcoded and cannot be bypassed.

### 1.6 Parse → Chunk → Embed → Index

```bash
# Parse HTML into structured documents
python -m pipeline.main parse

# Split into embeddable chunks (structure-aware)
python -m pipeline.main chunk

# Generate embeddings via Vertex AI (requires GCP)
python -m pipeline.main embed

# Index into ChromaDB (local) or Vertex AI Vector Search (prod)
python -m pipeline.main index --backend chroma
```

Or run everything at once:

```bash
python -m pipeline.main run --priority P0 --priority P1
```

### 1.7 Validate

```bash
python -m pipeline.main validate   # Check completeness
python -m pipeline.main stats      # See numbers
```

---

## Data Size Estimates

This is **not** terabytes. Georgian legislation is manageable:

| What | Estimated Size | Notes |
|------|---------------|-------|
| Raw HTML (all P0+P1 laws) | ~50–80 MB | 12 laws, each 200-1500 articles |
| Raw HTML (all P0+P1+P2+P3) | ~150–250 MB | ~25 laws total |
| Parsed JSON | ~30–60 MB | Structured, no HTML overhead |
| Chunks JSON | ~40–70 MB | With injected headers |
| Embeddings cache | ~200–400 MB | 768-dim float vectors |
| ChromaDB index | ~300–500 MB | Vectors + metadata + HNSW |
| **Total on disk** | **~800 MB – 1.3 GB** | For the complete corpus |

### Scraping time estimates (with 2s rate limiting):

| Priority | Laws | ~Articles | ~Requests | ~Time |
|----------|------|-----------|-----------|-------|
| P0 | 8 | ~3,500 | ~20 | ~1 min |
| P1 | 4 | ~500 | ~10 | ~30 sec |
| P2 | 7 | ~900 | ~15 | ~1 min |
| **Total** | **19** | **~5,000** | **~45** | **~3 min** |

> Each law is typically one page (the consolidated version). The scraper downloads the full text in a single request per law — not per article. So the total request count is low and matsne.gov.ge will not be stressed.

### Embedding cost estimate:

| Metric | Value |
|--------|-------|
| Total chunks (est.) | ~4,000–6,000 |
| Tokens per chunk (avg) | ~500 |
| Total tokens | ~2.5M |
| Vertex AI text-embedding-005 cost | ~$0.025 per 1M tokens |
| **Estimated embedding cost** | **~$0.06** |

---

## Step 2 — Build the Backend (NEXT)

> **Prerequisite:** Step 1 must be complete. The backend READS from the same ChromaDB/PostgreSQL that the corpus pipeline populates. It does not scrape or parse — it only searches.

The backend spec is in `master_plan/02_backend_system_prompt.md`. Here's what it builds:

### What the backend does

```
User question → Intake flow (guided questions) → Legal classification
    → Hybrid RAG search (vector + full-text) → Gemini 3.1 Pro analysis
    → Citation verification → Plain-language response with law citations
```

### Backend structure: `backend/`

- **FastAPI** app with Clean Architecture (routes → services → repositories)
- **Gemini 3.1 Pro** via Vertex AI for legal reasoning
- **Hybrid search**: vector similarity (ChromaDB/Vertex) + PostgreSQL full-text
- **Citation verification**: every law citation in Gemini's output is validated against the corpus
- **JWT auth**, rate limiting, WebSocket streaming, health checks
- **Docker**: API + PostgreSQL + Redis

### What must be done in Step 1 before starting Step 2

| Requirement | How to verify | Status |
|------------|---------------|--------|
| All P0 laws scraped and parsed | `python -m pipeline.main validate` — no P0 missing | ⬜ |
| All P1 laws scraped and parsed | Same — no P1 missing | ⬜ |
| Chunks generated | `python -m pipeline.main stats` — chunks > 0 | ⬜ |
| ChromaDB indexed (dev) | Stats shows indexed chunks | ⬜ |
| PostgreSQL has article data | Can query the `legal_articles` table | ⬜ |
| Every chunk has `source_url` and `citation_text` | Spot-check a chunk JSON file | ⬜ |

### How to start Step 2

```
Attach: master_plan/02_backend_system_prompt.md

Prompt: Build the FastAPI backend in backend/ as specified.
The law corpus is already indexed in ChromaDB (./data/chroma) and
PostgreSQL (law_corpus database). The backend only reads from these.
```

---

## Step 3 — Design System (can run in parallel)

The design spec is in `master_plan/03_design_system_prompt.md`. This generates UI mockups and design tokens for the Flutter app. It has no code dependency on Steps 1–2.

---

## Step 4 — Flutter App (requires Steps 2 + 3)

Build the Flutter mobile app using the design system from Step 3 and connecting to the FastAPI backend from Step 2.

---

## Project Map

```
the_master_of_law/
├── init.md                    ← You are here
├── master_plan/
│   ├── 01_law_corpus_agent_prompt.md    # Spec for Step 1
│   ├── 02_backend_system_prompt.md      # Spec for Step 2
│   ├── 03_design_system_prompt.md       # Spec for Step 3
│   └── README.md
│
├── law_corpus/                ✅ BUILT
│   ├── pipeline/              # Scraper → Parser → Chunker → Embedder → Indexer
│   ├── tests/                 # Unit tests with real Georgian fixtures
│   ├── scripts/               # Shell scripts for pipeline execution
│   ├── data/                  # Output (git-ignored, ~1 GB when populated)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── pyproject.toml
│
├── backend/                   ⬜ NEXT (Step 2)
│
└── flutter_app/               ⬜ LATER (Step 4)
```
