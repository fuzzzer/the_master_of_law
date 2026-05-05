# 🪄 One-Touch Full Fillout — Feature Plan

> **Goal:** User taps one button, answers 5-7 guided questions → AI generates a complete defense case with every section filled, every claim backed by exact law citations.

---

## Why This Feature

The average Georgian citizen facing a legal problem is **stressed, confused, and non-legal**. They don't know what "facts" vs "arguments" vs "strategy" means. Asking them to manually fill 8 tabs is overwhelming.

**One Touch** solves this: dump your raw situation → get a professionally structured defense.

---

## The Flow (3 Phases)

### Phase 1: Guided Intake Wizard (5-7 steps)
### Phase 2: AI Generation (backend processing)
### Phase 3: Case Summary View (review + edit)

---

## Phase 1 — Guided Intake Wizard

A bottom-sheet or full-screen wizard. Each step is ONE question, large text, big input.

### Step 1: რა მოხდა? (What happened?)
- **Type:** Free text with voice-to-text option
- **Placeholder:** "აღწერეთ სიტუაცია თქვენი სიტყვებით..."
- **AI suggestion chip:** "მაგ: მემამულე არ მიბრუნებს ბინის გირაოს"
- **Min length:** 30 chars before "Next" activates

### Step 2: როდის მოხდა? (When did it happen?)
- **Type:** Date picker + "approximate" toggle
- **Subtext:** "ეს მნიშვნელოვანია ხანდაზმულობის ვადის დასათვლელად"
- **Options:** Exact date / Month+Year / Year only / "არ ვიცი"

### Step 3: ვინ არის მეორე მხარე? (Who is the other party?)
- **Type:** Text + role chips
- **Chips:** დამსაქმებელი (Employer) | მეზობელი (Neighbor) | სახელმწიფო (State) | კომპანია (Company) | ფიზიკური პირი (Individual) | სხვა
- **Text field:** Name/description

### Step 4: რა მტკიცებულება გაქვთ? (What evidence do you have?)
- **Type:** Checklist with AI-suggested items based on Step 1
- **Static options:** ხელშეკრულება (Contract) | მიმოწერა (Correspondence) | ფოტო/ვიდეო | ქვითარი (Receipt) | მოწმეები (Witnesses) | სხვა
- **AI-dynamic:** Based on what they described, suggest relevant evidence types

### Step 5: რა შედეგი გსურთ? (What outcome do you want?)
- **Type:** Choice chips + optional free text
- **Chips:** კომპენსაცია (Compensation) | ხელშეკრულების შესრულება (Contract enforcement) | დანაშაულის დადგენა (Criminal liability) | უფლების აღდგენა (Right restoration) | სხვა

### Step 6 (conditional): დამატებითი ინფორმაცია (Additional info)
- **Type:** AI asks 1-2 follow-up questions based on previous answers
- **Example:** "თქვენ ხელშეკრულებას ახსენეთ — წერილობითი იყო თუ ზეპირი?"
- **This step may be skipped or generate multiple sub-steps**

### Step 7: შეჯამება (Review before generation)
- **Type:** Read-only summary of all answers
- **CTA:** "🪄 საქმის გენერაცია" (Generate Case) — big gold button
- **Subtext:** "AI შეავსებს ყველა სექციას კანონის ზუსტი მითითებით"

---

## Phase 2 — AI Generation

### What happens when they press 🪄:

1. **Frontend** packages all wizard answers into a structured JSON
2. **POST** to new endpoint `/api/v1/case-files/generate-from-intake`
3. **Backend** does:
   a. Expand the intake answers into a detailed context prompt
   b. RAG pipeline: query ChromaDB with the situation + desired outcome
   c. Retrieve 15-25 relevant law chunks
   d. Send to Gemini with the INTAKE_CASE_BUILDER prompt
   e. Gemini generates ALL 8 sections as structured JSON
   f. Persist to DB + return
4. **Frontend** receives structured case data
5. **Frontend** populates ALL local Hive case sections in one shot
6. **Navigate** to Case Summary View

