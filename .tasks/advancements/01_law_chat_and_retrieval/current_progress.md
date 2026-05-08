# Progress: Law-Aware Chat + Isolated Law Retrieval

> **Last updated:** _not started_
> **Agent:** _unassigned_

---

## Milestone 1: Audit Existing Backend Surface
- [ ] Verify `GET /api/v1/laws/search` returns correct results
- [ ] Verify `GET /api/v1/laws/codes` returns all 12 codes
- [ ] Verify `GET /api/v1/laws/codes/{id}` returns article tree
- [ ] Verify `GET /api/v1/laws/articles/{id}` returns full text
- [ ] Verify chat with `rag_config` laws-only mode works
- [ ] Document any API response gaps or missing fields
- [ ] **Milestone complete:** All endpoints return expected JSON ✅

## Milestone 2: Flutter — Law Browser Feature
- [ ] Read Flutter architecture guide (`fuzzy_starter/.agents/orchestrator.md`)
- [ ] Scaffold `lib/features/laws/` module structure
- [ ] Create `LawBrowserRepository` with all 4 endpoint methods
- [ ] Create data models: `LawCodeModel`, `LawArticleModel`, `LawSearchResultModel`
- [ ] Create `LawBrowserCubit` with states for all screens
- [ ] Build `LawCodesScreen` — list of 12 codes
- [ ] Build `LawCodeDetailScreen` — article tree
- [ ] Build `LawArticleScreen` — full article text
- [ ] Build `LawSearchScreen` — search + results
- [ ] Wire into Laws tab in bottom navigation
- [ ] **Milestone complete:** All 4 screens render with real data ✅

## Milestone 3: Flutter — Law-Aware Chat Mode
- [ ] Create "law-only" chat mode with hardcoded `RagConfigModel.lawsOnly()`
- [ ] Add visual mode indicator in chat header
- [ ] Chat input sends correct `rag_config` payload
- [ ] AI responses render with proper Georgian formatting
- [ ] Citations are tappable → navigate to `LawArticleScreen`
- [ ] **Milestone complete:** Full chat → citation → article flow works ✅

## Milestone 4: Isolated Retrieval for Case Building
- [ ] Add "Save to Case" action on articles and search results
- [ ] Build `RelevantLawsSection` widget for case view
- [ ] Implement `searchAndAttach` flow
- [ ] Case context header shows when launched from a case
- [ ] **Milestone complete:** Articles can be searched, selected, and attached to cases ✅

## Milestone 5: Polish & Integration Tests
- [ ] Loading states for all screens
- [ ] Error states with retry for all screens
- [ ] Empty states with helpful messages
- [ ] Georgian text rendering verified
- [ ] Widget tests for key components
- [ ] **Milestone complete:** All edge cases handled gracefully ✅

---

## Blockers / Notes

_None yet._
