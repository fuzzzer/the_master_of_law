# Next Steps — Stabilization + Testing Handoff (2026-06-21)

## Objective
Resume point after the 2026-06-21 stabilization program. The app was reviewed, hardened,
fixed, and tested on web in dev mode. This doc captures **what was done**, **current status**,
**testing artifacts**, and **what to do next**.

> **Branch:** `stabilize/2026-06-20` (all work lives here; NOT merged, NOT deployed).
> **Full report:** `~/FuzzyCore_HQ/qa-reports/mol_fixes_2026-06-20/FINAL_REPORT.md`

---

## Current State (one-line)
Code is materially hardened and stable — **backend tests 378→396 passing, 0 failed; frontend
analyzes clean**. The **only** thing blocking a fully-working live app is **GCP IAM** (Vertex
403 on project `master-of-law-prod`) — environment/credentials, not code.

---

## What was done

### Reviews (46 findings across 3 passes + live QA)
- Deep backend review (agy): 17 · Security audit of payments/credits/limits/auth: 12 · Flutter review: 15 · Live QA: 2.
- Reports: `~/FuzzyCore_HQ/qa-reports/mol_backend_review_2026-06-20/`, `mol_security_2026-06-20/`, `mol_frontend_review_2026-06-20/`.

### Fixes applied (branch `stabilize/2026-06-20`)
**Security / billing / auth + DB constraints** (tickets T-0001..T-0007 resolved):
- WS chat `/chat/{id}/ws` now enforces tier + rate limit + credit check + `deduct` (was free unlimited AI). — `routes/ws_chat_router.py`
- `admin_api_key` default removed; **raises in production** if unset / insecure. — `config/settings.py:81-96`
- **Atomic credit deduction**: `with_for_update()` + CASE-guarded balance, raises on insufficient. — `repositories/credit_repository.py`
- Unique constraints on `user_credits.user_id` and `questionnaire_answers(conversation_id,question_id)` + idempotent **Alembic migration `c72b171e5c15`** (de-dups, then constrains). Applied: `alembic current` = head.
- Redis-backed sliding-window rate limiter (was in-memory/fail-open). — `middleware/rate_limit_middleware.py`
- Middleware reorder so ErrorHandler wraps Auth/Credit/RateLimit. — `main.py:106-114`
- SUPERADMIN feedback gate, api_keys caching, N+1 flush fix.

**Backend RAG/pipeline** (summary `mol_fixes_2026-06-20/dev_rag_fixes.md`):
- Async-offloaded ChromaDB / Vertex embeddings / full-text search (no more event-loop blocking).
- Citation: resolves each article ref to the preceding code (not the first); regex matches Georgian `177-ე`, `115¹`.
- Agent executes all parallel function calls; guardrail on Flash; rerank null-metadata crash guarded.

**Flutter frontend** (summary `mol_fixes_2026-06-20/dev_frontend_fixes.md`):
- Emit-after-close crash fixed; **real credits feature** wired to `/account/credits`; 401→clear key+route to `/auth`; 429 Georgian message; exception-translator Map guard; sane Dio timeouts (120s override for AI); analyze gate fixed (`ui_kit` pub get). `fvm flutter analyze` = 0 errors.

**Law browser** (T-0008 resolved):
- `get_article` was matching `where={"article_number": <chunk_id>}` (never matched) → every article drill-in empty. Now resolves article prefix from the code index, fetches chunks by id. Verified live. — `services/law_browser_service.py`

---

## Testing — what was run & where the artifacts are

### Backend regression suite
- Run in the api container (pytest is NOT in the image — install ad-hoc):
  ```
  docker-compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml exec -T api \
    sh -c "pip install -q pytest pytest-asyncio aiosqlite; python -m pytest tests/ -q"
  ```
- Baseline **378 passed / 7 failed / 51 skipped** → after fixes **396 passed / 0 failed / 51 skipped**.

