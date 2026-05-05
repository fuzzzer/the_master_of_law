# 🚀 Run Feature Generation — One-Touch Full Fillout

> **Copy-paste this entire document into a new AI session to implement the feature.**
> It contains full context, references to all existing code, and the implementation plan.

---

## 📌 Project Context

You are implementing a feature called **"One-Touch Full Fillout"** for **კანონის ოსტატი (The Master of Law)** — an AI-powered legal defense app for Georgian citizens.

### What the app does:
- Users create **cases** (legal defense projects)
- Each case has **8 sections**: Facts, Arguments, Evidence, Strategy, Timeline, Risks, Action Items, AI Chat
- Every legal claim must have **exact citation** to Georgian law (article number + matsne.gov.ge link)
- Backend uses **ChromaDB RAG** (9,450 Georgian law chunks) + **Gemini 3.1 Pro** for AI

### What this feature does:
Instead of manually filling 8 tabs, user answers 5-7 simple guided questions → AI generates the **complete defense case** with all sections filled, every claim cited.

---

## 📂 Critical Files to Read First

### Architecture & Specs
```
frontend/.plans/SPEC.md                           — Full product spec (544 lines)
frontend/.plans/one_touch_full_fillout/plan.md    — Feature plan with wizard steps, API design, case summary view
frontend/.plans/one_touch_full_fillout/research.md — Research questions & decisions
frontend/.plans/one_touch_full_fillout/ideas_and_simplifiers.md — UX ideas & priority matrix
```

### Frontend — Data Models
```
frontend/lib/src/features/cases/models/case_data.dart    — CaseData + all sub-models (FactData, ArgumentData, etc.)
frontend/lib/src/features/cases/models/enums.dart        — LegalDomain, CaseStatus, FactClassification, ArgumentStrength, etc.
```

### Frontend — Existing Case UI
```
frontend/lib/src/features/cases/view/pages/case_workspace_page.dart   — The 8-tab case workspace
frontend/lib/src/features/cases/view/components/case_overview_section.dart — Overview dashboard (where magic button goes)
frontend/lib/src/features/cases/view/components/case_chat_section.dart — AI chat (reference for citation chips)
```

### Frontend — Architecture
```
frontend/.agents/orchestrator.md                          — Flutter architecture guide
frontend/.agents/general_guide/flutter_architecture.md    — BLoC/Cubit patterns, feature-first structure
frontend/lib/src/features/consultation/bloc/consultation_cubit.dart — Example cubit pattern
frontend/lib/src/features/consultation/bloc/consultation_state.dart  — Example state pattern
```

### Backend — Case Builder (Extend This)
```
backend/app/services/case_builder_service.py     — Existing CaseBuilderService (add build_from_intake)
backend/app/prompts/case_builder.py              — Existing Gemini prompt template
backend/app/routes/case_file_router.py           — Existing case-file endpoints (add new endpoint)
backend/app/services/rag_service.py              — RAG pipeline (5-stage: expand→vector→fulltext→merge→rerank)
backend/app/schemas/case_file_schema.py          — Pydantic schemas for case files
```

### Backend — Infrastructure
```
backend/app/main.py                              — FastAPI app factory
backend/app/config/settings.py                   — Settings & environment config
backend/app/integrations/vertex_ai_client.py     — Gemini client wrapper
backend/app/integrations/chroma_client.py        — ChromaDB connection
```

---

## 🏗️ Implementation Order

### Step 1: Backend — New Intake Endpoint

**File:** `backend/app/routes/case_file_router.py`
**Action:** Add new endpoint

```python
@router.post("/generate-from-intake", response_model=CaseFileDetail, status_code=201)
async def generate_from_intake(body: IntakeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Generate complete case from intake wizard answers (costs 3 credits)."""
```

**File:** `backend/app/schemas/case_file_schema.py`
**Action:** Add IntakeRequest schema

```python
class IntakeRequest(BaseModel):
    case_id: str
    domain: str  # "civil", "criminal", "labor", etc.
    intake: IntakeData

class IntakeData(BaseModel):
    situation: str              # Free text: what happened
    date: str | None = None     # ISO date or approximate
    date_precision: str = "exact"  # exact | month | year | unknown
    opponent: OpponentData | None = None
    existing_evidence: list[str] = []
    desired_outcome: str = ""
    additional_info: str = ""
```

### Step 2: Backend — Intake Case Builder

**File:** `backend/app/services/case_builder_service.py`
**Action:** Add `build_from_intake()` method

Key logic:
1. AI extracts 3-5 legal keywords from `intake.situation`
2. Run RAG query for each keyword → collect 15-25 law chunks
3. Build prompt from intake + law chunks
4. Generate structured JSON via Gemini (all 8 sections)
5. Verify citations against ChromaDB
6. Return structured case data

### Step 3: Backend — Intake Prompt Template

**File:** `backend/app/prompts/intake_case_builder.py` (NEW)
**Action:** Create the Gemini prompt that converts intake answers → full case

The prompt must:
- Accept structured intake data + retrieved law chunks
- Output JSON with: facts[], arguments[], evidence{}, strategy{}, timeline[], risks[], action_items[], citations[]
- Every legal claim must reference a specific article from the provided law chunks
- Output must be in Georgian
- Include trust levels: verified (in corpus), interpretation, guidance

### Step 4: Frontend — Case Wizard Cubit

**File:** `frontend/lib/src/features/case_wizard/bloc/case_wizard_cubit.dart` (NEW)
**Action:** State management for the wizard flow

