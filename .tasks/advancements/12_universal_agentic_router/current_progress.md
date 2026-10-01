# 12: Universal Agentic Orchestrator & State Machine Workflows

**Status**: 🔴 Not Started
**Last Updated**: 2026-05-12

## Milestone 1: The Core State Machine & Auto-Healing Engine 🔴
- [ ] Define the global `ConversationState` Pydantic model (tracks case_id, extracted_facts, chat_history, active_workflow, pending_authorizations).
- [ ] Implement `StructuredPromptNode`: A class that wraps Gemini calls, enforces a Pydantic schema for the response, and implements an automatic 3-retry self-healing loop for `json.JSONDecodeError` or `ValidationError`.
- [ ] Implement the `WorkflowOrchestrator`: A lightweight runner that manages the transition between nodes (e.g., from `SupervisorNode` -> `IntakeNode` -> `ToolExecutionNode`).

---
🛑 **Milestone 1 Gate: A simple structured prompt can be executed, and intentionally corrupted JSON is auto-repaired by the LLM without throwing 500 errors.**

## Milestone 2: The Supervisor Agent & Routing 🔴
- [ ] Build the `SupervisorPrompt`: A highly optimized, fast (Gemini Flash) node that intercepts every incoming user message.
- [ ] Supervisor outputs a strict JSON decision: `{"intent": "...", "target_workflow": "intake | tool_action | legal_qa", "confidence": 0.99}`.
- [ ] Update `ws_chat_router.py` to route all incoming messages through the Orchestrator, completely removing hardcoded modes from the frontend.

---
🛑 **Milestone 2 Gate: User messages dynamically trigger different workflows based solely on intent, verified via backend logs.**

## Milestone 3: The Universal Advocate & App Control 🔴
- [ ] Refactor `CASE_TOOLS` to include UI-control tools: `render_ui_component(component: str, data: dict)` allowing the AI to pop up checklists, summaries, or forms in the chat.
- [ ] Formalize the Dangerous Action Protocol (DAP):
  - Mark `delete_case`, `delete_user_data`, `submit_official_doc` as `requires_user_auth: true`.
  - When the AI attempts a DAP tool, the Orchestrator pauses, stores state in Redis, and emits a structured `AUTH_REQUIRED` payload to Flutter.
  - Create the `/resume_workflow` endpoint to continue execution once the user taps "Confirm" in the UI.
- [ ] Give the Advocate Agent full, unrestricted access to all non-DAP tools (add_fact, update_strategy) within the main conversation loop.

---
🛑 **Milestone 3 Gate: AI can freely build a case, but physically cannot delete it without a UI confirmation pausing and resuming the state machine.**

## Milestone 4: Migration & Cleanup 🔴
- [ ] Migrate the massive `CASE_INTAKE_SYSTEM` and `case_full_analysis` prompts into the new `PromptNode` architecture.
- [ ] Ensure all prompts are isolated in maintainable, easily reviewable files.
- [ ] Verify full backward compatibility with existing Firebase conversations.

---
🛑 **Milestone 4 Gate: System is production-ready, fully orchestrated, and the legacy routers are safely deprecated.**
