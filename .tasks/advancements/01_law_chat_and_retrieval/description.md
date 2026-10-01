# Task: Simple Law-Aware Chat + Isolated Law Retrieval

> **Covers:** Task 2 (Isolated Law Retrieval) + Task 3 (Simple Law-Aware Chat)
> **Why combined:** Both features share the same backend surface (`/laws/*`, `/chat/*`), the same Flutter feature module, and the same RAG subset (`legal_codes` only). Building them together avoids duplicate scaffolding.

---

## Purpose

Build two complementary user-facing features:

1. **Simple Law-Aware Chat** — A conversational interface where users ask plain-language questions about Georgian law and receive grounded, cited answers. Uses `legal_codes` collection only (no court practice). This is the "quick answer" mode.

2. **Isolated Law Retrieval** — A structured search-and-browse workflow for finding specific laws, articles, and legal provisions. This is Phase 1 of case building: the user (or AI) searches for relevant legal provisions before constructing arguments.

Together, these give users two access patterns:
- **Chat path:** "What does the law say about wrongful termination?" → AI answers with citations
- **Search path:** Browse legal codes → find relevant articles → save to case file

---

## Multi-Step Guide

### Milestone 1: Audit Existing Backend Surface
1. Verify `GET /api/v1/laws/search`, `/laws/codes`, `/laws/codes/{id}`, `/laws/articles/{id}` work correctly
2. Verify `POST /api/v1/chat/{id}/send` with `rag_config: {"legal_codes": true, "court_practice": false, "grand_chamber": false}` returns law-only answers
3. Document any gaps or missing fields in the API responses
4. **Verify:** curl commands return expected JSON for all endpoints

### Milestone 2: Flutter — Law Browser Feature
1. Read `frontend/.agents/orchestrator.md` for Flutter architecture patterns
2. Scaffold the `laws` feature module using established project patterns
3. Build repository layer: `LawBrowserRepository` wrapping the 4 law endpoints
4. Build cubit/state: `LawBrowserCubit` with states for codes list, code detail, article view, search results
5. Build UI screens:
   - `LawCodesScreen` — list of 12 legal codes with names in Georgian
   - `LawCodeDetailScreen` — article tree for a single code
   - `LawArticleScreen` — full article text with formatted content
   - `LawSearchScreen` — search bar + results list
6. Wire into the `Laws` tab in bottom navigation
7. **Verify:** Navigate through all 4 screens with real backend data

### Milestone 3: Flutter — Law-Aware Chat Mode
1. Create a "law-only" chat mode that hardcodes `RagConfigModel.lawsOnly()`
2. Build or extend `ChatScreen` with a visual indicator showing "Laws Only" mode
3. Ensure the chat input sends `rag_config` with only `legal_codes: true`
4. Display AI responses with proper Georgian text rendering and article citations
5. Make citations tappable → deep link to `LawArticleScreen` from Milestone 2
6. **Verify:** Send a legal question, receive a law-only answer, tap a citation to view the article

### Milestone 4: Isolated Retrieval for Case Building
1. Add a "Save to Case" action on law articles and search results
2. When inside an active case context, law retrieval results link to the case
3. Build `RelevantLawsSection` widget that shows laws saved to a case
4. Expose a `searchAndAttach` flow: search → select articles → attach to case file
5. **Verify:** From a case, search laws, select articles, see them in the case's "Relevant Laws" section

### Milestone 5: Polish & Integration Tests
1. Add loading states, error states, and empty states for all screens
2. Ensure Georgian text renders correctly (Mkhedruli U+10D0–U+10FF)
3. Test on different screen sizes
4. Write widget tests for key UI components
5. **Verify:** All screens handle loading/error/empty gracefully
