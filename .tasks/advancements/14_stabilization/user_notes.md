# Stabilization — User Notes

> These notes override anything in `description.md` or `specs.md`.

---

## Scoping Notes (from user)

1. **Rate limiting and API key auth** — test these now, they exist and are functional
2. **Credit gate middleware** — not tested yet since features aren't finalized
3. **Firebase auth** — test the dev mode and API key paths only (no real Firebase token verification in tests)
4. **Focus areas:**
   - Orchestration layer (conversation state machine, RAG pipeline, agent pipeline, case builder)
   - Complex user flows (multi-service interactions)
   - Peace of mind that nothing breaks in complex paths

## Design Decisions

1. All tests must be **pure unit tests** — no real DB, no real Gemini, no real ChromaDB
2. Use `unittest.mock` exclusively (matches existing test style)
3. Shared fixtures in `tests/conftest.py` reduce boilerplate
4. Keep test files aligned with source files: `test_conversation_service.py` tests `conversation_service.py`

## Priority Order

1. Fix pre-existing failures first (2 broken tests, 1 collection error)
2. Test infrastructure (conftest, exclusions)
3. Auth & rate limiting (user-requested priority)
4. Conversation state machine (core user flow)
5. RAG pipeline (core AI feature)
6. Legal analysis formatting (data correctness)
7. Agent pipeline (orchestrator)
8. Case builder & doc gen (high credit cost operations)
9. Complex flows (cross-service verification)
