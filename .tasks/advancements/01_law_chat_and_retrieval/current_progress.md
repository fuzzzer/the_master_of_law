# Progress: Law-Aware Chat + Isolated Law Retrieval

> **Status:** ✅ Complete (Milestones 1-4 done, Milestone 5 partial — tests not written)
> **Last updated:** 2026-05-09
> **Agent:** Antigravity

---

## Milestone 1: Audit Existing Backend Surface
- [x] Verify `GET /api/v1/laws/search` returns correct results
- [x] Verify `GET /api/v1/laws/codes` returns all 12 codes
- [x] Verify `GET /api/v1/laws/codes/{id}` returns article tree
- [x] Verify `GET /api/v1/laws/articles/{id}` returns full text
- [x] Verify chat with `rag_config` laws-only mode works
- [x] Document any API response gaps or missing fields
- [x] **Milestone complete:** All endpoints return expected JSON ✅

## Milestone 2: Flutter — Law Browser Feature
- [x] Read Flutter architecture guide
- [x] Scaffold `lib/features/laws/` module structure
- [x] Create `LawsRepository` with all 4 endpoint methods
- [x] Create data models: `LawCode`, `LawChunk`, `LawSearchResults`, `LawArticleDetail`
- [x] Create `LawsCubit` with states for all screens
- [x] Build `LawsHomePage` — list of codes from API
- [x] Build `LawCodeDetailPage` — article tree
- [x] Build `LawArticlePage` — full article text
- [x] Build `LawSearchPage` — search + results
- [x] Wire into Laws tab in bottom navigation
- [x] **Milestone complete:** All 4 screens render with real data ✅

## Milestone 3: Flutter — Law-Aware Chat Mode
- [x] Create "law-only" chat mode with `RagConfigPresets.lawsOnly`
- [x] Add visual mode indicator in chat header
- [x] Chat input sends correct `rag_config` payload
- [x] AI responses render with proper Georgian formatting
- [x] Citations are tappable → navigate to `LawArticlePage`
- [x] **Milestone complete:** Full chat → citation → article flow works ✅

## Milestone 4: Isolated Retrieval for Case Building
- [x] Add "Save to Case" action on articles and search results
- [x] Build `LinkedArticleData` Hive model (typeId: 8)
- [x] Add `linkArticle`/`unlinkArticle` to `CaseDetailCubit`
- [x] Case picker bottom sheet on `LawArticlePage`
- [x] **Milestone complete** ✅

## Milestone 5: Polish & Integration Tests
- [x] Loading states for all screens
- [x] Error states with retry for all screens
- [x] Empty states with helpful messages
- [x] Georgian text rendering verified
- [ ] Widget tests for key components
- [ ] **Milestone partial:** UI states done, tests not written

---

## Blockers / Notes

- Widget tests not yet written (Milestone 5).
- `RelevantLawsSection` widget for case workspace view can be added later when case workspace gets a full redesign.
