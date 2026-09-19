# 📋 Session Log

> Quick notes from each working session. Write what you did, what worked, what didn't.

---

## Session: 2026-05-04 (Evening)

**Goal:** Set up project organization — agents, notes, production guide  
**Duration:** ~2 hours  
**What happened:**
- Created `.agents/` directory with thematic AI skill contexts
- Created `.user_notes/` directory for human-in-the-loop context
- Created `PRODUCTION_SETUP.md` with full VPS deployment guide
- Reviewed master plan — corpus ✅, backend ✅, design system prompt ✅ (ready for execution)
- Next: test backend endpoints, then start Flutter app

---

## Session: 2026-05-04 (Afternoon)

**Goal:** Test backend Docker stack  
**Duration:** ~3 hours  
**What happened:**
- Fixed Redis password issue (was empty, crashed Redis)
- Rewrote alembic/env.py for async + sys.path
- Created alembic/script.py.mako (was missing)
- Fixed alembic.ini URL to use Docker hostname
- Successfully ran migrations — 6 tables created
- Health check works, law search works
- Chat/send endpoint needs more testing (Vertex AI auth was the issue)
- Switched from API key to ADC auth for proper GCP billing

---

## Session: 2026-05-04 (Morning)

**Goal:** Launch backend Docker stack for first time  
**Duration:** ~2 hours  
**What happened:**
- `docker compose up -d` — all 3 containers started
- PostgreSQL healthy, Redis healthy, API running
- Hit initial issues with DB migrations — fixed env.py
- Backend architecture is solid — 25 endpoints, 10 services, all wired

---

<!-- Add new sessions at the top -->