### Full-app live QA (qa-tester) — `~/FuzzyCore_HQ/qa-reports/mol_qa_full_2026-06-20/`
- `report.md` — summary · `testcases.md` — TC matrix · `api/` — **25 endpoint proof records** · `screenshots/` — web (auth landing).
- Reusable API suite: `~/FuzzyCore_HQ/qa-reports/_testsuites/mol_api_full.sh`.
- **API verdict:** 23/25 clean; all error paths correct (404/422, never 500); AI 500 returns clean JSON.
- **Web verdict:** loads clean at `localhost:8080`, no console errors, auth gate redirects to `/auth`.
- **Tickets filed:** T-0008 (resolved), T-0009 (open).

### How to run the stack (env quirks — verified 2026-06-21)
- This Mac has **standalone `docker-compose` (hyphen)** — the `docker compose` plugin is NOT installed, so `dev_runner.sh` fails; use:
  `docker-compose -f backend/docker-compose.yml -f backend/docker-compose.dev.yml up --build -d`
- Flutter web dev: `cd frontend && fvm flutter run -d web-server --web-port=8080 -t lib/main_development.dart` (CORS already allows :8080).
- **Hot-reload doesn't fire over the macOS bind mount** — after editing backend code, `docker-compose ... restart api` to load it.
- Full env notes: `~/FuzzyCore_HQ/qa-reports/mol_fixes_2026-06-20/ENV_SETUP_NOTES.md`.

---

## Open / NOT yet done (pick up here)

### 🔴 BLOCKER — GCP IAM (gates all live AI + search)
Live AI returns **403 PERMISSION_DENIED** (`aiplatform.endpoints.predict`) on project
`master-of-law-prod`, model `gemini-3.1-pro-preview`. Code is correct.
**Action:** set `GCP_SA_KEY_PATH` in `backend/.env` to a valid service-account key for
`master-of-law-prod` with role **Vertex AI User**, OR grant the gcloud ADC account
`roles/aiplatform.user`. Then `docker-compose ... up -d --force-recreate api`.

### Then re-run QA with AI enabled (could not be tested in dev)
- Live chat journey (RAG + Gemini answer + citations), case-build (3cr), doc-gen (5cr).
- **Credit/free-tier ENFORCEMENT** — NOT exercised: dev mode mock-ADMIN + credit gate fails open. Test as a real FREE user; verify atomic deduction under concurrent requests, WS chat billing, daily reset.
- T-0009 — `/laws/search` masks the 403 as empty `200`; add a degraded-state signal / keyword fallback once embeddings work.

### Authenticated web UI not drivable here
- Flutter web renders to canvas; no Accessibility grant on this host. To QA authenticated screens: either grant Accessibility + use OS-level driving, or **add the `marionette_flutter` binding** to `main_development.dart` (per `~/FuzzyCore_HQ/playbooks/marionette-qa.md`) to make it QA-able. Verify: real credit balance renders, 401 routes to key prompt, 429 message, chat survives back-nav mid-stream.

### Product gaps
- **No payment/purchase/PRO-upgrade flow exists** (security MOL-SEC-11) — monetization unimplemented; only path off FREE is the admin key. Decide approach (Stripe / in-app purchase / manual).
- **F-12 (deferred):** bulk hardcoded Georgian strings + hex colors → ARB/`UiKitColors` migration; recommend a dedicated agy run (do not partially apply).

### Before merge
- Human review of the billing/auth diff (`credit_repository.py`, `ws_chat_router.py`, `firebase_auth_middleware.py`, migration `c72b171e5c15`) — authored by agy, which was cut off before self-summarizing.
- Merge `stabilize/2026-06-20` once GCP key + diff review are done.

---

## Ticket ledger
T-0001..T-0008 ✅ resolved · T-0009 ⏳ open (blocked on IAM). Files in `~/FuzzyCore_HQ/tickets/{resolved,open}/`.
