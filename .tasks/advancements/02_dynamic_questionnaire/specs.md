# Specs: Dynamic Pre-Generation Questionnaire

---

## Behavioral Specifications

### Question Generation

| Behavior | Specification |
|----------|---------------|
| Trigger | After legal domain is classified and initial description is received |
| Min questions | 3 per session (always ask at least the critical ones) |
| Max questions | 12 per session (prevent user fatigue) |
| Language | All questions in Georgian (ka). Hints/purposes also in Georgian. |
| Adaptation | If user's initial message already answers a question, skip it |
| Domain-awareness | Questions must be specific to the detected legal domain, not generic |
| Follow-up | If an answer reveals a new issue, the AI may append 1-2 follow-up questions |

### Question Types

| Type | Input Widget | Validation |
|------|-------------|------------|
| `text` | Multi-line text field | Min 5 chars for required fields |
| `boolean` | Yes/No toggle | Must select one |
| `choice` | Radio buttons or chips | Must select one from options |
| `date` | Date picker | Valid date, not in future (for past events) |
| `number` | Number input | Non-negative, contextual max (e.g., amount in GEL) |

### Conversation State Machine (Updated)

```
GREETING → INTAKE → QUESTIONNAIRE → CLARIFICATION → ANALYSIS → ADVICE → FOLLOW_UP
                         ↑                                                    |
                         └─── (if major new info surfaces) ←──────────────────┘
```

### Answer Storage

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | UUID | Parent conversation |
| `question_id` | str | Unique question identifier |
| `question_text` | str | The Georgian text of the question |
| `answer_value` | str | User's answer (normalized) |
| `answer_type` | enum | text/boolean/choice/date/number |
| `skipped` | bool | Whether user skipped this question |
| `answered_at` | datetime | Timestamp |

---

## Technical Constraints

### Backend
- `QuestionnaireService` follows singleton pattern per project convention
- Question generation uses Gemini (not a separate model) — reuse existing `genai.Client`
- Generated questions are validated against a Pydantic schema before sending to client
- Credit cost: 0 credits for questionnaire (it's part of the intake, not a paid analysis)
- Questionnaire state persists in PostgreSQL (survives server restarts)
- Rate limit: same as conversation endpoints

### Gemini Prompt for Question Generation
- System prompt must include: legal domain, user's description, existing question templates
- Temperature: 0.3 (low creativity — questions should be precise)
- Output: structured JSON array of questions (enforced via Gemini structured output)
- Must NOT ask questions that could be answered from the legal corpus itself
- Must focus on FACTS the user knows that the AI cannot retrieve

### API Contract

```
POST /api/v1/questionnaire/{conversation_id}/generate
  → 200: { "questions": [...], "total": N, "required_count": M }

GET /api/v1/questionnaire/{conversation_id}
  → 200: { "questions": [...], "answers": [...], "progress": {"answered": X, "total": Y} }

POST /api/v1/questionnaire/{conversation_id}/answer
  Body: { "question_id": "...", "answer": "..." }
  → 200: { "accepted": true, "next_question": {...} | null, "follow_ups": [...] }

POST /api/v1/questionnaire/{conversation_id}/skip
  → 200: { "skipped_count": N, "ready_for_analysis": true }
```

### Flutter
- Questionnaire renders as a full-screen flow (not inline in chat)
- Questions appear one-at-a-time with smooth transition animation
- Back button allows editing previous answers
- Progress bar at top (e.g., "3/8 questions answered")
- "Skip" button visible only for non-required questions
- Review screen at end shows all answers in a summary card
- Georgian keyboard should be default for text inputs

### Performance
- Question generation: < 3 seconds via Gemini
- Answer submission: < 500ms (just a DB write)
- Question rendering: instant (questions are pre-fetched)

### What This Is NOT
- NOT a static form — questions are AI-generated per case
- NOT a replacement for the chat — it's a structured pre-step before analysis
- NOT a survey — every question must have a clear legal purpose
