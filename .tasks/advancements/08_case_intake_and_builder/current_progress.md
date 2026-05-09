# Progress: Case Intake & AI Case Builder

> **Last updated:** 2026-05-09
> **Agent:** Antigravity

---

## Milestone 1: Case Intake Prompt & Mode
- [x] Create `CASE_INTAKE_SYSTEM` prompt
- [x] Add `mode` field to `ChatSendRequest` schema
- [x] Route to correct prompt based on mode
- **Milestone complete ✅**

## Milestone 2: Readiness Detection
- [x] Text signal detection (readiness phrases)
- [x] Heuristic fallback (6+ messages, no questions)
- [x] Return `case_analysis_ready` in response
- [x] Frontend shows Build Case CTA
- [ ] Validate detection is reliable across real conversations
- **Milestone in progress 🔄** — detection triggers exist but need validation

## Milestone 3: Flash → Pro Dual-Model RAG
- [x] `_expand_for_rag()` with flash model
- [x] `_generate_case_data()` with pro model
- [x] Model selection via `settings.gemini_chat_model` / `settings.gemini_model`
- **Milestone complete ✅**

## Milestone 4: Build Case File Endpoint
- [x] `POST /case-files/build` endpoint exists
- [x] `buildCaseFile()` in `ConsultationCubit`
- [x] `populateFromAiAnalysis()` in `CaseDetailCubit`
- [ ] End-to-end validation (button tap → sections populated)
- **Milestone in progress 🔄** — wired up, needs E2E test

## Milestone 5: Chat Persistence in Case Workspace
- [x] `CaseChatSection` creates/loads linked conversation
- [x] Fallback on deleted conversation
- [ ] Validate persistence across tab switches and reopens
- **Milestone in progress 🔄**

## Milestone 6: Case Attachment in Standalone Chat
- [x] State fields added (`attachedCaseId`, etc.)
- [x] `CasesCubit` provided on `/chat` route
- [x] 📁 folder icon + case selector bottom sheet
- [x] Banner with detach
- [x] `case_context` sent to backend
- [ ] Validate context injection works (AI references case data)
- **Milestone in progress 🔄**

## Milestone 7: Auto-Generated Conversation Titles
- [x] Auto-generate title from first user message (first 60 chars)
- [x] `update_title()` in ConversationService
- [ ] Validate titles show correctly in conversation history list
- **Milestone in progress 🔄**

---

## Blockers / Notes

- Readiness detection: AI doesn't always use the exact `✅ საკმარისი ინფორმაცია შევაგროვე` phrase. May need prompt tuning to make it more consistent.
- All milestones are code-complete but lack real-device validation.
