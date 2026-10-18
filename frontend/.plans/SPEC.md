# ბუნდოვანი კანონი — Fuzzzy Law
# Full Product Spec (v1.0)

> **This is the canonical spec. All implementation must follow this document.**
> Last updated: 2026-05-05

---

## What This App Is

A mobile app that helps Georgian citizens build the strongest possible legal defense.
Not a chatbot. Not a law encyclopedia. A **case workspace** where AI organizes everything
and every claim is backed by exact law — one tap away from the official source.

---

## Core Principles (Non-Negotiable)

### 1. Cases = Projects
The app revolves around cases. There is no standalone chat, no floating notes.
Everything lives inside a case. A case is a project folder for a legal problem.

### 2. Zero Hallucination
Every AI legal claim has a citation chip. Every chip opens the exact article text.
Every article has a "View on matsne.gov.ge" button. If AI can't cite it, it says so
and refers the user to the correct government office with a phone number.

### 3. Radical Simplicity
The user is stressed, non-legal, possibly in crisis. Every screen does ONE thing.
No jargon without explanation. No blank canvas — always guided. Large text, clear buttons.

### 4. Honest Assessment
The app shows unfavorable facts, risks, and weaknesses. Hiding bad news loses cases.
Trust comes from honesty, not optimism.

---

## Navigation: 3 Tabs

```
┌────────────────────────────────────┐
│                                    │
│         [Active Screen]            │
│                                    │
├──────────┬──────────┬──────────────┤
│ 📁 საქმე │ 📚 კანონ │ 👤 პროფილი  │
│  Cases   │  Laws    │  Profile     │
└──────────┴──────────┴──────────────┘
```

| Tab | Icon | Purpose |
|-----|------|---------|
| **Cases** ⭐ | `folder_special` | Home screen. All your cases. |
| **Laws** | `menu_book` | Browse/search Georgian legal codes. Free, always available. |
| **Profile** | `person` | Settings, language, plan, about. |

---

## User Journey (What They See)

### Screen 1: My Cases (Home)

**First time — empty state:**
```
        ⚖️

  თქვენ ჯერ არ გაქვთ საქმე
  You don't have any cases yet

  შექმენით პირველი საქმე და
  AI დაგეხმარებათ მის მოწყობაში

  [+ ახალი საქმის შექმნა]

  ან შეისწავლეთ კანონები →
```

**With cases:**
Each case card shows:
- Title (user-given name)
- Legal domain chip (Criminal, Civil, Labor, etc.)
- Status badge: Active 🟢 / Pending 🟡 / Closed ⚪
- Completeness percentage (progress bar)
- Last updated date
- FAB "+" to create new case

---

### Screen 2: New Case (Bottom Sheet → 2 taps)

Step 1: Name + Domain picker
```
┌─────────────────────────────────┐
│ ახალი საქმე                      │
│                                 │
│ სათაური:                        │
│ [მაგ: მემამულის დავა          ]  │
│                                 │
│ სფერო:                          │
│ [სამოქ.] [სისხ.] [ადმინ.]      │
│ [შრომ.] [საგად.] [ოჯახ.]       │
│ [საკუთრ.] [სხვა]               │
│                                 │
│     [შექმნა და დაწყება →]        │
└─────────────────────────────────┘
```

Step 2: Empty case opens → prominent CTA to start AI consultation

---

### Screen 3: Case Workspace (THE Core Screen)

When user taps a case, they enter the **Case Workspace**. This is a single screen
with horizontal scrollable tabs at the top:

```
┌─────────────────────────────────────┐
│ ← საქმეები    მემამულის დავა   [⋮]  │
│ 🟢 აქტიური │ ⚖️ სამოქალაქო        │
├─────────────────────────────────────┤
│ [📊 მიმოხ.][💬 AI][📋 ფაქტ.][⚖️ არგ]│
│ [📎 მტკიც.][🛡️ სტრატ][📅 ვადა][⚠️] │
├─────────────────────────────────────┤
│                                     │
│   [Content of selected tab]         │
│                                     │
└─────────────────────────────────────┘
```

