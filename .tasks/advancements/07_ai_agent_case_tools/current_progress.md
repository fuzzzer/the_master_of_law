# Progress: AI Agent Case Tools

> **Last updated:** _not started_
> **Agent:** _unassigned_

---

## Milestone 1: Gemini Function Calling Infrastructure
- [ ] Extend `VertexAIClient` with function calling support
- [ ] Handle `FunctionCall` responses
- [ ] Support multi-turn tool use loop
- [ ] **Milestone complete:** Function calling works ✅

## Milestone 2: Case Tool Definitions
- [ ] Define all 13 tool schemas in `case_tools.py`
- [ ] Georgian + English descriptions for each tool
- [ ] Validate against Gemini `FunctionDeclaration` spec
- [ ] **Milestone complete:** All tools defined ✅

## Milestone 3: Backend Tool Execution
- [ ] Create `CaseToolExecutor` service
- [ ] Map tools to case file DB operations
- [ ] Add `case_agent` mode to chat router
- [ ] Handle tool call loop in router
- [ ] Return `pending_confirmation` for destructive actions
- [ ] Update `ChatSendResponse` with tool results
- [ ] **Milestone complete:** Backend executes tools ✅

## Milestone 4: Frontend Confirmation Flow
- [ ] Tool result display in chat bubbles
- [ ] Confirmation card UI with accept/reject buttons
- [ ] `confirmToolAction` / `rejectToolAction` in cubit
- [ ] Refresh `CaseDetailCubit` after execution
- [ ] **Milestone complete:** Full confirmation flow works ✅

## Milestone 5: Agent System Prompt
- [ ] Create `CASE_AGENT_SYSTEM` prompt
- [ ] Register in prompt registry
- [ ] Test natural tool usage in conversation
- [ ] **Milestone complete:** AI uses tools naturally ✅

## Milestone 6: Testing & Polish
- [ ] Integration tests for each tool
- [ ] Edge case testing (failures, timeouts, duplicates)
- [ ] Rate limit tool calls (max 5/message)
- [ ] Audit logging
- [ ] **Milestone complete:** Production ready ✅

---

## Blockers / Notes

_None yet._
