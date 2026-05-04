# 🏛️ The Master of Law — Master Plan

> **კანონის ოსტატი** — Your AI Legal Advocate

## Mission

**Every Georgian citizen deserves adequate legal defense — regardless of income.**

The Master of Law is an AI-powered legal advocate that ensures no one walks into court unprepared, uninformed, or undefended. It uses the full text of Georgian legislation, combined with Gemini 3.1 Pro's reasoning, to build real defense strategies — citing exact law articles, identifying every applicable defense, and explaining it all in plain language.

This is not a legal Q&A chatbot. It is a **defense tool** — it thinks like a lawyer, advocates for the user's best interest, and helps them achieve the most favorable legal outcome possible. Today it starts with criminal defense (the area where bad outcomes are most devastating), then expands to civil, administrative, and labor law.

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
│  │  ● Embedding generation (gemini-embedding-001 via google-genai) │  │
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
| **Embeddings** | `gemini-embedding-001` (Vertex AI, google-genai SDK) | 3,072-dim, excellent multilingual quality |
| **Vector Store** | Vertex AI Vector Search + ChromaDB (dev) | Managed, scalable, low-latency retrieval |
| **Database** | PostgreSQL 16 | Relational data, JSONB for flexible schemas |
| **Cache** | Redis 7 | Session management, rate limiting |
| **Containers** | Docker + Docker Compose | Reproducible builds, easy deployment |
| **CI/CD** | GitHub Actions → Cloud Run | Serverless, auto-scaling |
| **Law Source** | matsne.gov.ge | Official Georgian legislation portal |

---

## Key Design Principles

1. **Advocacy-First** — The system always acts as the user's advocate. It seeks the most favorable legal outcome, identifies every defense, and never remains neutral when the user's rights are at stake.
2. **Criminal Defense Priority** — Criminal cases have the highest stakes (freedom, record, family). The system prioritizes criminal law completeness and defense strategy quality above all other legal areas.
3. **Grounded in Law** — Every claim must cite specific Georgian legal articles. Zero hallucination tolerance. If a law doesn't support a defense, the system says so honestly.
4. **User-First Language** — All legal concepts explained in plain Georgian/English. No legalese. A citizen with no legal education should understand every word.
5. **Defense-Optimized** — Present multiple defense strategies ranked by likelihood of success. Include risks, timelines, and concrete next steps.
6. **Production-Grade** — Docker, health checks, structured logging, error tracking, rate limiting.
7. **Privacy-First** — User conversations are encrypted. Legal situations are deeply personal — no data shared with third parties.
8. **Saveable & Copyable** — AI responses and law articles can be saved as local notes, copied, annotated, and shared (e.g., with a real lawyer).
9. **Maintainable** — Clean architecture, one model per file, comprehensive testing, clear naming.

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
