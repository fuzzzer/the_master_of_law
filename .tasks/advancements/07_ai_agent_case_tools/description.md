# Task: AI Agent Case Tools

> **Covers:** AI-powered case modification via chat (function calling)
> **Dependencies:** Task 04 (Feedback & QA), Case Chat Intake (current session work), Gemini function calling support

---

## Purpose

Transform the AI chat from a passive Q&A into an active case management agent. When a user has a case attached (or is in case workspace chat), the AI can directly modify case data — add facts, link law articles, set strategy, create action items — all through natural conversation.

This is the final evolution of the "Cases = Projects" philosophy: the AI doesn't just analyze, it **acts**.

---

## Multi-Step Guide

### Milestone 1: Gemini Function Calling Infrastructure
1. Extend `VertexAIClient` with function calling support:
   - Add `tools` parameter to `generate()` and `generate_json()`
   - Support `FunctionDeclaration` definitions
   - Handle `FunctionCall` responses from Gemini
   - Handle multi-turn tool use (Gemini responds → tool call → execute → send result back)
2. Create `app/tools/case_tools.py` — define all tool schemas as Gemini `FunctionDeclaration` objects
3. **Verify:** Client can send tools to Gemini and receive `FunctionCall` responses

### Milestone 2: Case Tool Definitions
1. Define tool schemas in `case_tools.py`:
   - `add_fact(text, classification)` — add a fact to the case
   - `edit_fact(fact_id, text, classification)` — modify existing fact
   - `delete_fact(fact_id)` — remove a fact (requires confirmation)
   - `add_argument(title, explanation, strength)` — add argument
   - `delete_argument(argument_id)` — remove argument (requires confirmation)
   - `link_article(code_name, article_number, snippet)` — link a law article
   - `unlink_article(article_id)` — remove linked article (requires confirmation)
   - `set_strategy(primary, backup, confidence)` — set case strategy
   - `add_action_item(task, priority, deadline)` — add checklist item
   - `complete_action_item(item_id)` — mark item done
   - `delete_action_item(item_id)` — remove item (requires confirmation)
   - `add_risk(description, severity, mitigation)` — add risk assessment
   - `get_case_summary()` — read full case context (no modification)
2. Each tool has a clear description in Georgian + English for Gemini
3. **Verify:** All tool schemas validate against Gemini's `FunctionDeclaration` spec

### Milestone 3: Backend Tool Execution
1. Create `app/services/case_tool_executor.py`:
   - Receives tool name + arguments from Gemini response
   - Maps to case file operations (CaseFileRepository / direct DB)
   - Returns execution result (success/failure + details)
   - Marks destructive actions with `requires_confirmation: true`
2. Update `chat_router.py`:
   - New mode: `case_agent` (alongside `chat` and `case_intake`)
   - When mode is `case_agent`, include tools in Gemini call
   - Handle tool call loop: Gemini → tool call → execute → return result → Gemini continues
   - For destructive actions: don't execute, return `pending_confirmation` to frontend
3. Update `ChatSendResponse` with tool execution results
4. **Verify:** Backend can execute non-destructive tools and return results

### Milestone 4: Frontend Confirmation Flow
1. Add tool result display in chat bubbles:
   - Success: "✅ ფაქტი დამატებულია: [text]"
   - Pending confirmation: Show confirmation card with [✅ დიახ] [❌ არა] buttons
2. Add `confirmToolAction` / `rejectToolAction` methods to `ConsultationCubit`
3. When user confirms → send confirmation to backend → execute → show result
4. When user rejects → send rejection → AI acknowledges
5. After any tool execution → refresh `CaseDetailCubit` state
6. **Verify:** Full flow works — AI suggests deletion → user confirms → item removed → UI updates

### Milestone 5: Agent System Prompt
1. Create `CASE_AGENT_SYSTEM` prompt in `app/prompts/chat.py`:
   - Instructs AI to use tools when appropriate
   - Never modify without clear user intent
   - Always explain what it's doing and why
   - Ask before destructive actions
   - Provide case summary on request
2. Register in prompt registry
3. **Verify:** AI naturally uses tools during conversation when relevant

### Milestone 6: Testing & Polish
1. Write integration tests for each tool
2. Test edge cases: tool fails, network drops mid-confirmation, duplicate actions
3. Rate limit tool calls (max 5 per message)
4. Add tool usage to credit system if needed
5. **Verify:** All tools work reliably, no data corruption possible
