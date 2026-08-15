# ბუნდოვანი კანონი — Fuzzzy Law

> AI-powered legal advocate for Georgian citizens.

## ⛔ MANDATORY: Read Before ANY Code

**You MUST complete these steps before writing a single line of code. No exceptions.**

### Step 1: Read the project mindset and coding principles
→ Read `.agents/context/mindset_and_principles.md` — **STOP** until you've internalized the rules.

### Step 2: Read the context file for YOUR task type

| Your task involves… | MUST read first |
|---------------------|-----------------|
| **Backend** (endpoints, services, DB, RAG) | `.agents/context/backend.md` |
| **Flutter / UI** | `frontend/.agents/orchestrator.md` → `frontend/.agents/general_guide/flutter_architecture.md` |
| **Production deploy** | `.agents/context/production.md` |
| **Debugging** | `.agents/debug_surgeon/context.md` |
| **Design system** | `packages/open-design/design-systems/fuzzzy-law/DESIGN.md` |
| **Law corpus / RAG tuning** | `.agents/context/law_corpus.md` + `.agents/rag_specialist/context.md` |
| **Feature planning** | `master_plan/04_feature_roadmap.md` |
| **Evaluation** | `eval/steps.md` |
| **New feature / architecture** | `.agents/code_architect/context.md` |
| **Security hardening** | `.agents/security_hardener/context.md` |

### Step 3: Verify current state

Before modifying any file, read it first. Check recent git history if behavior is unclear:
```bash
git log --oneline -10 -- <file>
```

---

## Architecture

```
Flutter App (fuzzzy_law, ge.fuzzycore.fuzzzylaw)
  │ Features: auth, cases, consultation, feedback, laws, profile
  │ HTTPS / WebSocket + RAGCollectionConfig (feature flags)
  ▼
FastAPI Backend (~10K lines, 90 files)
  │ 15 routers → 45 endpoints
  │ 19 services, 8 repositories, 9 models, 9 schemas
  │ Firebase Auth → Credit Gate → Rate Limit → Error Handler
  │ 5-stage RAG: Expand → Vector (per-collection quotas) → FullText → Merge → Rerank
  │ Grounding: article store (SQLite+FTS5) + get_article/browse_code tools + retrieval repair
  │ Gemini 3.1 Pro legal analysis + source-specific prompt injection
  │ Pipeline transparency traces (per-request step log + admin dashboard)
  │ 564 tests across 37 test files (562 passing; 2 pre-existing infra failures)
  ▼
Data: PostgreSQL + ChromaDB (3 collections, 20,712 chunks) + Redis
  │ georgian_laws: 15,338 (12 legal codes)
  │ court_practice: 5,197 (Supreme Court rulings)
  │ grand_chamber: 177 (binding decisions)
```

### Backend Layer Pattern
```
Route (thin, HTTP only) → Service (business logic) → Repository (DB) → Model (ORM)
```

### Tech Stack (non-negotiable)
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy 2.x async
- **AI SDK**: `google-genai` (NOT `google-cloud-aiplatform` or `vertexai`)
- **Vector DB**: ChromaDB (local, 20,712 docs)
- **Database**: PostgreSQL 16 via asyncpg
- **Cache**: Redis 7
- **Auth**: Firebase Authentication
- **Frontend**: Flutter (Dart) with BLoC/Cubit pattern

```python
from google import genai  # ✅ CORRECT — the ONLY way
import vertexai            # ❌ WRONG — never use this
```

### Key Identifiers
- **Package:** `fuzzzy_law` | **Bundle ID:** `ge.fuzzycore.fuzzzylaw`
- **GCP Project:** `gen-lang-client-0225498420` | **Region:** `us-central1`
- **LLM:** `gemini-3.1-pro` | **Embeddings:** `gemini-embedding-001` (768 dims)

---

## Core Decision: Cases = Projects

Every feature serves one purpose: building the strongest legal case.
Users dump raw info → AI organizes it.
Everything links to everything (facts ↔ arguments ↔ laws ↔ evidence ↔ conversations).

---

## Post-Task: Update Documentation

After completing any task that changes the codebase structure, you MUST:
1. Update the relevant context file (e.g., `backend.md` if you added/removed endpoints)
2. Ensure numbers match reality
3. See `.agents/workflows/09_doc_sync.md` for the full workflow.

---

## Current Status

> **Last verified:** 2026-05-12

| Component | Status | Location |
|-----------|--------|----------|
| Law Corpus (20,712 chunks, 3 collections) | ✅ Done | `law_corpus/data/chroma/` |
| Backend (36 endpoints, 14 services) | ✅ Done | `backend/` |
| Eval Pipeline (50 cases) | ✅ Done | `eval/` |
| Design System | 🔄 In Progress | `packages/open-design/` |
| Flutter App | 🔄 In Progress | `frontend/` |
| Production (Hetzner VPS) | 🔄 Deployed | `.agents/context/production.md` |
