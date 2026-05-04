# 🏛️ The Master of Law — Master Plan

> **კანონის ოსტატი** — Your AI Legal Advocate
> **Last updated:** 2026-05-05

## Mission

**Every Georgian citizen deserves adequate legal defense — regardless of income.**

The Master of Law is an AI-powered legal advocate that ensures no one walks into court unprepared, uninformed, or undefended. It uses the full text of Georgian legislation, combined with Gemini 3.1 Pro's reasoning, to build real defense strategies — citing exact law articles, identifying every applicable defense, and explaining it all in plain language.

This is not a legal Q&A chatbot. It is a **case-building tool** — it thinks like a lawyer, advocates for the user's best interest, organizes all case materials, and helps users achieve the most favorable legal outcome possible.

---

## Project Status

| Step | Component | Status | Files |
|------|-----------|--------|-------|
| 1 | Law Corpus Pipeline | ✅ **DONE** | `law_corpus/`, `01_law_corpus_agent_prompt.md` |
| 2 | FastAPI Backend | ✅ **DONE** | `backend/`, `02_backend_system_prompt.md` |
| 3 | Design System | 🔄 **IN PROGRESS** | `03_design_system_prompt.md`, `04_feature_roadmap.md` |
| 4 | Flutter App | 🔄 **IN PROGRESS** | `fuzzy_starter/` (package: `master_of_law`) |
| 5 | Integration & Deploy | ⬜ **FUTURE** | — |

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                      USER (Flutter App)                            │
│  ● Case Builder — the command center (cases = projects)            │
│  ● AI Chat — conversational legal consultation                     │
│  ● Law Browser — search & read Georgian legislation                │
│  ● Notes — save AI responses, articles, personal notes             │
│  ● Document Intelligence — upload & AI-analyze documents           │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ HTTPS / WebSocket
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                   BACKEND (Python / FastAPI)                       │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │  Auth Guard   │  │  Rate Limiter │  │  Credit Gate          │    │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘    │
│         └─────────────────┼──────────────────────┘                │
│                           ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              5-Stage RAG Pipeline                           │    │
│  │  Query Expansion → Vector Search → Full-Text → Merge       │    │
│  │  → Rerank → Legal Analysis (Gemini 3.1 Pro)                │    │
│  └────────────────────────┬───────────────────────────────────┘    │
│                           ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  10 Services: RAG, Analysis, Citation, Case Builder,       │    │
│  │  Intake Flow, Classifier, Explanation, Cache, Conversation │    │
│  └────────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Data: PostgreSQL + ChromaDB (9,450 law chunks) + Redis    │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│              LAW CORPUS PIPELINE (Offline, Complete)                │
│  ✅ 12 Georgian legal codes, 9,450 chunks, fully embedded          │
└────────────────────────────────────────────────────────────────────┘
```

---

## Prompt Files

| # | Prompt File | Purpose | Status |
|---|-------------|---------|--------|
| 1 | [`01_law_corpus_agent_prompt.md`](./01_law_corpus_agent_prompt.md) | Law corpus scraping, parsing, embedding, indexing | ✅ Done |
| 2 | [`02_backend_system_prompt.md`](./02_backend_system_prompt.md) | FastAPI backend with RAG pipeline, 25 endpoints | ✅ Done |
| 3 | [`03_design_system_prompt.md`](./03_design_system_prompt.md) | Flutter app design system and UI specifications | 🔄 In Progress |
| 4 | [`04_feature_roadmap.md`](./04_feature_roadmap.md) | Feature roadmap (6 phases), user needs, architecture | ✅ Created |

---

## Core Architecture Decision: Cases = Projects

The app is **case-centric**. Every feature serves one purpose: **building the strongest possible legal case**.

Users don't come to "chat with AI" — they come because they have a **legal problem** and need to organize, understand, and act on it. The Case is the central entity:

```
Case
├── Facts (favorable ✅ / unfavorable ❌ / neutral ℹ️)
├── Legal Arguments → linked to Law Articles
├── Applicable Laws → auto-linked from AI + manual
├── Defense Strategy → AI-generated + user-editable
├── Timeline → events + deadlines
├── Evidence → documents, photos, receipts
├── Risks & Weaknesses → honest assessment
├── Action Plan → checklist with deadlines
├── Linked Conversations → all related AI chats
└── Raw Documents → dump anything, AI analyzes it
```

**5-Tab Navigation:** Chat | Cases ⭐ | Laws | Notes | Profile

---

## Feature Roadmap (Summary)

| Phase | Goal | Key Features |
|-------|------|-------------|
| **1. MVP** | Working app with basic AI + law browsing | Chat, law browser, basic cases, notes |
| **2. Case Builder** | Case dashboard as command center | Facts, arguments, strategy, timeline, evidence |
| **3. AI Intelligence** | Context-aware AI, proactive guidance | Auto-categorization, gap detection, risk scoring |
| **4. Document Intelligence** | Upload anything, AI analyzes | OCR, fact extraction, deadline detection |
| **5. Advanced Guidance** | Genuine legal advisor | Counter-arguments, case export PDF, lawyer handoff |
| **6. Platform & Scale** | Beyond individual use | Cloud sync, court procedures, lawyer directory |

Full details in [`04_feature_roadmap.md`](./04_feature_roadmap.md)

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Mobile App** | Flutter (Dart) — `master_of_law` package, `ge.fuzzycore.masteroflaw` |
| **Backend API** | Python 3.11 + FastAPI (25 endpoints, 10 services) |
| **AI Model** | Gemini 3.1 Pro (Vertex AI, google-genai SDK) |
| **Embeddings** | gemini-embedding-001 (768 dims, 9,450 chunks) |
| **Vector Store** | ChromaDB (dev) → Vertex AI Vector Search (prod) |
| **Database** | PostgreSQL 16 (users, conversations, cases) |
| **Cache** | Redis 7 (sessions, rate limiting) |
| **Auth** | Firebase Authentication |
| **Design Tool** | open-design (Electron app, uses local Claude Code CLI) |
| **Containers** | Docker + Docker Compose |

---

## Key Design Principles

1. **Case-Centric** — The Case is the primary organizing unit. Everything connects to a case.
2. **Advocacy-First** — The system always acts as the user's advocate, never neutral.
3. **AI as Organizer** — Users dump raw information. AI structures and categorizes it.
4. **Grounded in Law** — Every claim cites specific Georgian articles. Zero hallucination.
5. **User-First Language** — All legal concepts in plain Georgian. No legalese.
6. **Export-Ready** — Every case exportable as professional document for real lawyers.
7. **Privacy-First** — Notes stored locally. Conversations encrypted.
8. **Georgian-First** — Noto Sans Georgian primary. Georgian text drives layout decisions.
9. **Progressive Disclosure** — Simple first, complexity on demand.

---

## Directory Structure

```
the_master_of_law/
├── master_plan/                    # ← You are here
│   ├── README.md                   # ★ This file
│   ├── 01_law_corpus_agent_prompt.md    # ✅ Step 1 spec
│   ├── 02_backend_system_prompt.md      # ✅ Step 2 spec
│   ├── 03_design_system_prompt.md       # 🔄 Step 3 spec
│   ├── 04_feature_roadmap.md            # Feature roadmap + user needs
│   └── design/                          # Design assets + open-design brief
│
├── law_corpus/                     # ✅ COMPLETE — DO NOT MODIFY
│   ├── pipeline/                   # Scraper → Parser → Chunker → Embedder → Indexer
│   ├── data/chroma/                # ChromaDB: 9,450 chunks
│   └── data/chunks/                # 12 JSON files (one per legal code)
│
├── backend/                        # ✅ COMPLETE — FastAPI backend
│   ├── app/                        # Main application (routes, services, models)
│   ├── tests/                      # 124 tests
│   └── docker-compose.yml          # Production deployment
│
├── fuzzy_starter/                  # 🔄 Flutter app (package: master_of_law)
│   ├── lib/                        # App source
│   ├── packages/ui_kit/            # Design system tokens
│   └── packages/open-design/       # Open-design tool (cloned)
│
├── init.md                         # Project overview + status
├── current_steps.md                # Progress tracker
├── RESUME_PROMPT.md                # Session resume context
├── AI_GUIDE.md                     # Backend architecture reference
├── handoff.md                      # Backend handoff document
├── startup_handoff.md              # Backend startup guide
└── PRODUCTION_SETUP.md             # VPS deployment guide
```
