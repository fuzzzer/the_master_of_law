# Project Status — ბუნდოვანი კანონი

> **Last verified:** 2026-05-12

## Completed ✅

### Step 1 — Law Corpus Pipeline
- 12 Georgian legal codes scraped from matsne.gov.ge → `georgian_laws` (15,338 chunks)
- Supreme Court rulings → `court_practice` (5,197 chunks)
- Grand Chamber binding decisions → `grand_chamber` (177 chunks)
- **Total: 20,712 chunks** in 3 ChromaDB collections
- All embedded with `gemini-embedding-001` (768-dim)
- Full citation metadata: `source_url`, `article_url`, `citation_text`, `document_number`
- Location: `law_corpus/` — **DO NOT MODIFY**

### Step 2 — FastAPI Backend
- 90 Python files, ~10,261 lines
- 36 API endpoints across 13 routers
- 14 services, 7 repositories, 8 models, 9 schemas
- 5-stage RAG pipeline (query expansion → vector → full-text → merge → rerank)
- Multi-collection RAG with per-request feature flags (`RAGCollectionConfig`)
- Source-specific prompt injection for court_practice and grand_chamber
- AI case agent with tool execution and questionnaire intake
- WebSocket streaming chat
- Firebase auth + API key auth, credit system (FREE/PRO/ADMIN), rate limiting
- 204 test functions across 24 test files
- Docker production setup
- Location: `backend/`

### Step 2b — Evaluation Pipeline ✅
- 50 real Supreme Court cases (32 criminal, 15 civil, 3 admin)
- LLM-as-judge scoring: verdict_alignment, legal_reasoning, article_accuracy, practical_value
- Holdout system: removes eval cases from ChromaDB during testing → restores after
- Crash-safe: results save after each case, auto-resume on restart
- Location: `eval/`

### Step 2c — Production Deployment ✅
- Hetzner VPS deployed with Nginx reverse proxy + SSL (Certbot)
- Domain: `api.zrdai.work`
- Firebase + API key authentication working
- Docker Compose (api + postgres + redis)
- Deploy script: `deploy.sh`

## In Progress 🔄

### Step 3a — Design System
- ✅ DESIGN.md created with case-centric architecture
- ✅ Case Builder specs defined (cases = projects, 9 sections)
- ✅ Feature roadmap (6 phases)
- 🔄 Visual mockup generation via open-design
- ⬜ Extract design tokens → Flutter ui_kit

### Step 3b — Flutter App
- ✅ Package: `fuzzzy_law` (`ge.fuzzycore.fuzzzylaw`)
- ✅ Features scaffolded: auth, cases, consultation, feedback, laws, profile
- ✅ WebSocket chat with streaming
- ✅ AI case intake flow with questionnaire
- ✅ Connected to production backend
- 🔄 Design system integration
- ⬜ RAG source toggles in chat UI
