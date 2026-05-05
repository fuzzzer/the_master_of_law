# 🔍 Research Items — One-Touch Full Fillout

> Research questions that must be answered before implementation.

---

## 1. Prompt Engineering — Intake-to-Case

### Question
How should we structure the Gemini prompt to convert 5-7 intake answers into a full 8-section case file with accurate law citations?

### What to research
- [ ] Review existing `CASE_BUILDER` prompt in `backend/app/prompts/case_builder.py`
- [ ] Study how the current prompt formats law context from RAG chunks
- [ ] Test different prompt structures: single-shot vs chain-of-thought
- [ ] Test Georgian vs English prompt instructions (Gemini may reason better in English, output in Georgian)
- [ ] Measure citation accuracy: how often does Gemini cite real articles vs hallucinated ones?

### Key decision
**Single mega-prompt** vs **multi-step generation** (facts first → arguments → strategy → etc.)?
- Single: faster, cheaper (1 Gemini call), but less accurate per section
- Multi-step: 4-5 calls, more expensive, but each section gets focused attention
- **Recommended:** Multi-step with 3 calls: (1) Facts+Evidence, (2) Arguments+Laws, (3) Strategy+Risks+Actions

### Files to reference
- `backend/app/prompts/case_builder.py` — existing prompt template
- `backend/app/services/case_builder_service.py` — existing build pipeline
- `backend/app/services/rag_service.py` — RAG retrieval pipeline

---

## 2. RAG Query Strategy for Intake

### Question
How do we form optimal RAG queries from short intake answers?

### What to research
- [ ] Current RAG pipeline: `expand → vector → fulltext → merge → rerank`
- [ ] Can we run multiple RAG queries per intake? (one per legal issue detected)
- [ ] How to extract legal domain keywords from free-text Georgian input
- [ ] Optimal chunk count: 15-25 chunks per case generation?
- [ ] Should we pre-filter by legal domain (user selected) before vector search?

### Key decision
**Single RAG query** from the full situation text vs **multiple targeted queries**?
- Single: simpler, may miss specific sub-issues
- Multiple: e.g., query for "ხელშეკრულების დარღვევა", then "გირაოს დაბრუნება", then "ხანდაზმულობა"
- **Recommended:** AI first identifies 3-5 legal keywords/issues from the intake, then RAG query each

---

## 3. Wizard UX — Question Flow

### Question
How to make the wizard feel simple despite collecting complex legal information?

### What to research
- [ ] Study legal intake forms from Georgian legal aid services (legalaid.ge)
- [ ] Review best practices for multi-step wizards in mobile apps
- [ ] How to handle conditional logic (Step 6 follow-ups) without confusing the user
- [ ] Voice-to-text viability on web (Web Speech API) vs mobile only
- [ ] Progress indicator design: steps vs percentage vs none?

### Key decision
**Bottom sheet wizard** vs **full-screen wizard**?
- Bottom sheet: less intimidating, but limited space
- Full screen: more room for explanations, feels like a real form
- **Recommended:** Full-screen with smooth page transitions, minimal UI per step

---

## 4. Citation Verification Pipeline

### Question
How do we ensure every generated citation actually exists in our corpus?

### What to research
- [ ] Current citation format from Gemini: article number + code name
- [ ] Can we post-process Gemini output to verify each citation against ChromaDB?
- [ ] What happens when Gemini cites an article that's NOT in our corpus?
- [ ] Should we strip unverified citations or mark them with 🟡?
- [ ] matsne.gov.ge URL format: can we construct deep links from article metadata?

### Key decision
**Strict verification** (remove unverified) vs **trust-level labeling** (show all, mark unverified)?
- **Recommended:** Trust-level labeling — matches the existing 3-tier trust system (🟢🟡🔵)

---

## 5. Case Summary View — Architecture

### Question
New standalone page or overlay on existing case workspace?

### What to research
- [ ] Can we reuse existing case tab components (FactCard, ArgumentCard, etc.)?
- [ ] How to handle the "edit" transition smoothly (summary → workspace)
- [ ] Export format: PDF? Clipboard text? Share sheet?
- [ ] Should the summary view persist as a separate entity or just be an initial view?

### Key decision
**Separate page** vs **enhanced Overview tab**?
- Separate: cleaner UX for first-time viewing, but adds navigation complexity
- Enhanced Overview: reuse existing structure, but may not feel special enough
- **Recommended:** New `CaseGeneratedSummaryPage` that auto-navigates to after generation, then "Edit" goes to workspace

---

## 6. Partial Fill (Existing Case)

### Question
How should AI handle cases where some sections already have user data?

### What to research
- [ ] How to merge AI-generated data with existing user data (conflict resolution)
- [ ] Should AI see the existing data as context? (probably yes)
- [ ] User confirmation UX: "AI wants to add 3 facts — accept?" vs auto-merge
- [ ] Undo capability after AI fills sections

### Key decision
**Overwrite** vs **append** vs **suggest-and-confirm**?
- **Recommended:** Suggest-and-confirm with diff view: "AI suggests these additions" → user checkmarks what to keep

---

## 7. Performance & Cost

### Question
How long will generation take and what's the credit economics?

### What to research
- [ ] Gemini 3.1 Pro latency for ~2000 token input + structured JSON output
- [ ] If multi-step: total latency of 3 sequential Gemini calls
- [ ] Can we parallelize any Gemini calls? (facts+evidence || strategy+risks)
- [ ] Streaming partial results to show progress
- [ ] Cost per generation: tokens in/out × Gemini pricing

### Key decision
**Wait-for-all** vs **stream-sections**?
- Wait: simpler, user sees loading screen for 15-30s
- Stream: sections appear one by one, feels faster, more complex
- **Recommended:** Progressive loading with section-by-section reveal animation

---

## 8. Georgian NLP Considerations

### Question
How well does Gemini handle Georgian legal terminology?

### What to research
- [ ] Test Gemini's ability to correctly reference Georgian law article structure
- [ ] Test accuracy of legal term usage (vs casual Georgian)
- [ ] Can we provide a glossary of legal terms in the system prompt?
- [ ] How to handle mixed Georgian/Latin legal references (EU law references)

### Files to test with
- `law_corpus/data/chroma/` — actual Georgian law text chunks
- Test with 3-4 different legal domains: სამოქალაქო, სისხლის, შრომის, ადმინისტრაციული

---

## Priority Order

| # | Research Item | Blocking? | Effort |
|---|--------------|-----------|--------|
| 1 | Prompt Engineering | 🔴 Yes | High |
| 2 | RAG Query Strategy | 🔴 Yes | Medium |
| 4 | Citation Verification | 🔴 Yes | Medium |
| 3 | Wizard UX | 🟡 Partial | Low |
| 7 | Performance & Cost | 🟡 Partial | Medium |
| 8 | Georgian NLP | 🟡 Partial | Medium |
| 5 | Summary View Architecture | 🟢 No | Low |
| 6 | Partial Fill | 🟢 No | Low |
