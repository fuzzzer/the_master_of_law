# Progress: Dynamic Pre-Generation Questionnaire

> **Last updated:** _not started_
> **Agent:** _unassigned_

---

## Milestone 1: Analyze Current Intake Flow
- [ ] Read `backend/app/services/intake_service.py`
- [ ] Map conversation state machine transitions
- [ ] Document current hardcoded vs dynamic questions
- [ ] Identify `LegalClassifier` service and its 9 domains
- [ ] **Milestone complete:** Current flow fully documented ✅

## Milestone 2: Design the Questionnaire Engine (Backend)
- [ ] Design `QuestionnaireTemplate` model
- [ ] Build Gemini-powered question generator
- [ ] Define question schema (text, boolean, choice, date, number)
- [ ] Build `QuestionnaireService` with generate/process/should_ask_more
- [ ] Unit tests for question generation
- [ ] **Milestone complete:** Service generates domain-specific questions ✅

## Milestone 3: Integrate into Conversation State Machine
- [ ] Add `QUESTIONNAIRE` state between INTAKE and CLARIFICATION
- [ ] Implement state transitions to/from QUESTIONNAIRE
- [ ] Store answers in conversation context
- [ ] Handle skip flow for optional questions
- [ ] Handle back/edit flow for previous answers
- [ ] **Milestone complete:** Full state machine flow works end-to-end ✅

## Milestone 4: Backend API Endpoints
- [ ] `POST /questionnaire/{id}/generate` endpoint
- [ ] `GET /questionnaire/{id}` endpoint
- [ ] `POST /questionnaire/{id}/answer` endpoint
- [ ] `POST /questionnaire/{id}/skip` endpoint
- [ ] Pydantic schemas for all request/response models
- [ ] Register routes in `main.py`
- [ ] Integration tests via curl
- [ ] **Milestone complete:** All 4 endpoints work correctly ✅

## Milestone 5: Flutter UI
- [ ] Build `QuestionnaireScreen`
- [ ] Build type-specific question widgets (5 types)
- [ ] Progress indicator
- [ ] Skip and back navigation
- [ ] Review screen with answer summary
- [ ] **Milestone complete:** Full questionnaire flow on device ✅

## Milestone 6: Domain-Specific Question Sets
- [ ] Criminal law template (სისხლის სამართალი)
- [ ] Labor law template (შრომის სამართალი)
- [ ] Civil law template (სამოქალაქო სამართალი)
- [ ] Store templates in config/DB
- [ ] **Milestone complete:** Each domain generates different questions ✅

---

## Blockers / Notes

_None yet._
