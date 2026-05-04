# კანონის ოსტატი — Feature Roadmap & Product Vision

## Core Vision

> **Cases are Projects.** The app is case-centric. Every feature, every screen, every AI interaction
> exists to serve one purpose: building the strongest possible legal case for the user.

Users don't come to this app to "chat with AI" or "browse laws" — they come because
they have a **legal problem** and need to **organize, understand, and act on it**. The case
is the central organizing unit. Everything connects to a case.

---

## Current State (as of Sprint 1)

### Completed
- ✅ Law corpus scraped, structured, and stored (MongoDB)
- ✅ Backend API architecture defined (FastAPI)
- ✅ Design system created and integrated with open-design
- ✅ Flutter app skeleton to be renamed and configured (`master_of_law` / `ge.fuzzycore.masteroflaw`)
- ✅ UI Kit package ready for design token injection
- ✅ Comprehensive DESIGN.md with full case-centric specification

### Massive UX Improvements Needed
The current design is a starting point. Before shipping, we need:
1. **User research** — interview Georgian citizens who've had legal problems
2. **Information architecture review** — ensure the case dashboard doesn't overwhelm
3. **Progressive disclosure** — simple first, complexity on demand
4. **Georgian typography testing** — ensure Noto Sans Georgian renders beautifully at all sizes
5. **Accessibility audit** — screen reader, font scaling, color contrast
6. **Legal domain expertise** — consult real Georgian lawyers for workflow validation

---

## Primary User Needs

### Target User: Georgian citizen facing a legal problem

| Priority | Need | App Solution |
|---|---|---|
| 1 | **"What are my rights?"** | AI chat + law browser with plain-language explanations |
| 2 | **"Help me organize this mess"** | Case Builder — dump documents, AI structures them |
| 3 | **"What arguments can I make?"** | Legal Arguments section with law article linking |
| 4 | **"What could go wrong?"** | Risks & Weaknesses — honest AI assessment |
| 5 | **"What should I do next?"** | Action Plan with deadlines, priority-sorted |
| 6 | **"How do I explain this to a lawyer?"** | Case Export — professional summary PDF |

### Key Insight
Users don't know what they need until they start exploring. The app must:
- Start with a **simple question** ("What's your situation?")
- Progressively build complexity as the case develops
- Never require the user to be a legal expert
- Always show the user **what to do next**

---

## Feature Phases

### Phase 1 — MVP Foundation

**Goal:** Working app with basic AI consultation and law browsing

| Feature | Priority | Status |
|---|---|---|
| Design system → Flutter ui_kit | P0 | 🔄 In Progress |
| 5-tab navigation (Chat, Cases, Laws, Notes, Profile) | P0 | ⬜ |
| Basic AI chat (send message → get legal analysis) | P0 | ⬜ |
| Law browser (categories → codes → articles) | P0 | ⬜ |
| Full-text law search | P0 | ⬜ |
| Basic case creation (title + domain + status) | P1 | ⬜ |
| Notes (save any content, filter by type) | P1 | ⬜ |
| Onboarding (3-page intro) | P2 | ⬜ |
| Splash screen | P2 | ⬜ |
| Local storage (Hive) | P0 | ⬜ |
| Profile & settings | P2 | ⬜ |

### Phase 2 — Case Builder Core

**Goal:** The case dashboard becomes the app's command center

| Feature | Priority | Status |
|---|---|---|
| Case Dashboard with collapsible sections | P0 | ⬜ |
| Facts: favorable / unfavorable / neutral categorization | P0 | ⬜ |
| Legal Arguments: numbered cards with law article links | P0 | ⬜ |
| Applicable Laws: auto-linked from AI + manual add | P0 | ⬜ |
| Defense Strategy: AI-generated + user-editable | P1 | ⬜ |
| Timeline: chronological case events with deadlines | P1 | ⬜ |
| Action Plan: checklist with deadlines + priority | P1 | ⬜ |
| Evidence section: photos, documents grid | P1 | ⬜ |
| Risks & Weaknesses section | P2 | ⬜ |
| Linked Conversations | P1 | ⬜ |
| Basic case export (clipboard text) | P2 | ⬜ |

### Phase 3 — AI Intelligence

