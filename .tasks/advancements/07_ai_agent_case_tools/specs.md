# Specs: AI Agent Case Tools

---

## Behavioral Specifications

### Tool Call Flow

| Step | Actor | Action |
|------|-------|--------|
| 1 | User | Sends message in `case_agent` mode |
| 2 | Backend | Sends message + tools to Gemini |
| 3 | Gemini | Returns text + optional `FunctionCall` |
| 4 | Backend | If non-destructive → execute immediately |
| 4b | Backend | If destructive → return `pending_confirmation` |
| 5 | Frontend | Show result or confirmation UI |
| 6 | User | Confirms/rejects (if needed) |
| 7 | Backend | Execute confirmed action |
| 8 | Frontend | Refresh case state |

### Tool Categories

| Category | Tools | Destructive |
|----------|-------|-------------|
| Read | `get_case_summary` | No |
| Create | `add_fact`, `add_argument`, `link_article`, `add_action_item`, `add_risk`, `set_strategy` | No |
| Update | `edit_fact`, `complete_action_item` | No |
| Delete | `delete_fact`, `delete_argument`, `unlink_article`, `delete_action_item` | **Yes** |

---

## API Schema

### Tool Execution Response (added to `ChatSendResponse`)

```json
{
  "response": "...",
  "tool_results": [
    {
      "tool_name": "add_fact",
      "status": "executed",
      "result": {"fact_id": "ai_fact_123", "text": "..."},
      "requires_confirmation": false
    },
    {
      "tool_name": "delete_argument",
      "status": "pending_confirmation",
      "confirmation_id": "conf_456",
      "description": "წაშალოთ არგუმენტი: 'თავდაცვის უფლება'?",
      "requires_confirmation": true
    }
  ]
}
```

### Confirmation Request

```
POST /api/v1/chat/{conversation_id}/confirm-tool
{
  "confirmation_id": "conf_456",
  "confirmed": true
}
```

### Confirmation Response

```json
{
  "status": "executed",
  "tool_name": "delete_argument",
  "result": {"deleted_id": "arg_789"}
}
```

---

## Gemini Function Declaration Schema

```python
CASE_TOOLS = [
    FunctionDeclaration(
        name="add_fact",
        description="Add a new fact to the user's legal case. Use when the user mentions a new event, circumstance, or detail.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The fact description"},
                "classification": {
                    "type": "string",
                    "enum": ["favorable", "unfavorable", "neutral"],
                    "description": "How this fact affects the case"
                }
            },
            "required": ["text", "classification"]
        }
    ),
    # ... other tools follow same pattern
]
```

---

## Technical Constraints

- **Max tool calls per message:** 5 (prevent runaway loops)
- **Tool execution timeout:** 5s per tool
- **Confirmation expiry:** 10 minutes (after that, user must re-request)
- **Credit cost:** Tool calls included in chat message cost (no extra charge)
- **Concurrent safety:** Tool executor must lock case during writes
- **Audit trail:** All tool executions logged with user_id, tool_name, timestamp, result

### Existing Infrastructure Used

| Component | Role |
|-----------|------|
| `CaseDetailCubit` (frontend) | Has all add/edit/delete methods already |
| `CaseFileRepository` (backend) | DB operations for case files |
| `VertexAIClient` | Needs function calling support added |
| `chat_router.py` | Needs `case_agent` mode handling |
| `ConsultationCubit` | Needs tool result handling + confirmation flow |

### State Management

```
Frontend:
  ConsultationState.pendingConfirmations: List<ToolConfirmation>
  ConsultationCubit.confirmToolAction(confirmationId)
  ConsultationCubit.rejectToolAction(confirmationId)

Backend:
  Redis key: tool_confirm:{confirmation_id} → {tool_name, args, user_id, case_id, expires_at}
  TTL: 600s (10 minutes)
```

---

## Go/No-Go Criteria

- [ ] All 13 tools defined and validated
- [ ] Non-destructive tools execute without confirmation
- [ ] Destructive tools show confirmation UI
- [ ] Confirmation timeout works (10 min)
- [ ] Case state refreshes after tool execution
- [ ] AI naturally uses tools in conversation (not forced)
- [ ] Max 5 tool calls per message enforced
- [ ] All tool executions logged
- [ ] No data corruption under concurrent access
