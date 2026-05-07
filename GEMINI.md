# კანონის ოსტატი — The Master of Law

> AI-powered legal advocate for Georgian citizens. Case-centric architecture.

## Status: Step 3 — Design System & Flutter App 🔄

| Component | Status | Key File |
|-----------|--------|----------|
| Law Corpus (20,712 chunks, 3 collections) | ✅ Done | `law_corpus/data/chroma/` |
| Backend (27 endpoints) | ✅ Done | `.agents/context/backend.md` |
| Eval Pipeline (50 cases) | ✅ Done | `eval/steps.md` |
| Design System | 🔄 In Progress | `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` |
| Flutter App | 🔄 In Progress | `fuzzy_starter/` (package: `master_of_law`) |

## Context Loading — Read by Task

### Always read first:
- `.agents/context/project_status.md` — Current state, what's done, what's next

### By task:
| Task | Load These |
|------|-----------|
| **Backend work** | `.agents/context/backend.md` |
| **Flutter / UI** | `fuzzy_starter/.agents/orchestrator.md` → `fuzzy_starter/.agents/general_guide/flutter_architecture.md` |
| **Design system** | `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` |
| **Feature planning** | `master_plan/04_feature_roadmap.md` |
| **Production deploy** | `.agents/context/production.md` |
| **Law corpus** | `.agents/context/law_corpus.md` |
| **Evaluation** | `eval/steps.md` |
| **Original specs** | `master_plan/01_...`, `02_...`, `03_...` |

## Architecture (compact)

```
Flutter App (master_of_law, ge.fuzzycore.masteroflaw)
  │ 5 tabs: Chat │ Cases ⭐ │ Laws │ Notes │ Profile
  │ HTTPS / WebSocket + RAGCollectionConfig (feature flags)
  ▼
FastAPI Backend (27 endpoints, 10 services)
  │ Firebase Auth → Credit Gate → Rate Limit
  │ 5-stage RAG: Expand → Vector (multi-collection) → FullText → Merge → Rerank
  │ Source-specific prompt injection (court practice / Grand Chamber)
  │ Gemini 3.1 Pro legal analysis
  ▼
Data: PostgreSQL + ChromaDB (3 collections, 20,712 chunks) + Redis
  │ georgian_laws: 15,338 (12 legal codes)
  │ court_practice: 5,197 (Supreme Court rulings)
  │ grand_chamber: 177 (binding decisions)
```

## Core Decision: Cases = Projects

Every feature serves one purpose: building the strongest legal case.
Users dump raw info → AI organizes it.
Everything links to everything (facts ↔ arguments ↔ laws ↔ evidence ↔ conversations).
