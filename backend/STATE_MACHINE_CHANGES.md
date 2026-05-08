# State Machine Changes for Questionnaire Integration

This document describes the minimal changes needed to integrate the
`QUESTIONNAIRE` phase into the conversation state machine.

These changes are **documented as diffs** rather than applied directly
to avoid merge conflicts with parallel agents working on Tasks 03, 04, 05.

---

## 1. Add QUESTIONNAIRE to ConversationPhase enum

**File:** `backend/app/config/constants.py`

Add `QUESTIONNAIRE` between `INTAKE` and `CLARIFICATION`:

```python
class ConversationPhase(str, enum.Enum):
    """State machine phases for conversations."""
    GREETING = "GREETING"
    INTAKE = "INTAKE"
    QUESTIONNAIRE = "QUESTIONNAIRE"   # <-- ADD THIS
    CLARIFICATION = "CLARIFICATION"
    ANALYSIS = "ANALYSIS"
    ADVICE = "ADVICE"
    FOLLOW_UP = "FOLLOW_UP"
```

---

## 2. Update valid phase transitions

**File:** `backend/app/services/conversation_service.py`

Update `_VALID_TRANSITIONS` to include `QUESTIONNAIRE`:

```python
_VALID_TRANSITIONS: dict[ConversationPhase, list[ConversationPhase]] = {
    ConversationPhase.GREETING: [ConversationPhase.INTAKE],
    ConversationPhase.INTAKE: [ConversationPhase.QUESTIONNAIRE, ConversationPhase.CLARIFICATION],
    ConversationPhase.QUESTIONNAIRE: [ConversationPhase.CLARIFICATION, ConversationPhase.ANALYSIS],
    ConversationPhase.CLARIFICATION: [ConversationPhase.ANALYSIS, ConversationPhase.INTAKE],
    ConversationPhase.ANALYSIS: [ConversationPhase.ADVICE],
    ConversationPhase.ADVICE: [ConversationPhase.FOLLOW_UP, ConversationPhase.ANALYSIS],
    ConversationPhase.FOLLOW_UP: [ConversationPhase.ANALYSIS, ConversationPhase.FOLLOW_UP],
}
```

---

## 3. Update determine_next_phase heuristic

**File:** `backend/app/services/conversation_service.py`

In `determine_next_phase()`, add logic after INTAKE to move to QUESTIONNAIRE:

```python
# After enough intake → move to QUESTIONNAIRE
if current == ConversationPhase.INTAKE.value and message_count >= 2:
    return ConversationPhase.QUESTIONNAIRE

# After questionnaire complete → move to CLARIFICATION or ANALYSIS
if current == ConversationPhase.QUESTIONNAIRE.value:
    return ConversationPhase.CLARIFICATION
```

---

## Integration Point

The questionnaire service (`backend/app/services/questionnaire_service.py`) provides:

```python
async def should_ask_more(conversation_id: str) -> bool:
    ...

async def build_enriched_context(conversation_id: str) -> str:
    ...
```

These can be called from the chat router or conversation service to decide
when to transition from QUESTIONNAIRE to CLARIFICATION/ANALYSIS.