### Sections Generated:

| Section | What AI Fills | Source |
|---------|---------------|--------|
| **Facts** | 5-15 facts categorized (favorable/unfavorable/neutral) | User's description + AI analysis |
| **Arguments** | 3-7 legal arguments with strength ratings | RAG law corpus + situation |
| **Evidence** | What they have + what they need | User's checklist + legal requirements |
| **Strategy** | Primary + backup + fallback | AI analysis of strongest legal approach |
| **Timeline** | Key dates + procedural deadlines | User's dates + statute of limitations |
| **Risks** | 2-5 honest risk assessments + mitigations | AI adversarial analysis |
| **Action Items** | 5-10 prioritized next steps | Strategy + deadlines + evidence gaps |
| **Law Citations** | Every relevant article with matsne.gov.ge links | ChromaDB RAG results |

---

## Phase 3 — Case Summary View

A **single scrollable view** that shows the entire generated case at a glance.

### Layout (top to bottom):

```
┌──────────────────────────────────────┐
│  🪄 საქმე გენერირებულია AI-ით        │
│     "ბინის გირაოს დაბრუნება"          │
│     ⚖️ სამოქალაქო · 🟢 აქტიური      │
│                                      │
│  ████████████░░ 85% სიძლიერე         │
├──────────────────────────────────────┤
│                                      │
│  📋 ფაქტები (8)                      │
│  ┌ ✅ ხელშეკრულება წერილობითია       │
│  │   [§ მუხ. 316 სამოქ. კოდ.]       │
│  ├ ✅ გირაო 3000₾ გადახდილია         │
│  │   [§ მუხ. 627 სამოქ. კოდ.]       │
│  ├ ❌ 6 თვეზე მეტი გავიდა           │
│  │   ⚠️ ხანდაზმულობა                 │
│  └ ℹ️ ბინა 2 წელი დაიქირავა         │
│                                      │
│  ⚖️ არგუმენტები (4)                  │
│  ┌ 💪 ძლიერი: მუხ. 316-ის დარღვევა  │
│  │   [§ მუხ. 316] [§ მუხ. 405]      │
│  ├ ⚡ საშუალო: ზეპირი შეთანხმება     │
│  │   [§ მუხ. 316 §2]                │
│  └ ⚡ საშუალო: ბინის ზიანი           │
│     [§ მუხ. 408]                     │
│                                      │
│  🛡️ სტრატეგია                       │
│  ┌ 🟢 ძირითადი: სასამართლო სარჩელი  │
│  ├ 🟡 სარეზერვო: მედიაცია           │
│  └ ⚪ საბოლოო: ნაწილობრივი შეთანხმ.  │
│                                      │
│  ⚠️ რისკები (3)                      │
│  ┌ 🔴 მაღალი: ხანდაზმულობის ვადა    │
│  │   💡 დაუყოვნებლივ შეიტანეთ       │
│  ├ 🟡 საშუალო: მოწმის არყოფნა       │
│  └ 🟢 დაბალი: საბუთების ფორმა       │
│                                      │
│  📅 ვადები                           │
│  ┌ 🔴 3 დღე: სარჩელის ვადა!         │
│  └ 🟡 30 დღე: მტკიცებულების წარდგენა│
│                                      │
│  📋 სამოქმედო გეგმა                  │
│  □ ადვოკატთან კონსულტაცია            │
│  □ ხელშეკრულების ასლის მოპოვება      │
│  □ მოწმეების გამოკითხვა              │
│                                      │
│  ────────────────────────────────────│
│  [✏️ რედაქტირება]  [💬 AI კონსულტაცია]│
│  [📤 ექსპორტი]    [🔄 ხელახლა]       │
└──────────────────────────────────────┘
```

### Key UX Details:

1. **Every legal claim has a citation chip** — tappable → article bottom sheet → matsne.gov.ge
2. **Sections are collapsible** — tap header to expand/collapse
3. **Inline edit** — tap any item to edit in place
4. **Trust indicators** — 🟢 verified / 🟡 interpretation / 🔵 guidance on each AI claim
5. **"Edit" button** opens the regular 8-tab case workspace with all data pre-filled
6. **"AI კონსულტაცია"** starts a conversation with the full case context already loaded
7. **"ხელახლა"** re-runs the wizard with saved answers

---

## Entry Points

### 1. New Case Flow (Primary)
```
My Cases → [+ ახალი საქმე] → Name + Domain →
  "როგორ გსურთ შევსება?"
  [🪄 AI-ით ავტომატურად]  ← THIS FEATURE
  [✍️ ხელით შევსება]
```

### 2. Existing Empty Case (Secondary)
```
Case Workspace → Overview tab (empty) →
  Big centered CTA:
  "🪄 AI-ით საქმის სრული შევსება"
```

### 3. Partially Filled Case (Tertiary)
```
Case Workspace → [⋮] menu →
  "🪄 AI-ით დანარჩენის შევსება"
  → Only generates missing sections, preserves user's existing data
```

---

## Credit Cost

- **Full generation:** 3 credits (same as case-file build)
- **Partial regeneration:** 1 credit
- **Follow-up AI questions:** 0 credits (part of wizard flow)

---

## Backend Changes Required

### New Endpoint
```
POST /api/v1/case-files/generate-from-intake
```

### Request Body
```json
{
  "case_id": "local-case-uuid",
  "domain": "civil",
  "intake": {
    "situation": "მემამულე არ მიბრუნებს გირაოს...",
    "date": "2025-06-15",
    "date_precision": "exact",
    "opponent": {
      "type": "individual",
      "description": "მემამულე გიორგი"
    },
    "existing_evidence": ["contract", "receipt", "correspondence"],
    "desired_outcome": "compensation",
    "additional_info": "ხელშეკრულება წერილობითი იყო, 2 წლიანი ვადით"
  }
}
```

### Response Body
```json
{
  "case_file_id": "uuid",
  "title": "ბინის გირაოს დაბრუნების საქმე",
  "facts": [...],
  "arguments": [...],
  "evidence": { "has": [...], "needs": [...] },
  "strategy": { "primary": {...}, "backup": {...}, "fallback": {...} },
  "timeline": [...],
  "risks": [...],
  "action_items": [...],
  "citations": [
    {
      "article_id": "316",
      "code_title": "სამოქალაქო კოდექსი",
      "article_title": "ხელშეკრულების ცნება",
      "snippet": "ხელშეკრულება არის...",
      "article_url": "https://matsne.gov.ge/...",
      "trust_level": "verified"
    }
  ]
}
```

---

## Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| ChromaDB corpus (9,450 chunks) | ✅ Ready | RAG source for law articles |
| CaseBuilderService | ✅ Exists | Needs new `build_from_intake()` method |
| CASE_BUILDER prompt | ✅ Exists | Needs INTAKE_CASE_BUILDER variant |
| CaseData Hive model | ✅ Exists | All 8 sections defined |
| Gemini 3.1 Pro | ✅ Connected | JSON output mode available |
| Case workspace tabs | ✅ Built | Pre-filled from generated data |

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Gemini hallucinating law articles | 🔴 High | All citations verified against corpus; unverified = 🟡 warning |
| Generation takes >30s | 🟡 Medium | Stream progress: "ფაქტების ანალიზი... არგუმენტების შედგენა..." |
| User answers too vague | 🟡 Medium | AI follow-up questions in Step 6; minimum length validation |
| Wrong legal domain auto-detected | 🟢 Low | User picks domain in Step 1; AI validates but doesn't override |
| Generated content overwhelms user | 🟡 Medium | Summary view with collapsible sections; clear "next step" highlight |

---

## Success Metrics

1. **Completion rate:** >80% of users who start the wizard finish it
2. **Time to first complete case:** <5 minutes (vs ~30 min manual)
3. **Citation accuracy:** >95% of cited articles exist in corpus
4. **User edit rate:** Track which sections users edit most → improve prompts
