# 🔄 Session Resume Prompt

> **Copy-paste this to start ANY new AI conversation for this project.**
> **Last updated:** 2026-05-05

---

## Quick Start (paste to AI)

```
Read these files in order:

1. `current_steps.md` — Current project state and what's done/in-progress
2. `AI_GUIDE.md` — Full backend architecture, 25 endpoints, patterns
3. `master_plan/04_feature_roadmap.md` — Feature roadmap, user needs, 6 phases

For specific tasks, also load:
- Backend work → `handoff.md` + `startup_handoff.md`
- Design system → `packages/open-design/design-systems/kanonis-ostati/DESIGN.md`
- Flutter ui_kit → `fuzzy_starter/packages/ui_kit/lib/src/`
- Flutter architecture → `fuzzy_starter/.agents/general_guide/flutter_architecture.md`
- Production deploy → `PRODUCTION_SETUP.md`
- Original prompts → `master_plan/01_...`, `02_...`, `03_...`
```

---

## Where I Left Off

### Completed ✅
- **Step 1** — Law corpus: 9,450 chunks in ChromaDB, 12 Georgian legal codes
- **Step 2** — Backend: 25 endpoints, 10 services, 124 tests, Docker ready
- **Step 3a** — Design system: DESIGN.md created, case-centric architecture defined
- **Flutter rename** — `themasteroflaw` → `master_of_law`, bundle: `ge.fuzzycore.masteroflaw`

### In Progress 🔄
- Generating visual mockups via open-design (chat screen, case builder, laws, etc.)
- Once mockups done: extract design tokens → inject into Flutter ui_kit
- Then scaffold Flutter features and build navigation

### Current Phase
**Design System Generation → Flutter UI Kit → Flutter App MVP**

---

## Key Decisions Made

1. **Cases are projects** — The app is case-centric. Every chat, law article, note, and document connects to a case.
2. **5-tab navigation** — Chat, Cases (★ core), Laws, Notes, Profile
3. **Case Builder = command center** — Facts (favorable/unfavorable/neutral), arguments, applicable laws, defense strategy, timeline, evidence, risks, action plan, linked conversations
4. **AI as organizer** — Users dump raw info, AI structures and categorizes it
5. **Georgian-first** — Noto Sans Georgian primary, Inter for Latin, JetBrains Mono for article numbers
6. **Export-ready** — Every case should be exportable as a professional document for a real lawyer

---

## Project Map

```
the_master_of_law/
├── master_plan/             📐 Specs + roadmap (01=corpus ✅, 02=backend ✅, 03=design 🔄, 04=roadmap ✅)
├── law_corpus/              📚 Georgian law data (9,450 chunks, DO NOT MODIFY)
├── backend/                 🔧 FastAPI backend (25 endpoints, 10 services, 124 tests)
├── fuzzy_starter/           📱 Flutter app (renamed to master_of_law)
│   ├── packages/ui_kit/     🎨 Design system implementation (needs token injection)
│   └── packages/open-design/🖌️ Open-design tool for mockup generation
├── AI_GUIDE.md              📖 Backend architecture reference
├── handoff.md               📋 Backend handoff (detailed status)
├── startup_handoff.md       ▶️ How to start & test the backend
├── current_steps.md         📊 ★ Overall project progress tracker
├── PRODUCTION_SETUP.md      🚀 VPS deployment guide
└── RESUME_PROMPT.md         🔄 THIS FILE — session resume context
```
