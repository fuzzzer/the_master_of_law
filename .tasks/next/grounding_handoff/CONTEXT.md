# CONTEXT — System map & environment for the grounding executor

Everything below was verified live on 2026-07-19 by the planner/debugger agent.

## 1. Request lifecycle (where you will work)

Three AI entry points, all converging on one pipeline:

| Entry | File | Notes |
|---|---|---|
| REST chat | `backend/app/routes/chat_router.py` (`POST /api/v1/chat/{id}/send`) | simplest E2E test path |
| WS chat | `backend/app/routes/ws_chat_router.py` | primary app path; pipeline runs in `asyncio.create_task` |
| Case agent | `backend/app/routes/case_agent_router.py` | tools-heavy |

Pipeline: `app/services/agent_pipeline_service.py` → `AgentPipelineService.run()`
- Phase 1 PLAN (`_phase_1_plan`, Flash, JSON): intent, `search_queries`, optional direct answer.
- Phase 2 EXECUTE (`_phase_2_execute`): `rag.retrieve()` → `_format_law_context` → Gemini Pro
  chat with tools (`_select_tools`; tool loop max 5) → text.
- Phase 3 VERIFY (`_phase_3_verify`): `citation_service` extract → `verify_against_corpus`
  ({verified, corpus_found, not_found}) → Flash self-correction loop (max 2 iters).

RAG: `app/services/rag_retrieval_service.py` — Stage 0 expansion (skipped when planner supplies
queries) → Stage 1 multi-query vector (75/query, ALL collections in one pool — **this is the
imbalance bug**) → Stage 2 homemade keyword fulltext over `article_index.json` → Stage 3 merge →
Stage 4 Gemini rerank → quotas (laws 15 / cases 8) → threshold_service hits **prepended at
distance 0.0** (this is the pollution bug).

Citations: `app/services/citation_service.py` — `ARTICLE_PATTERN` matches `მუხლი N` only
(no sub-articles, no court cases). `_search_corpus_exact` does the live-corpus safety net.

Law browsing (basis for mechanism B): `app/services/law_browser_service.py` — `list_codes`,
`get_code`, `get_article` (article prefix → all chunks via chroma get), `search`. REST-only
today; NOT exposed as Gemini tools.

Tools: `app/tools/case_tools.py` — declarations + groups (`ALWAYS_TOOLS` = search_law only).
Executor: `app/services/case_tool_executor.py`.

Context caching (basis for mechanism C): `app/services/context_cache_service.py` (30-min TTL).
Domain classifier (basis for gating/routing): `app/services/legal_classifier_service.py` (9 domains).
Thresholds: `app/services/threshold_service.py` + `law_corpus/data/thresholds/`.

## 2. The transparency/trace suite (YOUR verification instrument)

Built 2026-07-19. Every AI request records ordered steps to Postgres `pipeline_traces`
(model `app/models/pipeline_trace.py`, migration `d41f8a2b9c03`).

- Record from anywhere: `from app.services.trace_service import record_step` →
  `record_step("step_name", key=value, ...)` (contextvar; no signature changes needed;
  no-op if no active trace). Routers own `start_trace`/`save_current_trace` — already wired.
- Existing step names you'll see: `request_received, guardrail_decision, phase_1_plan[_failed],
  rag_query_expansion, rag_vector_search, rag_fulltext_search, rag_merge_dedup, rag_rerank,
  rag_final_selection (full chunk texts), llm_generation_request (exact prompt),
  llm_requested_tools, tool_executed, llm_response, citation_verification, citation_correction,
  pipeline_result`.
- API (ADMIN; dev mode = auto-admin, no headers needed):
  `GET /api/v1/traces`, `/traces/sessions`, `/traces/{id}`,
  `/traces/{id}/export?format=markdown|json|text`,
  `/traces/conversation/{id}/export` (whole session).
- Dashboard: `http://127.0.0.1:8000/api/v1/traces/dashboard`.
- Settings flag: `TRACE_ENABLED` (default true). Tests: `tests/test_trace_service.py`.

## 3. Corpus & data layout

- ChromaDB (`law_corpus/data/chroma`, mounted in docker at `/app/law_corpus_data/chroma`):
  `georgian_laws` 15,338 / `court_practice` 5,197 / `grand_chamber` 177 chunks.
  chunk_id format: `<code>.article_<n>.chunk_<k>`; court: `court_practice:ას-175-2022:chunk_4:hash`.
  Metadata: `code_name, article_number ("მუხლი 48"), article_title, article_url
  (matsne.gov.ge/.../view/<docid>#article_<n>), _collection`.
- Parsed structured law (input for mechanism A): `law_corpus/data/georgian_laws/parsed/*.json`
  — 15 codes; per article: `article_id, code_name, book/part/chapter, article_number,
  article_title, content_ka, paragraphs (EMPTY — you populate), cross_references (EMPTY — you
  populate), effective_date, is_repealed`. Raw HTML for re-parsing: `.../raw/html/`.