**Goal:** AI understands case context and provides proactive guidance

| Feature | Priority | Status |
|---|---|---|
| Context-aware AI (reads full case before responding) | P0 | ⬜ |
| Auto-categorization (AI response → case sections) | P0 | ⬜ |
| Citation chip → direct article deep link | P0 | ⬜ |
| Argument strength evaluation (Strong/Moderate/Weak) | P1 | ⬜ |
| Gap detection ("Your case is missing...") | P1 | ⬜ |
| Case risk score (overall strength assessment) | P2 | ⬜ |
| Proactive suggestions ("Consider asking about X") | P2 | ⬜ |

### Phase 4 — Document Intelligence

**Goal:** Users dump any document, AI figures out what it is

| Feature | Priority | Status |
|---|---|---|
| Document upload (camera, gallery, file picker) | P0 | ⬜ |
| OCR text extraction from photos | P0 | ⬜ |
| AI document type identification | P1 | ⬜ |
| Auto fact extraction from documents | P1 | ⬜ |
| Deadline extraction from documents → timeline | P1 | ⬜ |
| Evidence ↔ argument linking | P2 | ⬜ |
| Contradiction detection between documents | P2 | ⬜ |

### Phase 5 — Advanced Legal Guidance

**Goal:** The app becomes a genuine legal advisor

| Feature | Priority | Status |
|---|---|---|
| Counter-argument preparation | P1 | ⬜ |
| Similar case pattern analysis | P1 | ⬜ |
| Proactive strategy pivots | P2 | ⬜ |
| Push notifications for deadlines | P1 | ⬜ |
| Professional PDF export with formatting | P0 | ⬜ |
| Lawyer handoff package (structured brief) | P1 | ⬜ |
| Multi-case cross-references | P2 | ⬜ |

### Phase 6 — Platform & Scale

**Goal:** Scale beyond individual use

| Feature | Priority | Status |
|---|---|---|
| Cloud sync (optional, end-to-end encrypted) | P1 | ⬜ |
| Lawyer directory integration | P2 | ⬜ |
| Court procedure guidance (step-by-step) | P1 | ⬜ |
| Document template generation (filings, complaints) | P2 | ⬜ |
| Community features (anonymized patterns) | P3 | ⬜ |
| Web companion app | P3 | ⬜ |

---

## Architecture Impact

### Case = Central Entity
```
Case
├── id, title, status, domain, dates
├── Facts[]           → linked to Documents, Conversations
├── Arguments[]       → linked to LawArticles, Facts
├── ApplicableLaws[]  → linked from Arguments, AI responses
├── Strategy{}        → linked to Arguments, Laws
├── Timeline[]        → linked to Facts, Documents, deadlines
├── Evidence[]        → linked to Facts, Arguments
├── Risks[]           → linked to Arguments (weaknesses)
├── ActionItems[]     → deadlines, priorities
├── Conversations[]   → full AI chat history
└── Documents[]       → photos, PDFs, raw uploads
```

### Everything Links to Everything
- A **Fact** can be linked to: a Document (source), a Conversation (where it was discussed), an Argument (that it supports/undermines)
- An **Argument** links to: Law Articles (legal basis), Facts (evidence), Strategy (which strategy it serves)
- A **Law Article** links to: Arguments (which reference it), Cases (which use it), AI Conversations (where it was cited)
- A **Document** links to: Facts (extracted from it), Timeline events (dates found in it), the Case itself

### Backend Implications
- Need a relational model (not just document store) for cross-linking
- Case CRUD + section-level CRUD
- AI context injection: when user starts a consultation within a case, send full case context to AI
- Export service: generate structured summaries from case data

---

## Next Steps (Immediate)

1. **Finish design mockups** in open-design (Chat, Case Builder, Laws, Onboarding)
2. **Extract design tokens** from generated mockups → inject into Flutter ui_kit
3. **Scaffold Flutter features** using gen.sh (chat, case_builder, laws, notes, profile)
4. **Implement navigation** — 5-tab bottom nav with GoRouter
5. **Connect law browser** to MongoDB backend API
6. **Build basic AI chat** — connect to FastAPI backend
7. **Implement basic case creation** — title, domain, manual facts
