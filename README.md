# ბუნდოვანი კანონი — Fuzzzy Law

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](#)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green)](#)
[![Build](https://img.shields.io/badge/build-passing-brightgreen)](#)

> AI-powered legal advocate for Georgian citizens.

**Fuzzzy Law** is a case-centric legal assistant that puts the full weight of Georgian law — statutes, Supreme Court practice, and Grand Chamber decisions — into the hands of ordinary people. Users describe a situation in plain Georgian; the app retrieves the relevant law, analyzes their standing, and helps them build a case. Answers are **grounded**: every legal claim is backed by retrieved articles and verified citations, not model memory. That grounding is the core correctness requirement of the whole project.

## What it does

- **Chat over Georgian law** — state-machine-driven conversations (Gemini 3.1 Pro) that clarify ambiguous details and give targeted, source-specific advice.
- **Grounded answers with citations** — a 5-stage RAG pipeline (query expansion → vector search with per-collection quotas → full-text search → merge → rerank) over **20,712 curated chunks** in 3 ChromaDB collections: `georgian_laws` (15,338 chunks, 12 legal codes), `court_practice` (5,197 Supreme Court rulings), `grand_chamber` (177 binding decisions). An article store (SQLite + FTS5) with `get_article` / `browse_code` tools plus retrieval repair and citation verification keeps the model honest.
- **Case builder** — facts, arguments, laws, evidence and conversations all link to each other; the AI organizes raw user input into a structured case.
- **BYOK, open access** — every model call is paid for by the caller's own Google API key (`BYOK_REQUIRED=true`), and the app can ship without accounts (`AUTH_ENABLED=false`) while keeping each user's cases private. Firebase Auth and a FREE/PRO/ADMIN credit-and-tier system are available when accounts are on; per-tier model choice is configurable from the UI without a redeploy.
- **Pipeline transparency** — per-request step traces and an admin dashboard, plus a 50-case eval pipeline in `eval/`.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Flutter (Dart), BLoC/Cubit, `fuzzzy_ui_kit` design system |
| Backend | Python 3.11 + FastAPI + SQLAlchemy 2.x async (~10K lines, 15 routers / 45 endpoints, 647 tests) |
| AI | `google-genai` SDK — Gemini 3.1 Pro (analysis), `gemini-embedding-001` (768-dim embeddings) |
| Data | PostgreSQL 16 (asyncpg) · ChromaDB (vectors) · Redis 7 (cache) · SQLite+FTS5 (article store) |
| Auth | Firebase Authentication (optional; BYOK mode runs without it) |

## Project structure

```
frontend/     Flutter app (package fuzzzy_law, bundle ge.fuzzycore.fuzzzylaw)
backend/      FastAPI service — routes → services → repositories → models
law_corpus/   Scrape → parse → chunk → embed → index pipeline (matsne.gov.ge)
eval/         50-case evaluation pipeline
docs/         QUICKSTART, ARCHITECTURE, API, DEVELOPMENT, LAW_CORPUS
master_plan/  Product plans and feature roadmap
.agents/      Per-task AI context files (read CLAUDE.md first)
```

## Running it

Full setup (corpus generation included): [docs/QUICKSTART.md](docs/QUICKSTART.md).

**Backend** (from `backend/`, see [backend/README.md](backend/README.md)):

```bash
# Bare metal
python3.11 -m venv .venv --system-site-packages && source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Or Docker (dev stack: API + Postgres + Redis)
./dev_runner.sh
```

**Frontend** (from `frontend/` — this project uses **fvm**, always prefix Flutter commands with it):

```bash
fvm flutter run -t lib/main_development.dart --flavor development
```

Entrypoints are `lib/main_development.dart` / `main_staging.dart` / `main_production.dart`, matching the Android flavors `development` / `staging` / `production`.

## Android APK

No prebuilt APK is committed to the repo. Build a debug APK yourself:

```bash
cd frontend
fvm flutter build apk --debug --flavor development -t lib/main_development.dart
# → build/app/outputs/flutter-apk/app-development-debug.apk
```

A fresh APK is also being built and shared in the **#fuzzzy-laws** Slack channel (2026-08-27).

## Status

- Law corpus (20,712 chunks, 3 collections): done.
- Backend + eval pipeline: done (647 tests across 38 files).
- Flutter app: active development — recently migrated onto the shared **`fuzzzy_ui_kit`** design system (path dependency on `fuzzy_design`); current work on feature branches (BYOK, no-account auth, per-tier model selection, local web serve).
- Production VPS deploy: not yet; a local + Tailscale test deploy runs with `AUTH_ENABLED=false`, `BYOK_REQUIRED=true`.

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md) — local environment in under 30 minutes.
- [Architecture](docs/ARCHITECTURE.md) — system design, data flows, database schema.
- [API Reference](docs/API.md) — all REST and WebSocket endpoints.
- [Development Guide](docs/DEVELOPMENT.md) — code style, testing, contribution.
- [Law Corpus](docs/LAW_CORPUS.md) — data sources, chunking, embedding.

AI contributors: read `CLAUDE.md` at the repo root first — it routes you to the mandatory per-task context files in `.agents/`.

## License

This project is licensed under the MIT License.
