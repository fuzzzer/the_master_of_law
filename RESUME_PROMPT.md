# 🔄 Session Resume Prompt

> **Copy-paste this to start ANY new AI conversation for this project.**

---

## Quick Start (paste to AI)

```
Read these files in order:

1. `.agents/init_prompt.md` — Your skill initialization (mindset + quality standards)
2. `.user_notes/priorities.md` — What I'm focused on right now
3. `.user_notes/session_log.md` — What happened in recent sessions
4. `AI_GUIDE.md` — Full backend architecture + all 25 endpoints

For specific tasks, also load:
- Code work → `.agents/code_architect/context.md`
- Debugging → `.agents/debug_surgeon/context.md`
- RAG/search → `.agents/rag_specialist/context.md`
- Production → `.agents/security_hardener/context.md` + `PRODUCTION_SETUP.md`
- Georgian law → `.agents/georgian_legal/context.md`
```

---

## Where I Left Off

Backend Docker stack runs (3 containers: postgres, redis, api). DB migrations applied (6 tables). Health endpoint works. Vertex AI auth uses ADC (mounted SA key).

**Tested ✅:** Health, law search, conversation creation  
**Needs testing:** Chat/send (full RAG + Gemini), case file builder, WebSocket streaming  

**Current phase:** Testing backend → Creating Flutter design system → Flutter app MVP

---

## Project Map

```
the_master_of_law/
├── .agents/                 ★ AI skill contexts (load relevant ones)
├── .user_notes/             ★ Human decisions, priorities, observations
├── master_plan/             📐 Design specs (01=corpus, 02=backend, 03=flutter)
├── backend/                 🔧 FastAPI backend (25 endpoints, 10 services)
├── law_corpus/              📚 Georgian law data (9,450 chunks, DO NOT MODIFY)
├── AI_GUIDE.md              📖 Backend architecture reference
├── PRODUCTION_SETUP.md      🚀 Full VPS deployment guide
├── STARTUP_STEPS.md         ▶️ How to start/test locally
└── current_steps.md         📊 Pipeline progress tracker
```
