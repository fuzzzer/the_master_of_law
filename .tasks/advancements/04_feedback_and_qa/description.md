# Task: Case Review Feedback System + QA & AI Tester

> **Covers:** Task 6 (Case Review & Feedback Tracking) + Task 7 (Comprehensive QA & AI Tester)
> **Why combined:** Both are about quality validation. The feedback system captures human evaluations; the AI tester automates regression detection. They share test infrastructure, reporting formats, and the goal of driving continuous improvement.

---

## Purpose

### Case Review & Feedback System
Build a lightweight system for testers, legal experts, and interested parties to review AI-generated case analyses and submit structured feedback. Feedback is categorized, tracked, and centralized to drive future improvements.

### QA & AI Tester
Systematically test the application across all user-facing flows. Set up an automated AI tester that runs in the web environment, executes test scenarios, and reports failures.

---

## Multi-Step Guide

### Milestone 1: Design Feedback Data Model
1. Design the feedback schema:
   - `feedback_id` (UUID)
   - `case_file_id` or `conversation_id` (what's being reviewed)
   - `reviewer_id` (user or anonymous)
   - `reviewer_type` (tester | legal_expert | user | anonymous)
   - `category` (accuracy | completeness | relevance | formatting | citation_quality | legal_reasoning | overall)
   - `rating` (1-5 scale)
   - `comment` (free text, Georgian or English)
   - `specific_section` (which part of the case/response is being reviewed)
   - `created_at` (timestamp)
2. Design feedback aggregation views: per-case averages, per-category trends, worst-performing areas
3. **Verify:** Schema covers all feedback dimensions from the eval pipeline criteria

### Milestone 2: Backend — Feedback Endpoints
1. Create `FeedbackModel` (SQLAlchemy) and Alembic migration
2. Create `FeedbackRepository` with CRUD + aggregation queries
3. Create `FeedbackService` with:
   - `submit_feedback(case_id, reviewer, category, rating, comment)`
   - `get_feedback(case_id)` → all feedback for a case
   - `get_feedback_summary()` → aggregated stats across all cases
   - `get_category_trends()` → average rating per category over time
4. Create endpoints:
   - `POST /api/v1/feedback` — submit feedback (0 credits, auth optional for testers)
   - `GET /api/v1/feedback/{case_id}` — get feedback for a case
   - `GET /api/v1/feedback/summary` — aggregated dashboard data (ADMIN only)
5. Register routes, add to endpoint table
6. **Verify:** Submit feedback via curl, retrieve it, see summary stats

### Milestone 3: Flutter — Feedback UI
1. Add a "Review This Case" button on case file detail screen
2. Build `FeedbackSheet` — bottom sheet with:
   - Category selector (chips)
   - 1-5 star rating
   - Comment text field
   - Optional section selector (which part of the case)
   - Submit button
3. Build `FeedbackHistoryWidget` — shows past feedback on a case (for case owner/admin)
4. Feedback confirmation: toast notification after submission
5. **Verify:** Submit feedback from Flutter, see it in the admin summary

### Milestone 4: Identify & Write Manual Test Cases
1. Map all user-facing flows:
   - Auth: register → login → token refresh
   - Chat: create conversation → send message → receive response → view history
   - Cases: create case → fill intake → generate analysis → view case → export
   - Laws: browse codes → view articles → search → save to case
   - Profile: view credits → view transactions
2. For each flow, write test cases covering:
   - Happy path
   - Empty/null inputs
   - Georgian text edge cases
   - Network error handling
   - Unauthorized access
3. Store test cases in `tests/e2e/test_cases/` as structured YAML or JSON
4. **Verify:** At least 30 test cases covering all 5 tabs

### Milestone 5: Backend Test Coverage Expansion
1. Run `pytest --cov` to identify uncovered code
2. Write tests for any service/repository with < 80% coverage
3. Focus on:
   - RAG pipeline edge cases (empty results, single collection, all disabled)
   - Credit system edge cases (zero credits, concurrent deductions)
   - Conversation state machine transitions (invalid transitions)
   - Citation extraction (malformed article references)
4. **Verify:** Overall coverage ≥ 85%, no critical path untested

### Milestone 6: AI Tester Setup (Web Environment)
1. Choose framework: Playwright (recommended) or Cypress for web E2E testing
2. Set up the test runner project in `tests/e2e/`
3. Configure for the Flutter web build:
   - Build Flutter web: `cd frontend && flutter build web`
   - Serve locally and run tests against it
4. Write AI-assisted test scripts:
   - Use an LLM to generate Playwright test scripts from the YAML test cases
   - Each script: navigate → interact → assert → screenshot on failure
5. Create a `run_tests.sh` script that:
   - Starts the backend (docker compose)
   - Builds and serves Flutter web
   - Runs all E2E tests
   - Generates HTML report
6. **Verify:** `./run_tests.sh` executes all E2E tests and produces a pass/fail report

### Milestone 7: Feedback-Driven Improvement Loop
1. Create a `feedback_analysis.py` script that:
   - Reads all feedback from the database
   - Groups by category
   - Identifies the 5 weakest areas
   - Generates a prioritized improvement plan
2. Connect feedback insights to eval pipeline: low-scoring categories in feedback → new eval test cases
3. **Verify:** Script outputs a ranked list of improvement priorities
