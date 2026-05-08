# Progress: Feedback System + QA & AI Tester

> **Last updated:** _not started_
> **Agent:** _unassigned_

---

## Milestone 1: Design Feedback Data Model
- [ ] Design feedback schema (all fields defined)
- [ ] Design aggregation views
- [ ] Validate schema covers eval pipeline criteria
- [ ] **Milestone complete:** Schema finalized ✅

## Milestone 2: Backend — Feedback Endpoints
- [ ] Create `FeedbackModel` (SQLAlchemy)
- [ ] Generate Alembic migration
- [ ] Create `FeedbackRepository` with CRUD + aggregation
- [ ] Create `FeedbackService`
- [ ] Create endpoints: POST, GET per-case, GET summary, PATCH, DELETE
- [ ] Register routes in `main.py`
- [ ] Add to endpoint table in context docs
- [ ] Test via curl
- [ ] **Milestone complete:** All feedback endpoints work ✅

## Milestone 3: Flutter — Feedback UI
- [ ] "Review This Case" button on case detail
- [ ] `FeedbackSheet` bottom sheet widget
- [ ] Category selector chips
- [ ] Star rating widget
- [ ] Comment field
- [ ] Submit + confirmation toast
- [ ] `FeedbackHistoryWidget` for admin/owner view
- [ ] **Milestone complete:** Feedback submission works from Flutter ✅

## Milestone 4: Manual Test Cases
- [ ] Map all user-facing flows (5 tabs)
- [ ] Write auth test cases
- [ ] Write chat test cases
- [ ] Write case builder test cases
- [ ] Write law browser test cases
- [ ] Write credit/profile test cases
- [ ] Store as YAML/JSON in `tests/e2e/test_cases/`
- [ ] At least 30 test cases total
- [ ] **Milestone complete:** Test cases documented ✅

## Milestone 5: Backend Test Coverage Expansion
- [ ] Run `pytest --cov` baseline
- [ ] Write tests for uncovered services
- [ ] RAG pipeline edge case tests
- [ ] Credit system edge case tests
- [ ] State machine transition tests
- [ ] Citation extraction tests
- [ ] Coverage ≥ 85%
- [ ] **Milestone complete:** Coverage target met ✅

## Milestone 6: AI Tester Setup (Web E2E)
- [ ] Set up Playwright project in `tests/e2e/`
- [ ] Configure for Flutter web
- [ ] Write E2E scripts for core flows
- [ ] Create `run_tests.sh`
- [ ] Generate HTML report
- [ ] Verify all tests pass
- [ ] **Milestone complete:** E2E suite runs and reports ✅

## Milestone 7: Feedback-Driven Improvement Loop
- [ ] Create `feedback_analysis.py` script
- [ ] Group feedback by category
- [ ] Identify top 5 weakest areas
- [ ] Connect to eval pipeline
- [ ] **Milestone complete:** Improvement priorities generated ✅

---

## Blockers / Notes

_None yet._
