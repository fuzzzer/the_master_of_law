# Backend Context — Fuzzzy Law

> FastAPI backend with multi-source RAG pipeline + Gemini 3.1 Pro legal analysis.
> **Last verified:** 2026-07-19

---

## Architecture

```
Flutter App → HTTP/WS with Firebase ID token (or API key)
  → CORS → Firebase Auth → Credit Gate → Rate Limit → Error Handler
  → Route Handler → Service → Repository → Response
```

### RAG Pipeline (core feature)
```
User Message + RAGCollectionConfig (feature flags)
  → [Stage 0] Gemini Query Expansion (5-10 formal Georgian legal terms)
  → [Stage 1] Multi-Query Vector Search (ChromaDB, per-collection quotas:
              laws 40 / practice 25 / chamber 10 per query — statutes can't be crowded out)
  → [Stage 2] Multi-Query Full-Text Search (JSON indices, top-50 per query)
  → [Stage 3] Merge & Deduplicate by chunk_id
  → [Stage 4] Gemini Rerank over a per-collection-balanced pool
              (laws 50 / practice 40 / chamber 10) → quotas laws 15 / cases 8
  → Threshold lookup (exact-value tables), gated by keyword-classified domain
  → [optional] Whole-code injection (FULL_CODE_INJECTION, labor/constitution)
  → Legal Analysis (Gemini 3.1 Pro + tools: search_law, get_article, browse_code)
  → Citation Verification + retrieval repair (full-text confirm/correct via article store)
  → Court-case + sub-article verification, anchoring check, uncertainty policy
  → [optional] Faithfulness pass (FAITHFULNESS_CHECK, Flash sentence audit)
```

### Grounding mechanisms (2026-07-19 hardening)
- **Article store (mechanism A)** — SQLite+FTS5 `law_corpus/data/georgian_laws/article_store.db`
  (12 codes, 5,325 articles, 18,314 paragraphs), built by
  `law_corpus/scripts/build_article_store.py` (pipeline step; also in incremental update).
  Backend access: `article_store_service` (`get_article(code, article, paragraph)`,
  `fts_search`, `get_code_full_text`). Deterministic (code, article, paragraph) → full text + matsne anchor.
- **Navigation tools (mechanism B)** — Gemini tools `get_article` / `browse_code`
  (in ALWAYS_TOOLS), backed by the article store; trace steps `article_store_lookup`, `tool_executed`.
- **Whole-code injection (mechanism C)** — `FULL_CODE_INJECTION` flag (default OFF = prod no-op):
  labor/constitutional questions get the entire code injected (trace step `full_code_injected`);
  statute chunk retrieval becomes irrelevant for those domains.
- **Generation contract** — retrieval repair (`retrieval_repair` step), anchored-claims metric
  (`anchoring_check`), faithfulness pass (`FAITHFULNESS_CHECK` flag, default OFF),
  zero-grounding disclaimer (`uncertainty_disclaimer_added`).
- **Verification net** — court-case numbers verified against `case_id` metadata
  (`case_citation_verification`), sub-articles against store paragraphs (`subarticle_verification`),
  live drift sampling (`law_corpus/scripts/drift_check.py`).
- **Eval loop** — `eval/golden_retrieval.yaml` (30 validated Q→article pairs) +
  `eval/run_golden_retrieval.py` (scores certification checks C1–C8 per trace, CI-able);
  grounding metrics endpoint + dashboard panel; `eval/run_weekly_audit.sh`.

### RAG Collection Feature Flags
```python
class RAGCollectionConfig(BaseModel):
    legal_codes: bool = True       # georgian_laws (15,338 chunks)
    court_practice: bool = True    # court_practice (5,197 chunks)
    grand_chamber: bool = True     # grand_chamber (177 chunks)
    
# Usage in chat request:
{"message": "...", "rag_config": {"legal_codes": true, "court_practice": false}}
```

