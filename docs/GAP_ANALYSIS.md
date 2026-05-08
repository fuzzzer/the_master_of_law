# Documentation Gap Analysis

> **Last updated:** 2026-05-09

## What Exists

The project has substantial documentation scattered across multiple locations:

| Location | Content | Quality |
|----------|---------|---------|
| `GEMINI.md` | Project rules, mindset, compact architecture, status | High — but agent-facing |
| `.agents/context/backend.md` | Backend architecture, endpoints, patterns, gotchas | High — but agent-facing |
| `.agents/context/project_status.md` | Current completion state, next steps | High — but agent-facing |
| `.agents/context/production.md` | Full VPS deployment guide (531 lines) | High — but ops-facing |
| `.agents/context/law_corpus.md` | ChromaDB collections, querying, metadata | High — but agent-facing |
| `master_plan/01_law_corpus_agent_prompt.md` | Original law corpus pipeline spec (603 lines) | High — but spec, not docs |
| `master_plan/02_backend_system_prompt.md` | Original backend spec (862 lines) | High — but spec, not docs |
| `master_plan/03_design_system_prompt.md` | Design system spec (553 lines) | High — but design spec |
| `master_plan/04_feature_roadmap.md` | Feature phases, product vision (194 lines) | High — but roadmap |
| `eval/steps.md` | Evaluation pipeline runbook (197 lines) | High — but narrow scope |
| `.agents/workflows/*.md` | 8 predefined agent workflows | High — but agent-facing |

## What's Missing

### Contributor-Facing Documentation (None existed)

| Document | Audience | Why Needed |
|----------|----------|------------|
| `QUICKSTART.md` | New developers | Zero-to-running guide for local dev |
| `ARCHITECTURE.md` | All developers | System design, data flow, decision logs |
| `API.md` | Backend/Flutter devs | Complete endpoint reference with curl examples |
| `DEVELOPMENT.md` | Contributors | How to add features, run tests, git workflow |
| `LAW_CORPUS.md` | Legal advisors, data engineers | What data exists, how to extend it |
| Root `README.md` | Everyone | Project identity, features, quick links |

### Specific Gaps Found

1. **No root README.md** — The project had no README at all. Visitors to the repo see nothing.

2. **No setup instructions for new developers** — Production deploy is documented, but local development setup is scattered across agent context files.

3. **No API reference with examples** — `.agents/context/backend.md` lists endpoints in a table but lacks request/response schemas and curl examples.

4. **No explanation of "why"** — Specs say WHAT was built, but nowhere documents WHY each architecture choice was made (e.g., why ChromaDB over Vertex AI Vector Search, why 5-stage RAG, why Firebase Auth).

5. **No contributor git workflow** — No branching strategy, commit conventions, or PR process documented.

6. **No debugging guide** — Gotchas exist in `backend.md` but are not collected into a troubleshooting resource.

7. **No Flutter setup instructions** — The frontend package is `themasteroflaw` (in `frontend/`), but no docs explain how to run it.

8. **No eval pipeline guide for developers** — `eval/steps.md` exists but is buried; not linked from any contributor-facing doc.

## What's Scattered

| Information | Locations Found | Ideal Single Source |
|-------------|----------------|---------------------|
| Endpoint list | `backend.md`, `02_backend_system_prompt.md`, code | `docs/API.md` |
| Setup commands | `backend.md`, `production.md`, code comments | `docs/QUICKSTART.md` |
| RAG pipeline details | `backend.md`, `02_backend_system_prompt.md`, code | `docs/ARCHITECTURE.md` |
| Credit system | `backend.md`, `constants.py`, middleware code | `docs/ARCHITECTURE.md` |
| Database schema | `02_backend_system_prompt.md`, model files | `docs/ARCHITECTURE.md` |
| Legal codes list | `law_corpus.md`, `01_law_corpus_agent_prompt.md` | `docs/LAW_CORPUS.md` |
| Design system | `03_design_system_prompt.md`, `packages/open-design/` | (Out of scope for Task 05) |

## Prerequisites/Setup Steps Currently Undocumented

### Backend Local Development
- Python 3.11+ with `uv` or `pip` (not documented for new contributors)
- `.venv` creation and activation
- PostgreSQL 16 local install OR Docker-only workflow
- Redis local install OR Docker-only workflow
- GCP Application Default Credentials setup
- `alembic upgrade head` for migrations

### Flutter Local Development
- Flutter SDK 3.32.0+ (from `pubspec.yaml`)
- Dart SDK 3.8.0+
- Android Studio / Xcode for simulators
- `flutter pub get`

### Law Corpus Pipeline
- The `law_corpus/` directory has its own `.venv` and dependencies
- Not documented how to run scrapers, chunkers, or embedders independently

### Testing
- `pytest` with `pytest-asyncio`
- No documentation on how to run specific test suites
- No mention of test database setup