```dart
class CaseWizardCubit extends Cubit<CaseWizardState> {
  // Step navigation
  void nextStep();
  void previousStep();
  
  // Data updates (one per wizard step)
  void updateSituation(String text);
  void updateDate(DateTime? date, DatePrecision precision);
  void updateOpponent(OpponentType type, String description);
  void updateEvidence(List<String> existing);
  void updateDesiredOutcome(String outcome);
  void updateAdditionalInfo(String info);
  
  // Generation
  Future<void> generateCase();  // POST to backend
  
  // State
  // currentStep, intakeData, generationStatus, generatedCase, failureType
}
```

### Step 5: Frontend — Wizard UI Pages

**Files:** `frontend/lib/src/features/case_wizard/view/pages/` (NEW)

Create 7 wizard step pages:
1. `wizard_situation_step.dart` — Free text "რა მოხდა?"
2. `wizard_date_step.dart` — Date picker "როდის მოხდა?"
3. `wizard_opponent_step.dart` — Party type + name "ვინ არის მეორე მხარე?"
4. `wizard_evidence_step.dart` — Checklist "რა მტკიცებულება გაქვთ?"
5. `wizard_outcome_step.dart` — Choice chips "რა შედეგი გსურთ?"
6. `wizard_followup_step.dart` — AI follow-up questions (conditional)
7. `wizard_review_step.dart` — Summary + Generate button

All steps follow the pattern:
- Large Georgian text question at top
- Single input type (text/date/chips/checklist)
- "შემდეგი" (Next) button at bottom
- Progress bar at top
- Back arrow to previous step

### Step 6: Frontend — Case Summary View

**File:** `frontend/lib/src/features/case_wizard/view/pages/case_summary_page.dart` (NEW)

Single scrollable view showing all generated sections:
- Each section is a collapsible card
- Every legal claim has a tappable citation chip [§ მუხ. XXX]
- Citation chip opens bottom sheet with article text + matsne.gov.ge link
- Bottom bar: [✏️ Edit] [💬 AI Chat] [📤 Export] [🔄 Regenerate]
- "Edit" navigates to the existing CaseWorkspacePage with all data pre-filled

### Step 7: Frontend — Entry Point Integration

**Files to modify:**
- `case_overview_section.dart` — Add "🪄 AI-ით სრული შევსება" button
- `case_workspace_page.dart` — Handle navigation to wizard
- Router — Add wizard route: `/cases/:id/wizard`

### Step 8: Frontend — Hive Data Mapping

Map the backend response JSON to existing CaseData model:
- `response.facts[]` → `List<FactData>` with classification, links
- `response.arguments[]` → `List<ArgumentData>` with strength, article links
- `response.strategy` → `StrategyData` with primary/backup/fallback
- etc.

Save to Hive immediately after generation so it appears in the workspace.

---

## 🎨 Design Tokens (Use Existing)

```dart
// Colors (from ui_kit)
uiColors.backgroundPrimaryColor  // #0A1628 — deep navy
uiColors.backgroundSecondaryColor // #121E32 — card background
uiColors.accentColor             // #D4A84B — gold (wizard CTA buttons)
uiColors.successColor            // green (favorable facts)
uiColors.errorColor              // red (high risks, urgent deadlines)
uiColors.warningColor            // amber (medium risks)

// Text (from ui_kit)
uiTextStyles.headlineBold24      // Wizard question titles
uiTextStyles.headlineBold20      // Section headers
uiTextStyles.bodyBold14          // Card titles
uiTextStyles.body14              // Card content
uiTextStyles.caption11           // Metadata, timestamps
```

---

## ⚠️ Critical Rules

1. **Every legal claim MUST have a citation chip** — no uncited legal advice
2. **Georgian text everywhere** — all UI strings in Georgian (ქართული)
3. **Feature-first architecture** — new feature goes in `lib/src/features/case_wizard/`
4. **Cubit pattern** — no raw setState, no ChangeNotifier. Only Cubit + BlocBuilder
5. **No dart:io on web** — use `kIsWeb` guards or conditional imports
6. **Existing models** — map to CaseData, don't create parallel models
7. **Honest assessment** — show unfavorable facts and risks prominently
8. **Minimum touch targets** — 48×48dp
9. **Error states** — every network call needs loading/error/success states
10. **No placeholder text** — every string must be real Georgian text

---

## 🧪 Testing Scenario

Use this story to test the full flow:

```
სიტუაცია: "2025 წლის მარტში ბინის მეპატრონემ არ დამიბრუნა გირაო 
3000 ლარის ოდენობით. ხელშეკრულება წერილობითი იყო, 2 წლით ვიქირავებდი 
ბინას. ბინა კარგ მდგომარეობაში დავტოვე. მეპატრონე ამბობს რომ ბინა 
დაზიანებულია მაგრამ ეს სიმართლე არ არის."

მოსალოდნელი შედეგი:
- Domain auto-detected: სამოქალაქო (Civil)
- Facts: ~6 facts (4 favorable, 1 unfavorable, 1 neutral)
- Arguments: ~3 arguments citing სამოქალაქო კოდექსი
- Strategy: სარჩელი (primary), მედიაცია (backup)
- Risks: ხანდაზმულობა, მტკიცებულების ტვირთი
- Citations: მუხ. 316, 531, 627, 628 of სამოქალაქო კოდექსი
```

---

## ✅ Definition of Done

- [ ] User can start wizard from new case flow or existing empty case
- [ ] Wizard has 5-7 steps with Georgian text, back/next navigation
- [ ] Pressing "🪄 გენერაცია" calls backend and shows progressive loading
- [ ] Backend generates all 8 case sections using RAG + Gemini
- [ ] Every legal claim has a verifiable citation chip
- [ ] Case Summary View shows all sections with collapsible cards
- [ ] "Edit" navigates to existing case workspace with all data pre-filled
- [ ] Error states show Georgian error messages with retry
- [ ] Works on both web and mobile (kIsWeb guards where needed)