**Source-specific prompt injection:** When court_practice/grand_chamber chunks are retrieved,
source-specific instructions are appended to the system prompt (e.g., "Grand Chamber
decisions are BINDING and override all lower court interpretations").

---

## Codebase Stats

| Metric | Count |
|--------|-------|
| Router files | 15 |
| Endpoints | 45 |
| Services | 19 |
| Repositories | 8 |
| Models | 9 |
| Schemas | 9 |
| Test files | 37 |
| Test functions | 540 |

---

## API Endpoints (44 total, 15 routers)

### health_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/health` | 0 | Liveness |
| GET | `/api/v1/health/ready` | 0 | Readiness (reports collection count) |

### auth_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/auth/verify-token` | 0 | Firebase token → user |
| GET | `/api/v1/auth/me` | 0 | Current user |

### account_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/account/credits` | 0 | Credit balance |
| GET | `/api/v1/account/transactions` | 0 | Credit history |

### conversation_router (4)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/conversations` | 0 | Start conversation |
| GET | `/api/v1/conversations` | 0 | List conversations |
| GET | `/api/v1/conversations/{id}` | 0 | Get with messages |
| DELETE | `/api/v1/conversations/{id}` | 0 | Delete |

### chat_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/chat/{id}/send` | **1** | Send → AI response (accepts `rag_config`) |

### ws_chat_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| WS | `/api/v1/chat/{id}/ws` | 1 | WebSocket streaming (accepts `rag_config`) |

### case_file_router (6)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/case-files/build` | **3** | Build defense case (accepts `rag_config`) |
| GET | `/api/v1/case-files` | 0 | List case files |
| GET | `/api/v1/case-files/{id}` | 0 | Get case file |
| PATCH | `/api/v1/case-files/{id}` | 0 | Update notes/status |
| DELETE | `/api/v1/case-files/{id}` | 0 | Delete case file |
| POST | `/api/v1/case-files/{id}/generate-document` | **5** | Generate official DOCX document |

### case_agent_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/chat/{id}/agent` | — | AI agent interaction |
| POST | `/api/v1/chat/{id}/confirm-tool` | — | Tool confirmation |

### questionnaire_router (5)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/questionnaire/{id}/generate` | — | Generate questionnaire |
| GET | `/api/v1/questionnaire/{id}` | 0 | Get questionnaire state |
| POST | `/api/v1/questionnaire/{id}/answer` | — | Submit answer |
| POST | `/api/v1/questionnaire/{id}/skip` | — | Skip question |
| POST | `/api/v1/questionnaire/{id}/extract` | — | Extract case data |

### law_browser_router (4)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/laws/search?q=...` | 0 | Search laws (free) |
| GET | `/api/v1/laws/codes` | 0 | List codes |
| GET | `/api/v1/laws/codes/{id}` | 0 | Code structure |
| GET | `/api/v1/laws/articles/{id}` | 0 | Article text |

### feedback_router (5)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/api/v1/feedback` | 0 | Submit feedback |
| GET | `/api/v1/feedback/summary` | 0 | Aggregated dashboard (ADMIN) |
| GET | `/api/v1/feedback/{target_id}` | 0 | Get feedback for target |
| PATCH | `/api/v1/feedback/{id}` | 0 | Update own feedback |
| DELETE | `/api/v1/feedback/{id}` | 0 | Delete own feedback |

### rag_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/rag/collections` | 0 | List RAG sources + availability |

### api_key_router (2)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/api-keys/check` | 0 | Check API key validity |
| POST | `/api/v1/api-keys` | 0 | Create API key (ADMIN) |

### contacts_router (1)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/contacts` | 0 | List beneficial official contacts |

### trace_router (7) — pipeline transparency (ADMIN)
| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/traces` | 0 | List trace summaries (filter by conversation/user) |
| GET | `/api/v1/traces/sessions` | 0 | Traces grouped per conversation |
| GET | `/api/v1/traces/dashboard` | 0 | HTML debugging dashboard (public page, data admin-only) |
| GET | `/api/v1/traces/metrics/grounding` | 0 | Grounding health rates over recent traces (dashboard panel) |
| GET | `/api/v1/traces/{trace_id}` | 0 | Full step-by-step trace |
| GET | `/api/v1/traces/{trace_id}/export` | 0 | Export one trace (json \| markdown \| text) |
| GET | `/api/v1/traces/conversation/{id}/export` | 0 | Export whole session for AI verification |

---

## Services (19)

| Service | Purpose |
|---------|---------|
| agent_pipeline_service | Unified 3-phase pipeline (plan → execute+tools → verify/repair) |
| article_store_service | Deterministic article lookups (SQLite+FTS5, mechanism A) |
| grounding_metrics_service | Grounding health aggregation over traces (plan 4.1) |
| rag_retrieval_service | 5-stage RAG pipeline |
| legal_analysis_service | Gemini system prompt + grounded analysis |
| citation_service | Extract `მუხლი N` patterns, verify against corpus |
| case_builder_service | 8-section defense case (3 credits) |
| case_tool_executor | Tool execution for case agent |
| conversation_service | State machine + message persistence |
| intake_flow_service | 6 guided questions in Georgian |
| questionnaire_service | Structured case intake questionnaire |
| legal_classifier_service | 9 legal domains classification |
| explanation_service | Simplify legal language |
| context_cache_service | 30-min TTL per conversation |
| law_browser_service | Search/browse corpus (free) |
| guardrail_service | Input/output safety checks |
| threshold_service | Credit threshold management |
| document_generator_service | AI drafts official documents to DOCX |
| trace_service | Step-by-step pipeline transparency recording (contextvar-based) |

---

## Key Patterns

### Dependency Injection
```python
@router.post("/endpoint")
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    repo = MyRepository(db)
```

### Gemini API (google-genai SDK)
```python
from app.integrations.vertex_ai_client import create_genai_client
client = create_genai_client()  # Vertex AI (ADC) by default; Gemini API if GEMINI_API_KEY is set
```

**CRITICAL:** Use `google-genai` only. NOT `google-cloud-aiplatform` or `vertexai`.

**Provider switch:** setting `GEMINI_API_KEY` in `.env` routes ALL Gemini calls
(chat, planner, rerank, embeddings) through the free-tier Gemini Developer API —
for local debugging only, never production. Models switch via `GEMINI_MODEL` /
`GEMINI_CHAT_MODEL` env vars (cheap: `gemini-3-flash-preview`, `gemini-flash-lite-latest`).
Comment the debug block in `.env` out to restore Vertex AI unchanged.

### Pipeline Transparency (tracing)
Every AI request (rest_chat / ws_chat / case_agent) records a step-by-step trace
to `pipeline_traces`: request → guardrail → plan → RAG stages (queries, hits,
rerank, final chunks with full law text) → exact Gemini prompt → tool calls →
citation verification → final response. Controlled by `TRACE_ENABLED` (default true).

```python
from app.services.trace_service import record_step, start_trace, save_current_trace
start_trace(entry_point="rest_chat", user_message=msg, ...)   # router, before pipeline
record_step("my_step", key=value)                              # anywhere in the pipeline (contextvar)
await save_current_trace(status="completed", response_text=t)  # router, all exit paths
```

Debug UI: `GET /api/v1/traces/dashboard` (in prod, paste `ADMIN_API_KEY` into the
key field). Session export for AI review: `GET /api/v1/traces/conversation/{id}/export`.

---

## Credit System

| Tier | Credits | Rate Limit |
|------|---------|------------|
| FREE | 5/day (auto-reset) | 5 req/min |
| PRO | Purchased | 30 req/min |
| ADMIN | 10,000 | 120 req/min |

---

## Config

| Setting | Value |
|---------|-------|
| GCP Project | `gen-lang-client-0225498420` |
| Region | `us-central1` |
| LLM | `gemini-3.1-pro` |
| Embeddings | `gemini-embedding-001` (768 dims) |
| ChromaDB | 3 collections: `georgian_laws`, `court_practice`, `grand_chamber` |
| DB | PostgreSQL 16 (8 models: user, user_credits, conversation, message, case_file, feedback, questionnaire, database) |
| FULL_CODE_INJECTION | default `false` — whole-code prompt injection (mechanism C); enable per env |
| FAITHFULNESS_CHECK | default `false` — Flash faithfulness pass per response; enable per env |

---

## Running

```bash
# Local
cd backend && source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Docker
cd backend && docker compose up --build -d
docker compose exec api alembic upgrade head

# Tests
.venv/bin/python -m pytest tests/ -v  # 564 tests (562 pass; 2 pre-existing infra failures)
```

---

## File Reference

| Task | Files |
|------|-------|
| Add endpoint | `routes/`, `schemas/`, register in `main.py` |
| Business logic | `services/` |
| DB queries | `repositories/` |
| Add DB table | `models/` → `alembic/env.py` → run migration |
| Change auth | `middleware/firebase_auth_middleware.py` |
| Change credits | `config/constants.py` → `CreditAction` |
| Change RAG | `config/constants.py` → `RAG_*` |
| Gemini prompts | `app/prompts/` |

---

## Gotchas

1. ChromaDB telemetry errors from posthog — harmless, ignore
2. Embedding consistency — corpus uses `RETRIEVAL_DOCUMENT`, queries MUST use `RETRIEVAL_QUERY`
3. Georgian text — always UTF-8 (Mkhedruli U+10D0–U+10FF)
4. Dev mode — no Firebase token needed, mock ADMIN user
5. Credit gate — fails open in dev, closed in production
