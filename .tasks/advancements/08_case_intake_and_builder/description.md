# Task: Case Intake & AI Case Builder

> **Covers:** Case intake interview (AI asks clarifying questions), AI-generated case file, case-aware standalone chat
> **Dependencies:** Task 01 (Chat & Retrieval), Task 03 (RAG & Guardrails)

---

## Purpose

The core "Cases = Projects" promise: a user describes their legal situation in natural language, the AI conducts an intake interview (asks what's missing), and when enough detail is gathered, generates a full structured case file — facts, applicable laws, defense strategies, prosecution counter-arguments, action checklist.

Additionally, the standalone Q&A chat needs the ability to attach an existing case for context-aware responses, turning the general chat into a case-specific legal assistant.

---

## Multi-Step Guide

### Milestone 1: Case Intake Prompt & Mode

1. Create `CASE_INTAKE_SYSTEM` prompt in `app/prompts/chat.py`:
   - Instructs AI to identify what the user HAS said vs what is MISSING
   - AI provides initial legal assessment + asks 2-3 follow-up questions
   - When all critical details gathered, AI outputs readiness signal: `✅ საკმარისი ინფორმაცია შევაგროვე`
2. Add `mode` field to `ChatSendRequest` schema (`chat` | `case_intake`)
3. Route to `CASE_INTAKE_SYSTEM` prompt when `mode == "case_intake"`
4. **Verify:** Case chat uses intake prompt, standalone chat uses default

### Milestone 2: Readiness Detection

1. Backend detects when AI signals readiness via:
   - Text signals: exact Georgian phrases in AI response
   - Heuristic fallback: 6+ messages, no questions in response
2. Return `case_analysis_ready: true` in `ChatSendResponse`
3. Frontend shows "Build Case" CTA button when `caseAnalysisReady == true`
4. **Verify:** After sufficient Q&A, Build Case button appears reliably

### Milestone 3: Flash → Pro Dual-Model RAG

1. `_expand_for_rag()` uses `gemini-3-flash-preview` (fast) to convert colloquial user text into proper legal search queries
2. Expanded queries fed to RAG pipeline for vector retrieval
3. `_generate_case_data()` uses `gemini-3.1-pro-preview` (strongest) for the actual case file generation
4. Both models configurable via `settings.gemini_chat_model` / `settings.gemini_model`
5. **Verify:** Backend logs show flash for expansion, pro for generation

### Milestone 4: Build Case File Endpoint

1. `POST /api/v1/case-files/build` endpoint:
   - Loads full conversation history
   - Runs flash expansion + RAG retrieval
   - Sends conversation + law context to Pro model with CASE_BUILDER prompt
   - Returns structured JSON (facts, evidence, laws, strategies, prosecution_args, action_checklist, lawyer_brief, citations)
2. Frontend `buildCaseFile()` in `ConsultationCubit` calls this endpoint
3. `populateFromAiAnalysis()` in `CaseDetailCubit` maps JSON → case data model
4. **Verify:** Tap Build Case → sections populate with AI-generated content

### Milestone 5: Chat Persistence in Case Workspace

1. `CaseChatSection` creates conversation on init, links to case via `linkedConversationIds`
2. On re-open, loads existing linked conversation instead of creating new
3. Fallback: if server-side conversation deleted, create fresh
4. **Verify:** Leave case → reopen → chat history preserved

### Milestone 6: Case Attachment in Standalone Chat

1. Add `attachedCaseId`, `attachedCaseTitle`, `attachedCaseContext` to `ConsultationState`
2. Provide `CasesCubit` on `/chat` route (MultiBlocProvider)
3. 📁 folder icon in input bar → opens case selector bottom sheet
4. Banner above input shows attached case name with ✕ detach button
5. `case_context` sent with each message → injected into AI prompt on backend
6. **Verify:** Attach case → ask question → AI references case facts/strategy

### Milestone 7: Auto-Generated Conversation Titles

1. On first user message, if conversation has no title, auto-generate from first 60 chars
2. Titles visible in conversation history list
3. **Verify:** New conversations show meaningful titles, not "New Conversation"