**8 sub-tabs inside a case:**

| Tab | Georgian | What User Sees |
|-----|----------|----------------|
| **Overview** | მიმოხილვა | Bird's-eye dashboard. Summary cards for every section. Tap any card → goes to that tab. |
| **AI Chat** | AI კონსულტაცია | Chat with AI that knows ALL case context. Every response has citation chips. Quick-add buttons push insights into case sections. |
| **Facts** | ფაქტები | Three categories: ✅ Favorable, ❌ Unfavorable, ℹ️ Neutral. Each fact has source links. |
| **Arguments** | არგუმენტები | Legal arguments with linked law articles. Strength indicator: Strong/Moderate/Weak. |
| **Evidence** | მტკიცებულებები | Photos, documents, files. Each linked to facts and arguments. |
| **Strategy** | სტრატეგია | AI-generated defense plan. Primary + backup strategies. Editable. |
| **Timeline** | ვადები | Chronological events + deadlines with countdown. Urgency colors. |
| **Risks** | რისკები | Honest weak points + severity + mitigation suggestions. |

---

### Screen 3a: Overview Tab (Bird's-Eye)

The overview shows summary cards — user sees ENTIRE case at a glance:

```
  ████████░░ 72% complete

  ┌──────────┬──────────┐
  │ ✅ Facts 8│ ⚠️ Risk 3│
  ├──────────┼──────────┤
  │ ⚖️ Args 5 │ 📎 Evid 4│
  └──────────┴──────────┘

  🛡️ Defense Strategy (summary)
  📅 Next deadline: 3 days
  📋 Action items: 2 remaining
  🤖 Last AI chat: "მუხ. 316..."
```

Each card is tappable → navigates to that sub-tab.

---

### Screen 3b: AI Chat Tab (In-Case Consultation)

**What makes this different from a regular chatbot:**

1. **Context banner at top** — shows AI has full case context:
   ```
   📁 8 ფაქტი · 5 არგუმენტი · 4 დოკუმენტი
   ```

2. **AI messages have trust levels:**
   - 🟢 Green left border = verified citation (links to matsne.gov.ge)
   - 🟡 Amber left border = AI interpretation (clearly labeled)
   - 🔵 Blue left border = general guidance (not a legal claim)

3. **Citation chips in every legal claim:**
   ```
   [§ მუხ. 316 სამოქ. კოდ.]  ← tappable
   ```
   Tap → bottom sheet with full article → "View on matsne.gov.ge" button

4. **Verification badge on every AI message:**
   ```
   ✅ 3 ციტატა დადასტურებულია
   ```

5. **Quick-add buttons:**
   ```
   [+ ფაქტებში] [+ არგუმენტში]
   ```
   One tap to push AI insight into the case.

6. **Auto-classification:**
   AI recognizes new facts, evidence, deadlines in user's message and offers
   to add them to the appropriate case section.

---

### Screen 3c: Facts Tab

Three-column categorization with segment control:

```
[✅ ხელსაყრელი (5)] [❌ არახელს. (2)] [ℹ️ ნეიტრ. (1)]

✅ ხელშეკრულება წერილობითია
   წყარო: 📎 contract.pdf
   არგუმენტი: #2 ⚖️

✅ თანხა გადახდილია სრულად
   წყარო: 📎 receipt.jpg
   🤖 AI-ით ამოცნობილი

[+ დაამატეთ ფაქტი]
```

Each fact shows:
- Classification (favorable/unfavorable/neutral)
- Source (document, conversation, manual)
- Links to arguments and risks
- AI-extracted badge if auto-detected

---

### Screen 3d: Arguments Tab

