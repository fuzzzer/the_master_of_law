# კანონის ოსტატი — The Master of Law

> Your AI Legal Advocate — because every Georgian citizen deserves adequate defense.
> **Last updated:** 2026-05-05

---

## Project Status

| Step | Component | Status | Location |
|------|-----------|--------|----------|
| 1 | Law Corpus Pipeline | ✅ **COMPLETE** | `law_corpus/` |
| 2 | FastAPI Backend | ✅ **COMPLETE** | `backend/` |
| 3a | Design System | 🔄 **IN PROGRESS** | `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` |
| 3b | Flutter App | 🔄 **IN PROGRESS** | `fuzzy_starter/` (package: `master_of_law`) |
| 4 | Integration & Deploy | ⬜ **FUTURE** | — |

---

## Step 1 — Law Corpus Pipeline ✅ DONE

**Spec:** `master_plan/01_law_corpus_agent_prompt.md`

Built a complete Python pipeline that scraped, parsed, chunked, embedded, and indexed 12 Georgian legal codes from matsne.gov.ge. 9,450 chunks in ChromaDB with full citation metadata.

---

## Step 2 — FastAPI Backend ✅ DONE

**Spec:** `master_plan/02_backend_system_prompt.md`

Built a production-grade backend with 25 endpoints, 10 services, 5-stage RAG pipeline (vector + full-text + rerank), Gemini 3.1 Pro legal analysis, Firebase auth, credit system, and Docker deployment. 124 tests passing.

---

## Step 3 — Design System & Flutter App 🔄 IN PROGRESS

**Spec:** `master_plan/03_design_system_prompt.md`
**Design:** `packages/open-design/design-systems/kanonis-ostati/DESIGN.md`
**Roadmap:** `master_plan/04_feature_roadmap.md`

### What's Done
- Comprehensive DESIGN.md with case-centric architecture
- Flutter app renamed: `fuzzystarter` → `master_of_law` (`ge.fuzzycore.masteroflaw`)
- 5-tab navigation defined: Chat, Cases (★), Laws, Notes, Profile
- Feature roadmap with 6 phases
- User needs analysis
- Case Builder as the core feature (cases = projects, everything links)

### What's In Progress
- Visual mockup generation via open-design
- Design token extraction → Flutter ui_kit injection

### What's Next
- Scaffold Flutter features using `gen.sh`
- Implement navigation with GoRouter
- Connect to backend API

---

## Step 4 — Connect Everything ⬜ FUTURE

- Flutter ↔ Backend API integration
- Firebase Auth setup
- End-to-end testing
- App Store / Play Store preparation

---

## Core Architecture Decision: Cases Are Projects

The app is **case-centric**. Every feature serves one purpose: building the strongest possible legal case.

```
Case (= Project)
├── Facts (favorable / unfavorable / neutral)
├── Arguments (linked to law articles)
├── Applicable Laws (auto-linked from AI + manual)
├── Defense Strategy (AI-generated + user-editable)
├── Timeline (events + deadlines)
├── Evidence (documents, photos)
├── Risks & Weaknesses
├── Action Plan (checklist)
├── Linked Conversations (AI chats)
└── Documents (raw uploads → AI analyzes)
```

Users **dump** raw information. The AI **organizes** it.

---

## Key Files

| Purpose | File |
|---------|------|
| **Resume any session** | `RESUME_PROMPT.md` |
| **Current progress** | `current_steps.md` |
| **Backend reference** | `AI_GUIDE.md` |
| **Backend details** | `handoff.md` |
| **Start backend** | `startup_handoff.md` |
| **Design system** | `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` |
| **Feature roadmap** | `master_plan/04_feature_roadmap.md` |
| **Flutter architecture** | `fuzzy_starter/.agents/general_guide/flutter_architecture.md` |
| **Production deploy** | `PRODUCTION_SETUP.md` |

---

## Project Map

```
the_master_of_law/
├── master_plan/                    # Specs + roadmap
│   ├── 01_law_corpus_agent_prompt.md   # ✅ Step 1 spec
│   ├── 02_backend_system_prompt.md     # ✅ Step 2 spec
│   ├── 03_design_system_prompt.md      # 🔄 Step 3 spec
│   ├── 04_feature_roadmap.md           # Feature roadmap + user needs
│   ├── design/                         # Design assets
│   └── README.md
├── law_corpus/                     # ✅ COMPLETE (9,450 chunks)
├── backend/                        # ✅ COMPLETE (25 endpoints, 124 tests)
├── fuzzy_starter/                  # 🔄 Flutter app (master_of_law)
│   ├── packages/ui_kit/            # Design system implementation
│   └── packages/open-design/       # Open-design tool
├── AI_GUIDE.md                     # Backend architecture
├── handoff.md                      # Backend handoff
├── current_steps.md                # Project tracker
├── RESUME_PROMPT.md                # Session resume
├── startup_handoff.md              # Backend startup guide
├── PRODUCTION_SETUP.md             # VPS deploy guide
└── init.md                         # ★ THIS FILE
```