- Indexes: `.../index/{article_index.json (2,118 keys), code_index.json, domain_index.json}`.
- Ingestion pipeline (exists — do not redesign): `law_corpus/scripts/run_full_pipeline.sh`,
  `run_incremental_update.sh`, `validate_corpus.py`; parser code in `law_corpus/modules|pipeline`.
- Embeddings: `gemini-embedding-001`, 768 dims; corpus used `RETRIEVAL_DOCUMENT`,
  queries MUST use `RETRIEVAL_QUERY` (`vertex_embedding_client.py`).

## 4. Environment (sharp edges — all verified)

- **Run stack**: `cd backend && docker compose up --build -d api`. Code changes need
  `--build` (image copies the code); `.env`-only changes need only `up -d api`.
- Stack: compose project "backend" — api on 127.0.0.1:8000, postgres + redis internal.
  Backend postgres is NOT on host port 5432 (host 5432 is an unrelated project!).
  DB access: `docker exec backend-postgres-1 psql -U fuzzzy_user -d fuzzzy_law -c "..."`.
  Migrations: `docker exec backend-api-1 alembic upgrade head`.
- **Gemini provider switch** (built 2026-07-19): `create_genai_client()` in
  `app/integrations/vertex_ai_client.py` — `GEMINI_API_KEY` set → free-tier Gemini API;
  empty → Vertex ADC (prod default, must stay untouched). Local `.env` has the debug block
  enabled: `GEMINI_API_KEY=...`, `GEMINI_MODEL=gemini-3-flash-preview`,
  `GEMINI_CHAT_MODEL=gemini-flash-lite-latest` (later duplicate keys win — comment the block
  out to restore Vertex). Key backup: `~/.config/master-of-law/gemini_debug_key.env`.
  Local ADC CANNOT reach Vertex (403 on both GCP projects) — free-tier is the only working
  local AI path. `gemini-2.5-flash-lite` is closed to new users (404) — don't use it.
- **Free-tier limits**: ~10-15 RPM; one chat request = 4-6 model calls + embeddings.
  Serialize E2E, sleep ≥20s between chat requests, expect and retry 429s.
- Tests: `cd backend && .venv/bin/python -m pytest tests/ -q` (venv rebuilt with uv; deps
  installed from pyproject list — editable install fails on flat layout, don't try).
- Dev auth: APP_ENV=development → no headers = mock ADMIN user. Chat E2E:
  `POST /api/v1/conversations` then `POST /api/v1/chat/{id}/send {"message": "..."}`.
- Noise to ignore: chromadb posthog telemetry errors; google-auth "quota project" warning.

## 5. Known pre-existing failures (NOT yours to fix, NOT regressions)

- `tests/test_agy_verification.py` — 2 tests need a live postgres on host:5432 with fuzzzy_user;
  that port belongs to another project on this machine. They fail with InvalidPasswordError.
  Full suite baseline: **472 passed, 2 failed** (as of 2026-07-19).

## 6. Audit findings driving the plan (trace `f9112db5-09eb-4ea8-a4ea-fd4419c8f796`, in DB)

Test Q: pregnancy dismissal (labor law). Findings:
1. Vector search: 450 hits → 188 court_practice / 11 grand_chamber / **1 georgian_laws**;
   Labor Code arts. 47/48 never retrieved. Model cited art. 48 from pretraining; Phase-3
   live-corpus lookup rescued it (correct URL `matsne.gov.ge/ka/document/view/1155567#article_48`,
   verified against live matsne).
2. threshold_service injected 3 criminal-law entries (arts. 40/29/115) at distance 0.0 into a
   labor prompt.
3. 5 Supreme Court cases (ას-1280-2019, ას-175-2022, ას-543-2020, ას-99-2021, ბს-922) were used
   for claims ("10 months salary" = 750×10 in ას-1280-2019 — grounded!) but NONE cited in the
   response; citation_service cannot see case numbers.
4. "მუხლი 48.8" extracted only as "მუხლი 48" (no sub-article granularity).
5. Response omitted the 30-day court deadline (it's in art. 48 itself) and the explicit
   pregnancy-dismissal prohibition (art. 47, present in corpus).
6. Language: 100% Georgian (verified programmatically). Answer substance: correct.

## 7. Where things live (quick index)

| What | Path |
|---|---|
| Plan | `.tasks/next/grounding_hardening_plan.md` |
| Verification protocol | `.tasks/next/grounding_handoff/VERIFICATION_PROTOCOL.md` |
| Trace suite service | `backend/app/services/trace_service.py` |
| Trace API + dashboard | `backend/app/routes/trace_router.py`, `backend/app/static/trace_dashboard.html` |
| Settings (flags) | `backend/app/config/settings.py`; RAG constants `app/config/constants.py` |
| Prompts | `backend/app/prompts/` (chat.py, advocate.py, agent_planning.py, rag_pipeline.py) |
| Eval harness | `eval/` (see `eval/steps.md`) |
| Certification output | `.tasks/audits/` (create it) |
