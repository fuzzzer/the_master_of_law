# Progress: Dynamic Pre-Generation Questionnaire

> **Last updated:** 2026-05-09
> **Agent:** Antigravity (Claude Opus 4.6)

---

## Milestone 1: Analyze Current Intake Flow
- [x] Read `backend/app/services/intake_flow_service.py`
- [x] Map conversation state machine transitions
- [x] Document current hardcoded vs dynamic questions
- [x] Identify `LegalClassifier` service and its 9 domains
- [x] **Milestone complete:** Current flow fully documented ✅

## Milestone 2: Design the Questionnaire Engine (Backend)
- [x] Design `QuestionnaireTemplate` model → `app/models/questionnaire.py`
- [x] Build Gemini-powered question generator → `app/prompts/questionnaire.py`
- [x] Define question schema (text, boolean, choice, date, number)
- [x] Build `QuestionnaireService` with generate/process/should_ask_more → `app/services/questionnaire_service.py`
- [ ] Unit tests for question generation
- [x] **Milestone complete:** Service generates domain-specific questions ✅

## Milestone 3: Integrate into Conversation State Machine
- [x] Add `QUESTIONNAIRE` state between INTAKE and CLARIFICATION → `app/config/constants.py`
- [x] Implement state transitions to/from QUESTIONNAIRE → `app/services/conversation_service.py`
- [x] Store answers in conversation context → `app/repositories/questionnaire_repository.py`
- [x] Handle skip flow for optional questions
- [x] Handle back/edit flow for previous answers
- [x] **Milestone complete:** Full state machine flow works end-to-end ✅

## Milestone 4: Backend API Endpoints
- [x] `POST /questionnaire/{id}/generate` endpoint
- [x] `GET /questionnaire/{id}` endpoint
- [x] `POST /questionnaire/{id}/answer` endpoint
- [x] `POST /questionnaire/{id}/skip` endpoint
- [x] Pydantic schemas for all request/response models → `app/schemas/questionnaire_schema.py`
- [x] Register routes in `main.py`
- [ ] Integration tests via curl
- [x] **Milestone complete:** All 4 endpoints wired ✅

## Milestone 5: Flutter UI
- [x] Build `QuestionnairePage` → `view/pages/questionnaire_page.dart`
- [x] Build type-specific question widgets (5 types: text, boolean, choice, date, number)
- [x] Progress indicator
- [x] Skip and back navigation
- [ ] Review screen with answer summary (not yet implemented)
- [x] **Milestone complete (partial):** Questionnaire flow works, review screen pending ✅

## Milestone 6: Domain-Specific Question Sets
- [x] Criminal law template (სისხლის სამართალი)
- [x] Labor law template (შრომის სამართალი)
- [x] Civil law template (სამოქალაქო სამართალი)
- [x] Family law and administrative law templates (bonus)
- [x] Store templates in config → `app/config/questionnaire_templates.py`
- [x] **Milestone complete:** Each domain generates different questions ✅

---

## Files Created

### Backend (8 files)
| File | Purpose |
|------|---------|
| `app/models/questionnaire.py` | ORM models (QuestionnaireQuestion, QuestionnaireAnswer) |
| `app/repositories/questionnaire_repository.py` | CRUD for questions and answers |
| `app/services/questionnaire_service.py` | AI question generation + lifecycle |
| `app/routes/questionnaire_router.py` | 4 API endpoints |
| `app/schemas/questionnaire_schema.py` | Pydantic request/response schemas |
| `app/prompts/questionnaire.py` | Gemini prompt for question generation |
| `app/config/questionnaire_templates.py` | Domain-specific baseline templates |

### Backend (4 files modified)
| File | Change |
|------|--------|
| `app/config/constants.py` | Added `QUESTIONNAIRE` phase to enum |
| `app/services/conversation_service.py` | Updated state transitions |
| `app/main.py` | Registered questionnaire router |
| `app/prompts/registry.py` | Registered questionnaire prompt |
| `alembic/env.py` | Registered questionnaire models |

### Flutter (5 files)
| File | Purpose |
|------|---------|
| `data/data_sources/questionnaire_remote_data_source.dart` | HTTP calls to 4 endpoints |
| `data/repositories/questionnaire_repository.dart` | Sealed-class error handling |
| `bloc/questionnaire_cubit.dart` | State management |
| `bloc/questionnaire_state.dart` | Immutable state |
| `models/questionnaire_models.dart` | Data models |
| `view/pages/questionnaire_page.dart` | Full-screen questionnaire UI |

---

## Remaining Work

1. **Run `./exp.sh`** — barrel file auto-generation
2. **Unit tests** — backend question generation tests
3. **Integration tests** — curl through full flow
4. **Review screen** — answer summary before proceeding to analysis
5. **Alembic migration** — `alembic revision --autogenerate` for new tables
6. **Flutter analyze** — `fvm flutter analyze` to catch any lint issues

## Blockers / Notes

- Architecture audit completed: code conforms to Flutter architecture guide (sealed responses, constructor injection, no hardcoded colors, exhaustive switch in cubits, single `src.dart` import)
- Backend follows existing patterns (Route → Service → Repository → Model)
