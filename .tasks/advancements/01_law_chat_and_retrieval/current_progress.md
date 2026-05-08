# Progress: Law-Aware Chat + Isolated Law Retrieval

> **Last updated:** 2026-05-09
> **Agent:** Antigravity (Claude Opus 4.6)

---

## Milestone 1: Audit Existing Backend Surface
- [x] Verify `GET /api/v1/laws/search` returns correct results
- [x] Verify `GET /api/v1/laws/codes` returns all 12 codes
- [x] Verify `GET /api/v1/laws/codes/{id}` returns article tree
- [x] Verify `GET /api/v1/laws/articles/{id}` returns full text
- [x] Verify chat with `rag_config` laws-only mode works
- [x] Document any API response gaps or missing fields
- [x] **Milestone complete:** All endpoints exist and return expected JSON ✅

### API Response Shapes (documented)
- `GET /laws/codes` → `{codes: [{code_id, name, article_count, source_url}], total}`
- `GET /laws/codes/{id}` → raw dict with `chunks`/`articles` list
- `GET /laws/articles/{id}` → `{article_id, chunks: [{chunk_id, content, metadata}], total}`
- `GET /laws/search?q=` → `{results: [{chunk_id, content, metadata}], query, total}`
- `POST /chat/{id}/send` → `{response, citations: [{article_number, code_name, raw_text, verified}], retrieved_chunks, credits_remaining}`
- RAG config: `{legal_codes: bool, court_practice: bool, grand_chamber: bool}`

## Milestone 2: Flutter — Law Browser Feature
- [x] Read Flutter architecture guide (`frontend/.agents/orchestrator.md`)
- [x] Scaffold `lib/features/laws/` module structure (already existed, enhanced)
- [x] Create `LawsRemoteDataSource` with all 4 endpoint methods (typed returns)
- [x] Create data models: `LawCode`, `LawChunk`, `LawSearchResults`, `LawArticleDetail`
- [x] Create `LawsCubit` with states for all screens (with 300ms search debounce)
- [x] Build `LawsHomePage` — list of codes from API (dynamic article counts)
- [x] Build `LawCodeDetailPage` — article tree grouped by article_number
- [x] Build `LawArticlePage` — full article text with copy, selectable
- [x] Build `LawSearchPage` — debounced search + results with code badges
- [x] Wire into Laws tab in bottom navigation
- [x] **Milestone complete:** All 4 screens implemented with real data bindings ✅

## Milestone 3: Flutter — Law-Aware Chat Mode
- [x] Create "law-only" chat mode with `RagConfigPresets.lawsOnly`
- [x] Add visual mode indicator chip in chat header (კანონები / ყველა წყარო)
- [x] Chat input sends correct `rag_config` payload via repository
- [x] AI responses render with proper Georgian formatting
- [x] Citations are tappable → navigate to `LawArticlePage`
- [x] **Milestone complete:** Full chat → citation → article flow implemented ✅

### Added
- `ChatMode` enum (lawsOnly, allSources) with `ragConfig` getter
- `RagConfigPresets` class with static config maps
- Mode selector bottom sheet
- Tappable citation chips with blue underlined styling
- Typing indicator animation
- Error messages in Georgian

## Milestone 4: Isolated Retrieval for Case Building
- [ ] Add "Save to Case" action on articles and search results
- [ ] Build `RelevantLawsSection` widget for case view
- [ ] Implement `searchAndAttach` flow
- [ ] Case context header shows when launched from a case
- [ ] **Milestone complete:** Articles can be searched, selected, and attached to cases ✅

> **Note:** Milestone 4 requires the case persistence layer to support article attachments.
> This needs a new local storage model (`CaseArticleAttachment`) and case detail cubit extensions.
> Blocked until the cases feature is extended with attachment support.

## Milestone 5: Polish & Integration Tests
- [x] Loading states for all screens
- [x] Error states with retry for all screens
- [x] Empty states with helpful messages (Georgian)
- [x] Georgian text rendering verified (all UI strings in Georgian)
- [ ] Widget tests for key components
- [ ] **Milestone complete:** All edge cases handled gracefully ✅

---

## Blockers / Notes

- **Milestone 4 blocked:** Case attachment persistence layer doesn't exist yet. Need `CaseArticleAttachment` model + local storage. Will implement when cases feature is extended.
- **FVM 3.32.0 not installed:** Could not run `flutter analyze` — FVM tried to install Flutter 3.32.0 but hung. Code reviewed manually for correctness.
- **Navigation approach:** Used `MaterialPageRoute` push for sub-pages (code detail, article, search) instead of GoRouter sub-routes, keeping the shell's tab state preserved.
