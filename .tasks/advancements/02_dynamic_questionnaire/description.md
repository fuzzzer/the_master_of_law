# Task: Dynamic Pre-Generation Questionnaire

> **Covers:** Task 1 (Dynamic Pre-Generation Questionnaire)
> **Dependency:** Benefits from Task 01 (Law Chat) being complete, but can be built independently on the backend first.

---

## Purpose

Before the AI generates a final legal document, defense case, or detailed legal advice, it should first gather structured, case-specific information from the user through a dynamic questionnaire. The AI designs the questions based on:
- The legal domain detected (criminal, civil, labor, etc.)
- The specific situation described so far
- What information gaps exist for building a strong case

This replaces the current static 6-question intake flow with an intelligent, adaptive process that asks only what's needed and asks it in the right order.

---

## Multi-Step Guide

### Milestone 1: Analyze Current Intake Flow
1. Read the existing intake flow in `backend/app/services/intake_service.py`
2. Read the conversation state machine: GREETING → INTAKE → CLARIFICATION → ANALYSIS → ADVICE → FOLLOW_UP
3. Map which questions are currently hardcoded and which are dynamic
4. Identify the `LegalClassifier` service and its 9 legal domains
5. **Verify:** Document the current flow with inputs/outputs for each state transition

### Milestone 2: Design the Questionnaire Engine (Backend)
1. Design a `QuestionnaireTemplate` model — a JSON structure defining questions per legal domain
2. Build a Gemini-powered question generator:
   - Input: conversation history + detected legal domain + user's initial description
   - Output: ordered list of questions with types (free text, yes/no, multiple choice, date, number)
3. Each question includes:
   - `question_text_ka` (Georgian)
   - `question_type` (text | boolean | choice | date | number)
   - `options` (for choice type)
   - `required` (boolean)
   - `purpose` (why this question matters — shown to user as hint)
   - `legal_relevance` (which legal argument this feeds into)
4. Build a `QuestionnaireService` with methods:
   - `generate_questionnaire(conversation_id, domain, context)` → list of questions
   - `process_answers(conversation_id, answers)` → enriched context for analysis
   - `should_ask_more(conversation_id)` → boolean (are there critical gaps?)
5. **Verify:** Unit tests — given a criminal case description, generates relevant questions about dates, witnesses, evidence, prior record

### Milestone 3: Integrate into Conversation State Machine
1. Add a new state: `QUESTIONNAIRE` between `INTAKE` and `CLARIFICATION`
2. The AI transitions to `QUESTIONNAIRE` after initial classification
3. Questions are sent one-at-a-time or in batches (configurable)
4. User answers are stored in the conversation's context
5. After all required questions are answered, transition to `ANALYSIS`
6. Allow users to skip non-required questions
7. Allow users to go back and change previous answers
8. **Verify:** Full state machine flow works: GREETING → INTAKE → QUESTIONNAIRE → ANALYSIS

### Milestone 4: Backend API Endpoints
1. `POST /api/v1/questionnaire/{conversation_id}/generate` — trigger question generation
2. `GET /api/v1/questionnaire/{conversation_id}` — get current questions + answers
3. `POST /api/v1/questionnaire/{conversation_id}/answer` — submit answer(s)
4. `POST /api/v1/questionnaire/{conversation_id}/skip` — skip remaining optional questions
5. Register routes, add schemas, wire into the conversation flow
6. **Verify:** curl through the full flow — generate → answer → answer → skip → get enriched context

### Milestone 5: Flutter UI
1. Build `QuestionnaireScreen` — renders questions in a form-like interface
2. Question type widgets: `TextQuestionWidget`, `BooleanQuestionWidget`, `ChoiceQuestionWidget`, `DateQuestionWidget`, `NumberQuestionWidget`
3. Progress indicator showing X of Y questions answered
4. "Skip remaining" button for non-required questions
5. Review screen showing all answers before proceeding to analysis
6. **Verify:** Complete the questionnaire flow on device, see answers reflected in the subsequent AI analysis

### Milestone 6: Domain-Specific Question Sets
1. Create baseline question templates for top 3 domains:
   - Criminal law (სისხლის სამართალი): dates, charges, evidence, witnesses, prior record, arrest details
   - Labor law (შრომის სამართალი): employment dates, contract type, termination reason, documentation
   - Civil law (სამოქალაქო სამართალი): parties, contract details, damages, timeline
2. Store templates in a config file or database
3. AI uses templates as a starting point, then adds/modifies based on specific context
4. **Verify:** Each domain generates a meaningfully different questionnaire
