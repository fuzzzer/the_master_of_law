# Task: Case Generation Flow — End-to-End

## Objective

Wire up the full case generation pipeline so the user can trigger case file creation from the consultation chat, see it build, and land on a populated case workspace.

---

## Current State

### Backend (DONE)
The three-stage pipeline is fully implemented:

1. **Intake** (`CASE_INTAKE_SYSTEM` in `backend/app/prompts/chat.py`) — AI asks questions, gives preliminary legal takes
2. **Full Analysis** (`CASE_FULL_ANALYSIS` in `backend/app/prompts/chat.py`) — one-shot comprehensive legal analysis from the fierce advocate prompt (the proven `LEGAL_ANALYSIS_SYSTEM`)
3. **JSON Builder** (`CASE_BUILDER` in `backend/app/prompts/case_builder.py`) — converts analysis into structured JSON

**Key backend files:**
- `backend/app/services/case_builder_service.py` — `build_case_file()` chains Stage 2 → Stage 3
- `backend/app/routes/case_file_router.py` — `POST /api/v1/case-files/build` endpoint (takes `conversation_id`)
- `backend/app/routes/chat_router.py` — detects `[CASE_READY]` tag, sets `case_ready` on conversation
- `backend/app/models/conversation.py` — has `case_ready` boolean column
- `backend/app/schemas/conversation_schema.py` — `ConversationDetail` returns `case_ready`

**Endpoint:** `POST /api/v1/case-files/build`
- Body: `{"conversation_id": "uuid-string"}`
- Returns: full `CaseFileDetail` JSON with all populated fields
- Costs 3 credits

### Frontend (PARTIALLY DONE)
- `ConsultationCubit` has `caseAnalysisReady` state and `buildCaseFile()` method
- `ConsultationState` has `caseAnalysisReady`, `isBuildingCase`, `caseFileData` fields
- `ConsultationRepository` and `ConsultationRemoteDataSource` have `buildCaseFile()` wired
- `loadConversation()` reads `case_ready` from backend response to restore state

### What's Missing (THIS TASK)
The UI has no button or mechanism for the user to trigger case generation.

---

## Requirements

### 1. "Build Case" Button in Chat UI

**Location:** In `consultation_page.dart`, add a persistent action button that appears when the user has enough conversation context. Two triggers:

- **Automatic:** `state.caseAnalysisReady == true` (AI detected [CASE_READY] or heuristic triggered)
- **Manual:** Always show a subtle "საქმის გენერაცია" option in the app bar or as a floating action so the user can trigger it whenever they feel ready, even if the AI hasn't flagged readiness yet

**UX Flow:**
1. User chats with AI, describes their legal situation
2. A "📋 საქმის გენერაცია" button becomes prominent (or is always available as a menu action)
3. User taps → confirmation dialog (this costs 3 credits)
4. Loading state with progress indicator ("საქმე მზადდება... ეს შეიძლება 30-60 წამი გაგრძელდეს")
5. On success → navigate to the case workspace page with the new case

**Design considerations:**
- When `caseAnalysisReady == true`: show a prominent animated banner/button above the input field
- When not ready but conversation has 2+ messages: show subtle icon in app bar
- During build: disable chat input, show loading overlay
- On error: show snackbar, re-enable chat

### 2. Navigation After Build

After `buildCaseFile()` returns data:
1. Create/update the case in the cases list
2. Navigate to `CaseWorkspacePage` with the case ID
3. The workspace should show all populated sections (facts, strategies, evidence, tasks, etc.)

**Check:** `frontend/lib/src/app/navigation/themasteroflaw_router.dart` for existing case workspace route.

### 3. Frontend Files to Modify

| File | What to do |
|------|-----------|
| `consultation_page.dart` | Add build button (banner + app bar action) |
| `consultation_cubit.dart` | `buildCaseFile()` already exists — just wire navigation |
| `consultation_state.dart` | Already has `isBuildingCase`, `caseFileData` — may need `buildError` |
| `case_workspace_page.dart` | Verify it renders all fields from `caseFileData` |
| `cases_cubit.dart` | May need refresh after new case is created |

### 4. Edge Cases
- User has no credits → show "insufficient credits" message (backend returns 402)
- Build fails → show error, allow retry
- User navigates away during build → handle gracefully
- Conversation has no messages → disable button
- `case_ready` persists across refreshes (backend already handles this)

---

## Key Code References

### ConsultationCubit.buildCaseFile (already implemented)
```dart
// frontend/lib/src/features/consultation/bloc/consultation_cubit.dart
Future<Map<String, dynamic>?> buildCaseFile() async {
  if (state.conversationId == null) return null;
  emit(state.copyWith(isBuildingCase: true));
  final result = await _repository.buildCaseFile(
    conversationId: state.conversationId!,
  );
  // ... handles success/failure
}
```

### Backend build endpoint
```python
# backend/app/routes/case_file_router.py
@router.post("/build", response_model=CaseFileDetail, status_code=201)
async def build_case_file(body: CaseFileBuildRequest, ...):
    # Checks credits (3 required)
    # Calls svc.build_case_file() which chains:
    #   1. CASE_FULL_ANALYSIS (rich legal text)
    #   2. CASE_BUILDER (structured JSON)
    # Deducts credits on success
```

### Case data structure (what the builder returns)
```json
{
  "title": "...",
  "facts": {"what_happened": "...", "when": "...", "where": "...", "who_involved": "...", "key_evidence": "..."},
  "evidence": {"has": [], "needs": [], "recommended_types": [], "deadlines": []},
  "applicable_laws": {"favorable": [], "against": [], "neutral": []},
  "defense_strategies": [{"name": "...", "success_likelihood": "...", "risk_level": "...", ...}],
  "prosecution_args": [{"argument": "...", "counter": "..."}],
  "action_checklist": [{"deadline": "...", "action": "...", "done": false}],
  "unclear_items": ["..."],
  "lawyer_brief": {"key_points": [], "questions_to_ask": [], "documents_to_bring": []},
  "citations": [{"code": "...", "article": "...", "text": "...", "url": "..."}]
}
```

---

## Verification

1. Start a conversation in case_intake mode
2. Describe a legal situation (e.g., "მეზობელმა მიწა წამართვა")
3. Chat 2-3 messages with the AI
4. Press "საქმის გენერაცია" button
5. Wait for build (30-60 seconds)
6. Verify navigation to case workspace
7. Verify all sections are populated (facts, strategies, evidence, tasks, citations)
8. Refresh the page — verify "Build Case" button state persists if case not yet built
9. Test insufficient credits (402) handling
