# Current Steps — კანონის ოსტატი Project Tracker

> **Last updated:** 2026-05-05

---

## Step 1 — Law Corpus Pipeline ✅ COMPLETE

- 12 Georgian legal codes scraped from matsne.gov.ge
- 9,450 chunks parsed, embedded (gemini-embedding-001, 768-dim), indexed in ChromaDB
- All P0 laws present, 2 P1 laws unavailable (entrepreneurial_law, consumer_rights_law)
- Full citation data verified: `source_url`, `article_url`, `citation_text`, `document_number`

**Location:** `law_corpus/` — DO NOT MODIFY

---

## Step 2 — FastAPI Backend ✅ COMPLETE

- 70+ files, ~5,000 lines
- 25 API endpoints (8 routers)
- 10 services (RAG, legal analysis, citation, case builder, intake flow, classifier, explanation, context cache, conversation, law browser)
- 5 repositories (user, credit, conversation, message, case_file)
- 5-stage RAG pipeline (query expansion → vector search → full-text → merge → rerank)
- Full middleware stack (Firebase auth, credit gate, rate limit, error handler, CORS)
- Docker production setup (PostgreSQL + Redis + API)
- 124 tests passing
- All prompts extracted to `app/prompts/` (typed PromptTemplate classes)

**Location:** `backend/`

**Remaining:**
- [ ] Run Alembic migrations on real DB
- [ ] Install `structlog` (when network available)
- [ ] End-to-end testing with real Gemini API

---

## Step 3 — Design System & Flutter App 🔄 IN PROGRESS

### 3a. Design System (current)
- ✅ Comprehensive DESIGN.md created for open-design tool
- ✅ Case-centric architecture defined (Cases = Projects, everything links to cases)
- ✅ 5-tab navigation: Chat, Cases, Laws, Notes, Profile
- ✅ Full component specifications (chat bubbles, case dashboard, citation chips, etc.)
- ✅ Feature roadmap with 6 phases defined
- ✅ User needs analysis documented
- 🔄 Generating visual mockups via open-design (in progress)
- [ ] Extract design tokens from mockups → Flutter ui_kit
- [ ] Generate remaining screen mockups (Case Builder, Laws, Notes, Onboarding)

### 3b. Flutter App Setup
- ✅ `fuzzy_starter` project cloned and configured
- ✅ Renamed: `fuzzystarter` → `master_of_law`
- ✅ Bundle ID: `ge.fuzzycore.masteroflaw` (+ `.stg`, `.dev` flavors)
- ✅ Class names: `MasterOfLawApp`, `MasterOfLawHttpClient`, `MasterOfLawLocalizations`
- ✅ All barrel exports regenerated via `./exp.sh`
- ✅ Georgian (ka) + English (en) localization already configured
- [ ] Inject design tokens into ui_kit (UiKitColors, UiTextStyles, UiFormStyles)
- [ ] Scaffold features (chat, case_builder, laws, notes, profile)
- [ ] Implement 5-tab bottom navigation with GoRouter
- [ ] Connect to backend API

**Location:** `fuzzy_starter/` (package name: `master_of_law`)

---

## Step 4 — Connect Everything ⬜ FUTURE

- [ ] Flutter ↔ Backend API integration
- [ ] Firebase Auth setup
- [ ] End-to-end flow: chat → analysis → case builder
- [ ] App Store / Play Store preparation

---

## Key Design Files

| File | Purpose |
|------|---------|
| `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` | Complete design system for open-design tool |
| `master_plan/04_feature_roadmap.md` | Feature roadmap (6 phases) + user needs |
| `master_plan/03_design_system_prompt.md` | Original design system spec |
| `master_plan/design/open_design_brief.md` | Screen-by-screen prompts for open-design |
| `master_plan/design/DESIGN.md` | Predefined design tokens (reference) |

---

## Project Structure (Current)

```
the_master_of_law/
├── master_plan/                    # Design specs + roadmap
│   ├── 01_law_corpus_agent_prompt.md   # ✅ Step 1 spec (DONE)
│   ├── 02_backend_system_prompt.md     # ✅ Step 2 spec (DONE)
│   ├── 03_design_system_prompt.md      # 🔄 Step 3 spec (IN PROGRESS)
│   ├── 04_feature_roadmap.md           # ✅ Feature roadmap + user needs
│   ├── design/                         # Design assets + open-design brief
│   └── README.md
├── law_corpus/                     # ✅ COMPLETE — DO NOT MODIFY
├── backend/                        # ✅ COMPLETE — FastAPI + 25 endpoints
├── fuzzy_starter/                  # 🔄 Flutter app (renamed to master_of_law)
│   ├── packages/ui_kit/            # Design system implementation
│   └── packages/open-design/       # Open-design tool (cloned)
├── AI_GUIDE.md                     # Backend architecture reference
├── handoff.md                      # Backend handoff document
├── current_steps.md                # ★ THIS FILE
├── RESUME_PROMPT.md                # Session resume prompt
└── init.md                         # Original project init prompt
```
