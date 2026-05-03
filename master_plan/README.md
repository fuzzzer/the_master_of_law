# 🏛️ The Master of Law — Master Plan

> **კანონის ოსტატი** — The Ultimate Georgian Legal Assistant

## Vision

A production-grade AI-powered legal assistant that empowers any Georgian citizen — regardless of legal expertise — to understand their rights, navigate the legal system, and receive optimal legal guidance grounded entirely in Georgian legislation.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        USER (Flutter App)                         │
│  ● Conversational chat interface                                  │
│  ● Guided intake flow (situation → facts → legal area)            │
│  ● Law browser / search                                           │
│  ● Case history & saved analyses                                  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ HTTPS / WebSocket
                           ▼
┌────────────────────────────────────────────────────────────────────┐
│                   BACKEND (Python / FastAPI)                       │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │  Auth Guard   │  │  Rate Limiter │  │  Request Validator    │    │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘    │
│         └─────────────────┼──────────────────────┘                │
│                           ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Conversation Orchestrator                      │    │
│  │  ● Multi-turn context management                            │    │
│  │  ● Intake flow state machine                                │    │
│  │  ● Legal area classifier                                    │    │
│  └────────────────────────┬───────────────────────────────────┘    │
│                           ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              RAG Pipeline (Vertex AI)                       │    │
│  │  ● Embedding generation (text-embedding-005)                │    │
│  │  ● Vector search (Vertex AI Vector Search)                  │    │
│  │  ● Cross-encoder reranking                                  │    │
│  │  ● Citation extraction & verification                       │    │
│  └────────────────────────┬───────────────────────────────────┘    │
│                           ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Legal Analysis Engine                          │    │
│  │  ● Gemini 3.1 Pro (via Vertex AI)                           │    │
│  │  ● System prompt: Georgian legal expert persona             │    │
│  │  ● Grounded generation with mandatory citations             │    │
│  │  ● Defense strategy optimizer                               │    │
│  │  ● Plain-language explanation generator                     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Data Layer                                     │    │
│  │  ● PostgreSQL (conversations, users, case history)          │    │
│  │  ● Vector Store (law embeddings, article chunks)            │    │
│  │  ● Redis (session cache, rate limiting)                     │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│              LAW CORPUS PIPELINE (Offline Agent)                   │
│  ● Scrapes/downloads from matsne.gov.ge                           │
│  ● Parses legal documents (PDF, HTML, DOCX)                       │
│  ● Structure-aware chunking by article/section                    │
│  ● Metadata extraction (code, book, chapter, article, date)       │
│  ● Embedding generation & vector store ingestion                  │
│  ● Scheduled update pipeline (cron / Cloud Scheduler)             │
└────────────────────────────────────────────────────────────────────┘
```

---

## Three Agent Prompts

| # | Prompt File | Purpose |
|---|-------------|---------|
| 1 | [`01_law_corpus_agent_prompt.md`](./01_law_corpus_agent_prompt.md) | Agent that fetches, parses, structures, and indexes all Georgian legislation |
| 2 | [`02_backend_system_prompt.md`](./02_backend_system_prompt.md) | Agent that builds the Python/FastAPI backend with Vertex AI RAG pipeline |
| 3 | [`03_design_system_prompt.md`](./03_design_system_prompt.md) | Agent that defines the Flutter app's design system and UI specifications |

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Mobile App** | Flutter (Dart) | Cross-platform, existing wireframe |
| **Backend API** | Python 3.12 + FastAPI | Async, type-safe, excellent AI/ML ecosystem |
| **AI Model** | Gemini 3.1 Pro (Vertex AI) | Best-in-class reasoning, massive context window |
| **Embeddings** | `text-embedding-005` (Vertex AI) | Optimized for semantic search |
| **Vector Store** | Vertex AI Vector Search + ChromaDB (dev) | Managed, scalable, low-latency retrieval |
| **Database** | PostgreSQL 16 | Relational data, JSONB for flexible schemas |
| **Cache** | Redis 7 | Session management, rate limiting |
| **Containers** | Docker + Docker Compose | Reproducible builds, easy deployment |
| **CI/CD** | GitHub Actions → Cloud Run | Serverless, auto-scaling |
| **Law Source** | matsne.gov.ge | Official Georgian legislation portal |

---

## Key Design Principles

1. **Grounded in Law** — Every response must cite specific Georgian legal articles. Zero hallucination tolerance.
2. **User-First Language** — All legal concepts explained in plain Georgian/English. No legalese.
3. **Defense-Optimized** — The system always seeks the most favorable legal outcome for the user.
4. **Production-Grade** — Docker, health checks, structured logging, error tracking, rate limiting.
5. **Privacy-First** — User conversations are encrypted. No data shared with third parties.
6. **Saveable & Copyable** — AI responses and law articles can be saved as local notes, copied, annotated, and shared.
7. **Maintainable** — Clean architecture, one model per file, comprehensive testing, clear naming.

---

## Getting Started

1. Read each prompt file in order (01 → 02 → 03)
2. Execute the Law Corpus Agent first to build the knowledge base
3. Build the Backend System using the structured prompt
4. Generate the Design System and implement the Flutter app
5. Connect everything via Docker Compose

---

## Directory Structure (Target)

```
the_master_of_law/
├── master_plan/                    # ← You are here
│   ├── README.md
│   ├── 01_law_corpus_agent_prompt.md
│   ├── 02_backend_system_prompt.md
│   └── 03_design_system_prompt.md
│
├── backend/                        # Python/FastAPI backend
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── middleware/
│   │   └── utils/
│   └── tests/
│
├── law_corpus/                     # Law data pipeline
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── pipeline/
│   │   ├── scraper/
│   │   ├── parser/
│   │   ├── chunker/
│   │   ├── embedder/
│   │   └── indexer/
│   ├── data/
│   │   ├── raw/
│   │   ├── parsed/
│   │   ├── chunks/
│   │   └── embeddings/
│   └── tests/
│
├── flutter_app/                    # Flutter mobile application
│   ├── lib/
│   ├── assets/
│   └── ...
│
├── docker-compose.yml
├── .env.example
└── README.md
```
