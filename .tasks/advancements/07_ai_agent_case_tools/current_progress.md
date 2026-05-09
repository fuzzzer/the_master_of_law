# Progress: AI Agent Case Tools

> **Last updated:** 2026-05-09
> **Agent:** Antigravity

---

## Milestone 1: Gemini Function Calling Infrastructure
- [x] Extend `VertexAIClient` with `generate_with_tools()` method
- [x] Handle `FunctionCall` responses via `_extract_function_calls()`
- [x] Support multi-turn tool use loop in `case_agent_router.py`
- [x] **Milestone complete:** Function calling works ✅

## Milestone 2: Case Tool Definitions
- [x] Define all 13 tool schemas in `app/tools/case_tools.py`
- [x] Georgian + English descriptions for each tool
- [x] `DESTRUCTIVE_TOOLS` frozenset identifies 4 delete operations
- [x] `CASE_TOOLS` wrapper ready for Gemini API
- [x] **Milestone complete:** All tools defined ✅

## Milestone 3: Backend Tool Execution
- [x] Create `CaseToolExecutor` service (`app/services/case_tool_executor.py`)
- [x] Map all 13 tools to case file DB operations
- [x] Create dedicated `case_agent_router.py` with `/agent` and `/confirm-tool` endpoints
- [x] Handle multi-turn tool call loop in router (max 5 calls/message)
- [x] Return `pending_confirmation` for destructive actions via Redis/in-memory
- [x] Update `ChatSendResponse` schema with `tool_results` field
- [x] Add `ToolConfirmRequest` / `ToolConfirmResponse` schemas
- [x] Register router in `main.py` (routes 37→39)
- [x] **Milestone complete:** Backend executes tools ✅

## Milestone 4: Frontend Confirmation Flow
- [x] `ToolResultData` model in `consultation_state.dart`
- [x] `pendingConfirmations` and `caseFileId` state fields
- [x] `sendAgentMessage()` in `ConsultationCubit`
- [x] `confirmToolAction()` / `rejectToolAction()` in cubit
- [x] `enterAgentMode()` / `exitAgentMode()` in cubit
- [x] `sendMessage()` auto-routes to agent when `isAgentMode`
- [x] `sendAgentMessage` / `confirmToolAction` in data source + repository
- [ ] Confirmation card UI widget (visual component — deferred to UI pass)
- [ ] Refresh `CaseDetailCubit` after tool execution (needs UI integration)
- [x] **Milestone complete (data layer):** Confirmation flow wired ✅

## Milestone 5: Agent System Prompt
- [x] Create `CASE_AGENT_SYSTEM` prompt in `prompts/chat.py`
- [x] Register in prompt registry
- [x] Includes tool usage rules, conversation style, Georgian defaults
- [x] Dynamic `{case_context}` injection
- [x] **Milestone complete:** AI uses tools naturally ✅

## Milestone 6: Testing & Polish
- [x] 29 tests: definitions, executor, schemas, prompts (all passing)
- [x] Edge cases: wrong user, expired confirmation, unknown tool
- [x] Rate limit: `MAX_TOOL_CALLS_PER_MESSAGE = 5`
- [x] Audit logging via `_log_execution()`
- [x] **Milestone complete:** Production ready ✅

---

## Files Created/Modified

### New files
| File | Purpose |
|------|---------|
| `backend/app/tools/__init__.py` | Tools package init |
| `backend/app/tools/case_tools.py` | 13 FunctionDeclaration schemas |
| `backend/app/services/case_tool_executor.py` | Tool execution + confirmation tracking |
| `backend/app/routes/case_agent_router.py` | `/agent` and `/confirm-tool` endpoints |
| `backend/tests/test_case_agent_tools.py` | 29 tests |

### Modified files
| File | Change |
|------|--------|
| `backend/app/integrations/vertex_ai_client.py` | Added `generate_with_tools()` |
| `backend/app/prompts/chat.py` | Added `CASE_AGENT_SYSTEM` prompt |
| `backend/app/prompts/registry.py` | Registered new prompt |
| `backend/app/schemas/chat_schema.py` | Added tool result schemas, `case_file_id` |
| `backend/app/main.py` | Registered `case_agent_router` |
| `frontend/.../consultation_remote_data_source.dart` | Added agent + confirm APIs |
| `frontend/.../consultation_repository.dart` | Added agent + confirm methods |
| `frontend/.../consultation_state.dart` | Added `ToolResultData`, agent state |
| `frontend/.../consultation_cubit.dart` | Added agent mode + confirmation methods |

---

## Remaining Work (UI Polish Pass)
- [ ] Tool result chips in chat message bubbles (visual indicator)
- [ ] Confirmation card UI widget (confirm/reject buttons)
- [ ] Auto-refresh `CaseDetailCubit` after tool execution
- [ ] Agent mode toggle in `ConsultationPage` app bar
