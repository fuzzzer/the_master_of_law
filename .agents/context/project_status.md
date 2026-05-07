# Project Status — კანონის ოსტატი

> **Last updated:** 2026-05-07

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
- 70+ files, ~5,000 lines, 27 API endpoints, 10 services, 5 repositories
- 5-stage RAG pipeline (query expansion → vector → full-text → merge → rerank)
- **Multi-collection RAG** with per-request feature flags (`RAGCollectionConfig`)
- Source-specific prompt injection for court_practice and grand_chamber
- `GET /api/v1/rag/collections` — list available sources with counts
- Gemini 3.1 Pro legal analysis with grounded citations
- Firebase auth, credit system (FREE/PRO/ADMIN), rate limiting
- Docker production setup, 124 tests passing
- Location: `backend/`

### Step 2b — Evaluation Pipeline ✅ NEW
- 50 real Supreme Court cases (32 criminal, 15 civil, 3 admin)
- LLM-as-judge scoring: verdict_alignment, legal_reasoning, article_accuracy, practical_value
- Holdout system: removes eval cases from ChromaDB during testing → restores after
- Crash-safe: results save after each case, auto-resume on restart
- Per-case AI generation export to `eval/test_cases/generations/evaluated/`
- v1 baseline: avg overall 3.47/5 (17 cases evaluated)
- v2 re-eval of low-scoring cases in progress
- Location: `eval/`

## In Progress 🔄

### Step 3a — Design System
- ✅ DESIGN.md created with case-centric architecture
- ✅ Case Builder specs defined (cases = projects, 9 sections)
- ✅ Feature roadmap (6 phases)
- 🔄 Visual mockup generation via open-design
- ⬜ Extract design tokens → Flutter ui_kit

### Step 3b — Flutter App
- ✅ Renamed: `themasteroflaw` → `master_of_law` (`ge.fuzzycore.masteroflaw`)
- ✅ 5-tab navigation: Chat, Cases ⭐, Laws, Notes, Profile
- ✅ Localization: Georgian (ka) + English (en)
- ⬜ Inject design tokens into ui_kit
- ⬜ Scaffold features using gen.sh
- ⬜ Implement navigation with GoRouter
- ⬜ Connect to backend API
- ⬜ **Implement RAG source toggles in chat UI** (feature flags for collections)

## Next Steps (Priority Order)
1. **Implement RAG collection feature flags in Flutter** (toggle laws/court/GC per chat)
2. Finish mockup generation in open-design
3. Extract design tokens → inject into `packages/ui_kit/`
4. Scaffold Flutter features (chat, case_builder, laws, notes, profile)
5. Build 5-tab bottom navigation
6. Connect law browser to backend API
7. Build basic AI chat with collection toggles

## Key Identifiers
- **App name:** კანონის ოსტატი (The Master of Law)
- **Package:** `master_of_law`
- **Bundle ID:** `ge.fuzzycore.masteroflaw`
- **GCP Project:** `gen-lang-client-0225498420`
- **Backend:** FastAPI on port 8000
- **Database:** PostgreSQL + ChromaDB (3 collections) + Redis