```
⚖️ არგუმენტი #1                    💪 ძლიერი
   მემამულემ დაარღვია მუხ. 316
   [§ მუხ. 316 სამოქ. კოდ.]
   [§ მუხ. 405 სამოქ. კოდ.]
   📎 ხელშეკრულება, ქვითარი

⚖️ არგუმენტი #2                    ⚡ საშუალო
   ზეპირი შეთანხმებაც ძალაშია
   [§ მუხ. 316 §2 სამოქ. კოდ.]

[+ ახალი არგუმენტი]  ← guided builder, not blank text
```

**Argument creation is GUIDED** (not blank text field):
1. "What happened?" → free text
2. "Which law applies?" → AI suggests, user confirms
3. "What evidence supports this?" → link existing evidence
4. AI evaluates strength automatically

---

### Citation Chip → Bottom Sheet → matsne.gov.ge

This is the trust chain — identical everywhere in the app:

```
┌─────────────────────────────────────┐
│ § მუხლი 316 — სამოქალაქო კოდექსი   │
│                                     │
│ [Full article text from corpus]     │
│                                     │
│ 💡 რას ნიშნავს ეს:                  │
│ [Plain language explanation]        │
│                                     │
│ 🔗 [matsne.gov.ge-ზე ნახვა]        │  ← opens official source
│                                     │
│ [📁 საქმეში დამატება] [📋 კოპირება] │
└─────────────────────────────────────┘
```

---

### When AI Doesn't Know → Referral Card

```
┌─ ℹ️ ─────────────────────────────────┐
│ ეს საკითხი მოითხოვს დამატებით        │
│ ინფორმაციას.                          │
│                                      │
│ 🏛️ იუსტიციის სახლი                  │
│ 📞 2 72 55 99  [📞 ზარი]             │
│ 📍 სანაპიროს ქ. 2, თბილისი          │
│ 🕐 ორშ–პარ 09:00–18:00               │
│                                      │
│ 💬 რა ჰკითხოთ:                       │
│ "მინდა შევიტყო ჩემი საკუთრების       │
│  რეგისტრაციის სტატუსი..."            │
│ [📋 კოპირება]                        │
│                                      │
│ 🔍 [matsne.gov.ge-ზე ძიება]         │
└──────────────────────────────────────┘
```

---

### Laws Tab (Standalone — Tab 2)

Browse Georgian legal codes freely (no case required, no credits):

```
Laws Home → Category Grid (2 columns)
  ├── სისხლის სამართალი (Criminal) — red dot
  ├── სამოქალაქო (Civil) — blue dot
  ├── ადმინისტრაციული (Administrative) — green dot
  ├── შრომის (Labor) — orange dot
  ├── საგადასახადო (Tax) — purple dot
  ├── ოჯახის (Family) — pink dot
  └── საკუთრების (Property) — teal dot

Category → Code list → Article list → Article detail
```

**Article detail** includes:
- Full legal text with proper Georgian typography (1.6 line height)
- "💡 რას ნიშნავს" (What this means) plain-language box
- "📁 საქმეში დამატება" (Add to Case) button → pick which case
- "🔗 matsne.gov.ge" link
- Legal term tooltips on jargon words

---

### Profile Tab (Tab 3)

Simple settings:
- Account info + plan (FREE / PRO)
- Language toggle (🇬🇪 ქართული / 🇬🇧 English)
- Theme (dark default / light)
- Legal disclaimer
- About + version

---

## Court-Winning Features (Built Into Case Tabs)

These features live inside the relevant case tabs:

### In Overview Tab:
- **Case Strength Meter** — 0-100 score with breakdown (facts/evidence/legal basis/procedure)
- **Upcoming Deadlines** — countdown with urgency colors (🔴 < 7 days, 🟡 < 30, 🟢 > 30)
- **Action Items** — prioritized checklist

### In Arguments Tab:
- **Counter-Argument Preparation** — "What the other side will say" with your prepared response + citations
- **Argument Strength Indicator** — Strong / Moderate / Weak with reason

