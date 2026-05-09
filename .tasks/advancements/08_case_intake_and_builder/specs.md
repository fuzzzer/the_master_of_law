# Specs: Case Intake & AI Case Builder

---

## Chat Modes

| Mode | Prompt | Behavior |
|------|--------|----------|
| `chat` (default) | `CHAT_SYSTEM` | General Q&A, conversational, no intake |
| `case_intake` | `CASE_INTAKE_SYSTEM` | Intake interview, asks clarifying questions, signals readiness |

---

## Readiness Detection

| Signal | Condition |
|--------|-----------|
| **Text match** | AI response contains `✅` or `საკმარისი ინფორმაცია შევაგროვე` or `მზად ვარ სრული ანალიზისთვის` |
| **Heuristic** | `mode == case_intake` AND `msg_count >= 6` AND response has no `?`, `კითხვა`, or `დამაზუსტებელი` |

---

## Dual-Model Strategy

| Step | Model | Purpose |
|------|-------|---------|
| Query expansion | `gemini-3-flash-preview` | Convert colloquial text → legal search terms (fast, cheap) |
| Case file generation | `gemini-3.1-pro-preview` | Generate structured defense case from conversation + law context (accurate, thorough) |
| Chat responses | `gemini-3-flash-preview` | Real-time conversational responses |

---

## Case File JSON Schema (from CASE_BUILDER prompt)

```json
{
  "title": "string",
  "facts": {"what_happened": "", "when": "", "where": "", "who_involved": "", "key_evidence": ""},
  "evidence": {"has": [], "needs": [], "recommended_types": [], "deadlines": []},
  "applicable_laws": {
    "favorable": [{"code": "", "article": "", "explanation": "", "url": ""}],
    "against": [...],
    "neutral": [...]
  },
  "defense_strategies": [{"name": "", "success_likelihood": "", "risk_level": "", "legal_basis": [], "how_it_works": "", "what_you_need": "", "risks": ""}],
  "prosecution_args": [{"argument": "", "counter": ""}],
  "action_checklist": [{"deadline": "", "action": "", "done": false}],
  "lawyer_brief": {"key_points": [], "questions_to_ask": [], "documents_to_bring": []},
  "citations": [{"code": "", "article": "", "text": "", "url": ""}]
}
```

---

## Case Context Injection (for attached case in standalone chat)

Backend receives `case_context` string in `ChatSendRequest`. Injected before user message:

```
[ATTACHED CASE CONTEXT]
{serialized case data: facts, arguments, strategy, risks, linked articles}
[END CASE CONTEXT]

User question: {message}
```

---

## Go/No-Go Criteria

- [ ] Case intake asks clarifying questions (not just answers directly)
- [ ] Build Case button appears reliably after sufficient Q&A
- [ ] Case sections populate with AI-generated content after build
- [ ] Chat persists across case tab switches
- [ ] Case attachment in standalone chat works (AI references case data)
- [ ] Conversation titles auto-generated and visible in history
- [ ] No ducktape pattern-matching on user messages
