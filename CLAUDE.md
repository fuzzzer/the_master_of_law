# კანონის ოსტატი — The Master of Law

> AI-powered legal advocate for Georgian citizens. Case-centric architecture.

## Status: Step 3 — Design System & Flutter App 🔄

| Component | Status | Key File |
|-----------|--------|----------|
| Law Corpus (9,450 chunks) | ✅ Done | `law_corpus/data/chroma/` |
| Backend (25 endpoints) | ✅ Done | `.agents/context/backend.md` |
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
| **Original specs** | `master_plan/01_...`, `02_...`, `03_...` |

## Architecture (compact)

```
Flutter App (master_of_law, ge.fuzzycore.masteroflaw)
  │ 5 tabs: Chat │ Cases ⭐ │ Laws │ Notes │ Profile
  │ HTTPS / WebSocket
  ▼
FastAPI Backend (25 endpoints, 10 services)
  │ Firebase Auth → Credit Gate → Rate Limit
  │ 5-stage RAG: Expand → Vector → FullText → Merge → Rerank
  │ Gemini 3.1 Pro legal analysis
  ▼
Data: PostgreSQL + ChromaDB (9,450 law chunks) + Redis
```

## Core Decision: Cases = Projects

Every feature serves one purpose: building the strongest legal case.
Users dump raw info → AI organizes it.
Everything links to everything (facts ↔ arguments ↔ laws ↔ evidence ↔ conversations).
