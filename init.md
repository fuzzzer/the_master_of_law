# კანონის ოსტატი — The Master of Law

> Three ready-to-go prompts. Copy each one, attach the referenced file(s), and send to your AI agent.

---

## PROMPT 1 — Build the Law Corpus Pipeline

**Attach this file to the conversation:** `master_plan/01_law_corpus_agent_prompt.md`

```
I need you to build a complete Python data pipeline that scrapes, parses, chunks, embeds, and indexes all Georgian legislation into a searchable vector store.

The full specification is in the attached file "01_law_corpus_agent_prompt.md" — read it completely before writing any code.

Key points:
- Build the project inside the "law_corpus/" directory at the root of this repository
- Follow the exact project structure defined in the spec
- Primary data source: matsne.gov.ge (Georgian Legislative Herald)
- Use structure-aware chunking that respects the Georgian legal hierarchy (Code → Book → Chapter → Article → Paragraph)
- Embeddings via Vertex AI text-embedding-005
- Dual indexing: ChromaDB (dev) + Vertex AI Vector Search (prod), switchable via env var
- PostgreSQL for metadata + full-text search
- CLI interface using click or typer for all pipeline stages
- Must be resumable — crashes should not require restart from scratch
- Include Docker support, .env.example, and tests with real fixture data
- Respect matsne.gov.ge with rate limiting (min 2s delay between requests)

Start with the project skeleton (pyproject.toml, directory structure, config, models), then implement each module in order: scraper → parser → chunker → embedder → indexer.

Make it production-grade. Every file should have proper error handling, logging, and type hints.
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
