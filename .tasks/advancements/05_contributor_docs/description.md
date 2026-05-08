# Task: Contributor Documentation

> **Covers:** Task 8 (Contributor Documentation)
> **Dependencies:** None — can run independently. Benefits from other tasks being complete to document their outputs.

---

## Purpose

Write comprehensive, well-organized documentation for:
1. **New contributors** — developers joining the project who need to understand the architecture, set up their environment, and start contributing
2. **Interested stakeholders** — legal professionals, investors, or partners who want to understand what the system does and how it works
3. **Future maintainers** — people who need to debug, extend, or refactor the system

Documentation must be easily readable, well-structured, and cover both the "why" and "how" of every major component.

---

## Multi-Step Guide

### Milestone 1: Audit Existing Documentation
1. Read ALL existing docs:
   - `GEMINI.md` — project rules and architecture
   - `.agents/context/backend.md` — backend architecture
   - `.agents/context/project_status.md` — current state
   - `.agents/context/production.md` — production setup
   - `.agents/context/law_corpus.md` — law corpus details
   - `master_plan/01_...`, `02_...`, `03_...` — original specs
   - `eval/steps.md` — eval pipeline
2. Identify gaps: what exists as tribal knowledge but isn't documented?
3. List all prerequisites and setup steps currently scattered across files
4. **Verify:** Gap analysis document listing what's missing

### Milestone 2: Quick Start Guide
1. Write `docs/QUICKSTART.md` — zero-to-running in < 30 minutes:
   - System requirements (macOS/Linux, Python 3.11+, Flutter 3.x, Docker)
   - Clone and initial setup
   - Backend: `cd backend && docker compose up -d` → health check
   - Flutter: `cd fuzzy_starter && flutter run`
   - First API call: curl example
   - Common errors and fixes
2. Include a "verify your setup" checklist at the end
3. **Verify:** A fresh machine can follow the guide and get a running system

### Milestone 3: Architecture Documentation
1. Write `docs/ARCHITECTURE.md`:
   - High-level system diagram (text/mermaid)
   - Data flow: user → Flutter → API → RAG → Gemini → response
   - Backend layer architecture: Route → Service → Repository → Model
   - Database schema (6 tables) with relationships
   - RAG pipeline: 5 stages with explanation of each
   - ChromaDB: 3 collections, what they contain, how they're queried
   - Credit system: tiers, costs, rate limits
   - Authentication: Firebase Auth → JWT → middleware
2. Include decision logs: WHY was each architecture choice made?
3. **Verify:** A new developer can understand the full system from this doc alone

### Milestone 4: API Reference
1. Write `docs/API.md`:
   - Every endpoint with: method, path, auth, credits, request body, response, example
   - Error codes and their meanings
   - Rate limiting behavior
   - WebSocket protocol for streaming chat
   - RAG collection config usage
2. Group by feature: Health, Auth, Chat, Cases, Laws, RAG, Credits
3. Include curl examples for every endpoint
4. **Verify:** All 27 endpoints documented with working curl examples

### Milestone 5: Development Guide
1. Write `docs/DEVELOPMENT.md`:
   - Code style and conventions
   - How to add a new endpoint (reference workflow `07_endpoint_builder.md`)
   - How to add a new service
   - How to modify the RAG pipeline
   - How to update the legal corpus
   - How to run tests
   - How to use the eval pipeline
   - Git workflow: branches, commits, PRs
2. Include common debugging scenarios and solutions
3. **Verify:** A contributor can follow the guide to add a new endpoint without external help

### Milestone 6: Law Corpus Documentation
1. Write `docs/LAW_CORPUS.md`:
   - What legal sources are included (12 codes, court practice, Grand Chamber)
   - How scraping works (matsne.gov.ge pipeline)
   - How chunking works
   - How embeddings are generated
   - How to add a new legal source
   - How to re-embed the corpus
   - Data quality guarantees and verification process
2. Include the full list of legal codes with their Georgian names and chunk counts
3. **Verify:** Someone can understand and extend the corpus from this doc

### Milestone 7: Root README Overhaul
1. Rewrite the root `README.md`:
   - Project name and mission (1 paragraph)
   - Features list
   - Quick start (link to `docs/QUICKSTART.md`)
   - Architecture overview (link to `docs/ARCHITECTURE.md`)
   - Contributing (link to `docs/DEVELOPMENT.md`)
   - License
   - Status badges (build, tests, coverage)
2. Keep it concise — 1 screenful, then links to detailed docs
3. **Verify:** README answers "what is this?" and "how do I get started?" in < 2 minutes of reading