### In Facts Tab:
- **Burden of Proof Tracker** — What YOU must prove (with evidence status) vs what OPPONENT must prove

### In Evidence Tab:
- **Admissibility Check** — AI evaluates if evidence is legally admissible + suggestions to strengthen it

### In Timeline Tab:
- **Statute of Limitations Warning** — Auto-calculated countdown
- **Procedural Compliance Checklist** — Filing deadlines, court fees, document requirements

### In Risks Tab:
- **Red Team Mode** — AI argues AGAINST user to find weaknesses

### In Strategy Tab:
- **Primary + Backup + Fallback** strategies with confidence ratings

### Export (from Overview):
- **Case Export** — generates professional PDF/text summary for handing to a real lawyer
- All citations become clickable matsne.gov.ge links in the export

---

## Visual Design Summary

### Colors (Dark Mode = Default)
- **Background:** Deep navy (#0A1628), never pure black
- **Surface/Cards:** Slightly lighter navy (#121E32)
- **Accent:** Warm gold/amber (#D4A84B) — Georgian cultural pride
- **Text Primary:** Off-white (#F0EDE8)
- **Text Secondary:** Muted (#8B95A5)
- **Semantic:** Success green, Warning amber, Error red, Info blue
- **Trust levels:** Green (verified), Amber (interpretation), Blue (guidance)

### Typography
- **Georgian:** Noto Sans Georgian — ALL Georgian UI text
- **Latin:** Inter — English text and UI labels
- **Legal references:** JetBrains Mono — article numbers, citations
- **Line height:** 1.5–1.6 for legal text readability

### Key Rules
- 48×48dp minimum touch targets
- 4.5:1 contrast ratio (WCAG AA)
- No gradients on cards/buttons
- Accent color max 2 elements per screen
- Legal term tooltips on all jargon (ℹ️ icon)

---

## Technical Architecture

### Features Directory Structure
```
lib/src/features/
├── cases/
│   ├── models/          (CaseData, FactData, ArgumentData, etc.)
│   ├── data/
│   │   ├── data_sources/
│   │   └── repositories/
│   ├── bloc/            (CasesCubit, CaseDetailCubit)
│   └── view/
│       ├── pages/       (MyCasesPage, CaseWorkspacePage)
│       └── components/  (CaseCard, FactCard, ArgumentCard, etc.)
├── consultation/
│   ├── models/
│   ├── data/
│   ├── bloc/
│   └── view/            (ChatPage, ChatBubble, CitationChip, etc.)
├── laws/
│   ├── models/
│   ├── data/
│   ├── bloc/
│   └── view/            (LawsHomePage, ArticleDetailPage, etc.)
└── profile/
    └── view/            (ProfilePage, SettingsPage)
```

### Routes (GoRouter)
```
/                          → redirect to /cases
/cases                     → MyCasesPage (Tab 1)
/cases/new                 → New Case bottom sheet
/cases/:id                 → CaseWorkspacePage (default: overview)
/cases/:id/overview        → Overview sub-tab
/cases/:id/chat            → AI Consultation sub-tab
/cases/:id/facts           → Facts sub-tab
/cases/:id/arguments       → Arguments sub-tab
/cases/:id/evidence        → Evidence sub-tab
/cases/:id/strategy        → Strategy sub-tab
/cases/:id/timeline        → Timeline sub-tab
/cases/:id/risks           → Risks sub-tab
/laws                      → LawsHomePage (Tab 2)
/laws/:codeId              → Code structure
/laws/:codeId/:articleId   → Article detail
/profile                   → ProfilePage (Tab 3)
```

### Data Flow
```
User creates case → local storage (Hive)
User starts AI chat → POST /api/v1/chat/{id}/send (1 credit)
  → Backend: case context injected into prompt
  → Backend: RAG pipeline finds relevant laws
  → Backend: Gemini generates response with citations
  → Backend: Citation verification against corpus
  → Response: text + citations with article_url (matsne.gov.ge links)
User taps citation → Bottom sheet (article from corpus)
User taps "matsne.gov.ge" → url_launcher opens official source
User taps "+ Add to Facts" → local storage update
```

---

## Implementation Phases

### Phase 1 — App Shell (Build First)
1. ✅ UI Kit: colors, typography, theme (Noto Sans Georgian + Inter)
2. ✅ 3-tab bottom navigation with GoRouter
3. ✅ Cases list (local, Hive) with empty state
4. ✅ Case workspace with 8 sub-tabs (placeholder content)
5. ✅ New case creation (name + domain)
6. ✅ Profile page (language toggle, dark/light theme)

### Phase 2 — Case Content (Build Second)
1. Facts CRUD (add/edit/delete/categorize)
2. Arguments CRUD with guided builder
3. Evidence attach (photos/files)
4. Timeline with deadlines
5. Risks section
6. Strategy section
7. Overview dashboard with summary cards + strength meter
8. Case export (text/clipboard)

### Phase 3 — AI Integration (Build Third)
1. Connect to backend API (auth + chat endpoints)
2. AI chat with case context injection
3. Citation chips with matsne.gov.ge deep links
4. Trust level badges (verified/interpretation/guidance)
5. Quick-add buttons (chat → case sections)
6. Referral cards when AI doesn't know
7. Auto-classification of new facts from chat

### Phase 4 — Laws Browser
1. Connect to /api/v1/laws/* endpoints
2. Category grid → code list → article detail
3. "Add to Case" from article detail
4. Search functionality
5. Plain-language explanations
6. Legal term tooltips

### Phase 5 — Court-Winning Features
1. Burden of proof tracker
2. Counter-argument preparation
3. Procedural compliance checklist
4. Evidence admissibility check
5. Case strength meter
6. Statute of limitations warnings
7. Trial preparation checklist
8. Red Team mode

---

## Georgian Legal Institution Directory

Built into the app for referrals when AI lacks information:

| Institution | Phone | Website | Handles |
|-------------|-------|---------|---------|
| იუსტიციის სახლი | 2 72 55 99 | my.gov.ge | Property, civil registry, notary |
| სახალხო დამცველი | 2 39 14 21 | ombudsman.ge | Human rights violations |
| იურიდიული დახმარების სამსახური | 2 92 12 92 | legalaid.ge | Free legal aid |
| შრომის ინსპექცია | 2 15 16 00 | lio.gov.ge | Labor disputes |
| სასამართლოს ადმინისტრატორი | 2 51 87 00 | court.ge | Court schedules, filing |
| პროკურატურა | 2 40 52 22 | pog.gov.ge | Criminal case status |
| საგადასახადო | 2 26 11 45 | rs.ge | Tax disputes |
| მომხმარებლის დაცვა | 2 33 10 10 | competition.ge | Consumer protection |
| ეროვნული ბანკი | 2 40 61 98 | nbg.gov.ge | Banking/financial disputes |

---

## The Push-Back Rule

Any implementation decision that reduces **clarity, win probability, or accessibility**
must be rejected and replaced. Specifically:

- ❌ Never show AI text without trust level indicator
- ❌ Never say "consult a lawyer" without also showing free alternatives + contacts
- ❌ Never show raw legal text without plain-language summary
- ❌ Never let user write legal arguments from scratch — always guide
- ❌ Never hide unfavorable facts or risks
- ❌ Never let a deadline be buried in a sub-screen — deadlines on overview + notifications
- ✅ Always show citation source chain (AI claim → article text → matsne.gov.ge)
- ✅ Always categorize facts honestly (favorable/unfavorable/neutral)
- ✅ Always show what evidence is still missing
- ✅ Always provide the next recommended action
