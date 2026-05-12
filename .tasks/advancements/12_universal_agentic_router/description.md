# Universal Agentic Orchestrator & State Machine Workflows

## The Problem
The current application architecture relies on rigid, hardcoded routing. The frontend explicitly decides if a user is in "Chat Mode" or "Case Agent Mode". Prompts are massive, monolithic strings, and data extraction relies on the LLM "getting it right" on the first try without validation. The system lacks a unified brain that can smoothly transition a user from a casual question -> to deep intake -> to UI interaction -> to dangerous case modifications.

## The Solution: A Highly Orchestrated Agentic Graph
We will build a customized, maintainable **Agentic State Machine** (inspired by LangGraph and Semantic Kernel). 

Instead of a single endpoint guessing what to do, the system will operate as a flow of explicit **Nodes**. Information flows transparently:
1. **Global State**: A strictly typed `ConversationState` object holds everything the AI knows (history, extracted facts, active case ID, app UI state).
2. **The Supervisor**: A fast, cheap routing agent intercepts the message, looks at the `ConversationState`, and assigns the task to a specialized Sub-Agent.
3. **Structured & Auto-Healing Prompts**: Every Sub-Agent (Intake, Legal Scholar, Tool Manager) outputs **strict JSON**. If the LLM hallucinates a bad format, a validation loop catches it, appends the error to the prompt, and forces the LLM to fix its own mistake automatically.
4. **App Control & Dangerous Action Protocol (DAP)**: The Agent can emit UI components (e.g., showing a summary card in the chat). For destructive actions (deleting data, spending credits), the Agent's tool call triggers a DAP freeze. The State Machine saves its execution state to Redis, sends an Authorization payload to the user, and goes to sleep. When the user taps "Confirm", the machine wakes up and completes the tool call.

## Why This Matters
- **Maintainability**: Prompts become isolated, single-purpose classes. You can review and tweak the "Intake" logic without touching the "Case Modification" logic.
- **Resilience**: The auto-healing JSON loop guarantees the backend never crashes due to LLM hallucinations.
- **Unrestricted Power + Extreme Safety**: The AI is given the keys to the entire app, but the DAP strictly enforces human-in-the-loop verification for anything that causes permanent harm or spends money.

## Dependencies
- Tasks 01-11 complete.
- Knowledge of Pydantic for JSON validation.
- Redis for pausing/resuming state machine graphs.
