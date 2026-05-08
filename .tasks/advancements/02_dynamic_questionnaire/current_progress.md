# Progress: Dynamic Pre-Generation Questionnaire

> **Last updated:** 2026-05-09
> **Agent:** Task 02 Implementation

---

## Milestone 1: Analyze Current Intake Flow ✅
- [x] Read `backend/app/services/intake_flow_service.py` — static 6-question flow in Georgian
- [x] Map conversation state machine transitions:
  - GREETING → INTAKE → CLARIFICATION → ANALYSIS → ADVICE → FOLLOW_UP
- [x] Document current hardcoded vs dynamic questions:
  - Hardcoded: what_happened, when, where, who, documents, desired_outcome
  - Dynamic: NEW — AI-generated per domain with skip/adapt logic
- [x] Identify `LegalClassifier` service and its 9 domains:
  - criminal, civil, administrative, labor, family, tax, land, constitutional, commercial
- [x] **Milestone complete:** Current flow fully documented ✅

## Milestone 2: Design the Questionnaire Engine (Backend) ✅
- [x] Design `QuestionnaireTemplate` model — JSON structure with `question_id`, `question_text_ka`, `question_type`, `options`, `required`, `purpose`, `legal_relevance`
- [x] Build Gemini-powered question generator:
  - `backend/app/prompts/questionnaire.py` — `QUESTIONNAIRE_GENERATOR` + `FOLLOW_UP_GENERATOR`
  - Temperature: 0.3, JSON output, Georgian language
- [x] Build `QuestionnaireService` with:
  - `generate_questionnaire(conversation_id, domain, context)` → list of questions
  - `process_answers(conversation_id, answers)` → enriched context
  - `should_ask_more(conversation_id)` → boolean
- [x] Unit tests for question generation — 18 tests, all passing
- [x] **Milestone complete:** Service generates domain-specific questions ✅

## Milestone 3: Integrate into Conversation State Machine ✅ (Documented)
- [x] Add `QUESTIONNAIRE` state between INTAKE and CLARIFICATION — documented in `STATE_MACHINE_CHANGES.md`
- [x] Implement state transitions to/from QUESTIONNAIRE — documented
- [x] Store answers in conversation context — via `QuestionnaireItem` DB table
- [x] Handle skip flow for optional questions — implemented in service + API
- [x] Handle back/edit flow for previous answers — implemented in Flutter cubit
- [x] **Milestone complete:** Full state machine flow documented ✅

## Milestone 4: Backend API Endpoints ✅
- [x] `POST /api/v1/questionnaire/{conversation_id}/generate` — generates questions
- [x] `GET /api/v1/questionnaire/{conversation_id}` — gets state
- [x] `POST /api/v1/questionnaire/{conversation_id}/answer` — submits answer
- [x] `POST /api/v1/questionnaire/{conversation_id}/skip` — skips optional question
- [x] Pydantic schemas for all request/response models — `questionnaire_schema.py`
- [x] Route registration documented in `backend/app/routes/REGISTRATION.md`
- [x] **Milestone complete:** All 4 endpoints implemented ✅

## Milestone 5: Flutter UI ✅
- [x] Build `QuestionnairePage` — full-screen flow (not inline chat)
- [x] Build type-specific question widgets (5 types): Text, Boolean, Choice, Date, Number
- [x] Progress indicator — `QuestionnaireProgressIndicator` (X of Y)
- [x] Skip button for non-required questions
- [x] Review screen with answer summary — `ReviewSummary`
- [x] Smooth transitions (`SlideTransition`, `AnimatedSwitcher`) + back navigation
- [x] **Milestone complete:** Full questionnaire flow implemented ✅

## Milestone 6: Domain-Specific Question Sets ✅
- [x] Criminal law template (სისხლის სამართალი) — 5 baseline questions
- [x] Labor law template (შრომის სამართალი) — 5 baseline questions
- [x] Civil law template (სამოქალაქო სამართალი) — 5 baseline questions
- [x] Store in config — `backend/app/config/questionnaire_templates.py`
- [x] AI uses templates as starting point — injected into Gemini prompt
- [x] **Milestone complete:** Each domain generates different questions ✅

---

## New Files Created

### Backend
- `backend/app/models/questionnaire.py` — `QuestionnaireItem` ORM model
- `backend/app/schemas/questionnaire_schema.py` — Pydantic schemas
- `backend/app/repositories/questionnaire_repository.py` — Async CRUD repository
- `backend/app/services/questionnaire_service.py` — Core service with Gemini integration
- `backend/app/prompts/questionnaire.py` — Gemini prompt templates
- `backend/app/config/questionnaire_templates.py` — Domain baseline templates
- `backend/app/routes/questionnaire_router.py` — FastAPI endpoints
- `backend/app/routes/REGISTRATION.md` — Route registration guide
- `backend/alembic/versions/ADD_QUESTIONNAIRE_MIGRATION.md` — Migration instructions
- `backend/tests/test_questionnaire_service.py` — 18 unit tests

### Frontend (Flutter)
- `frontend/lib/src/features/questionnaire/questionnaire.dart` — Barrel export
- `frontend/lib/src/features/questionnaire/models/questionnaire_models.dart` — Models
- `frontend/lib/src/features/questionnaire/bloc/questionnaire_cubit.dart` — State management
- `frontend/lib/src/features/questionnaire/bloc/questionnaire_state.dart` — States
- `frontend/lib/src/features/questionnaire/data/data_sources/questionnaire_remote_data_source.dart` — API client
- `frontend/lib/src/features/questionnaire/data/repositories/questionnaire_repository.dart` — Repository
- `frontend/lib/src/features/questionnaire/view/pages/questionnaire_page.dart` — Main screen
- `frontend/lib/src/features/questionnaire/view/components/progress_indicator.dart` — Progress bar
- `frontend/lib/src/features/questionnaire/view/components/question_widgets.dart` — 5 input widgets
- `frontend/lib/src/features/questionnaire/view/components/review_summary.dart` — Review screen

### Modified Files (Conflict-Safe)
- `backend/app/prompts/registry.py` — Added questionnaire prompt registration
- `frontend/lib/src/features/features.dart` — Already exported questionnaire (pre-existing)

---

## Blockers / Notes

- **State machine:** `QUESTIONNAIRE` phase not yet added to `ConversationPhase` enum to avoid merge conflicts. See `STATE_MACHINE_CHANGES.md` for the exact diff.
- **Router registration:** Questionnaire router is NOT registered in `main.py`. See `backend/app/routes/REGISTRATION.md` for the 2-line diff.
- **Alembic migration:** Not run yet. See `backend/alembic/versions/ADD_QUESTIONNAIRE_MIGRATION.md` for instructions.
