# Backend Stabilization — Comprehensive Test Suite

## The Problem

The backend has **204 passing tests** but they only cover leaf-node components (schemas, formatters, classifiers, config values). The entire **trunk** of the application — the services that actually deliver user value — has **zero test coverage**:

- **Conversation state machine** (7 phases, transition validation) — 0 tests
- **RAG pipeline** (5-stage retrieval, merge/dedup, quota enforcement) — 0 tests
- **Agent pipeline** (3-phase: Plan → Execute → Verify) — 0 tests
- **Case builder** (3-stage: conversation → analysis → structured JSON) — 0 tests
- **Legal analysis service** (context formatting, source-specific prompt injection) — 0 tests
- **Rate limiting middleware** — 0 tests
- **API key authentication** — 0 tests
- **WebSocket chat flow** — 0 tests
- **Complex cross-service flows** — 0 tests

Additionally, there are **2 pre-existing test failures**:
1. `test_config.py::TestRAGConstants::test_values` — stale assertion (`50` should be `75`)
2. `test_scratch.py::test_flag` — scratch file incorrectly collected as test

## Why This Matters

Every user-facing feature flows through untested code. A single regression in the conversation state machine, RAG pipeline, or agent pipeline could silently break the entire application. The credit system charges users for operations that have never been tested end-to-end.

## Dependencies

- Tasks 01–13 complete (all features are built and deployed)
- No new features — this task is purely about verifying and stabilizing what exists

## Implementation Approach

The entire test suite uses **unit-level mocking** (no real DB, no real Gemini, no real ChromaDB). Every external dependency is mocked via `unittest.mock.AsyncMock` or `MagicMock`. This keeps tests fast (<30s for the full suite) and runnable without infrastructure.

---

## Milestones

### Milestone 1: Fix Pre-Existing Failures
1. Fix `test_config.py::TestRAGConstants::test_values` — update assertion from `50` to `75`
2. Mark `test_scratch.py` with `conftest.py` exclusion or rename so pytest doesn't collect it
3. Fix `tests/scripts/test_rag.py` collection error via `conftest.py` or `pyproject.toml` exclusion
4. **Verify**: `pytest tests/ --ignore=tests/scripts -q` → 0 failures

### Milestone 2: Test Infrastructure
1. Create `tests/conftest.py` with shared fixtures:
   - `mock_db` — `AsyncMock` of `AsyncSession` (flush, commit, rollback)
   - `mock_gemini` — `AsyncMock` of `VertexAIClient` (generate, generate_json, generate_stream, create_chat)
   - `mock_chroma` — `MagicMock` of `ChromaClient` (vector_search, search_by_metadata, get_by_ids)
   - `mock_embedding` — `MagicMock` of `VertexEmbeddingClient` (embed_query, embed_queries)
   - `sample_chunks` — pre-built list of law/court/grand_chamber chunk dicts
   - `sample_conversation_history` — pre-built history list
2. Configure `pyproject.toml` to exclude `tests/scripts/` from collection
3. **Verify**: All fixtures importable, existing tests still pass

### Milestone 3: Rate Limiting Tests
1. Test `RateLimitMiddleware`:
   - Requests within limit succeed
   - Requests exceeding per-minute limit return 429
   - Different tiers (FREE=5, PRO=30, ADMIN=120) have correct limits
   - Window cleanup after 60s resets counters
   - Public paths bypass rate limiting
   - Missing user context → treated as FREE tier
2. **Verify**: All rate limit tests pass

### Milestone 4: API Key & Auth Tests
1. Test API key utilities (`api_keys.py`):
   - `generate_api_key()` → creates valid `sk_*` key and persists to file
   - `is_valid_api_key()` → returns True for stored key, False for random
   - `load_api_keys()` → handles missing file, corrupt JSON, empty file
2. Test API key router:
   - `POST /api/v1/api-keys` with valid admin key → 200 + new key
   - `POST /api/v1/api-keys` with invalid admin key → 403
   - `GET /api/v1/api-keys/check` with valid admin key → 200
   - `GET /api/v1/api-keys/check` with invalid admin key → 403
3. Test Firebase auth middleware (public path bypass, dev mode mock user, API key auth):
   - Public paths (`/health`, `/ready`, `/docs`) → no auth required
   - Dev mode + no token → mock user `dev-user-001`
   - Valid API key → user_id `api-user-{key[:8]}`
   - Admin API key → user_id `admin-api-key`, tier `SUPERADMIN`
   - Invalid API key → 401
4. **Verify**: All auth tests pass

### Milestone 5: Conversation State Machine Tests
1. Test `ConversationService._parse_uuid`:
   - Valid UUID → returns UUID object
   - Invalid string → returns None
   - Empty string → returns None
2. Test `ConversationService._conv_to_dict`:
   - Full ORM object → correct dict with all fields
   - None values → sensible defaults
3. Test `ConversationService.create_conversation` → starts in GREETING phase
4. Test `ConversationService.transition_phase`:
   - All valid transitions (GREETING→INTAKE, INTAKE→QUESTIONNAIRE, etc.)
   - Invalid transition → logs warning but still transitions (soft state machine)
5. Test `ConversationService.determine_next_phase`:
   - GREETING + 1 message → INTAKE
   - QUESTIONNAIRE → ANALYSIS
   - ANALYSIS → ADVICE
   - ADVICE → FOLLOW_UP
   - Unknown phase → GREETING (fallback)
6. Test `ConversationService.save_user_message` and `save_assistant_message`
7. Test `ConversationService.get_conversation_history` with `max_messages` truncation
8. Test `ConversationService.delete_conversation` deletes messages before conversation (FK order)
9. **Verify**: All state machine tests pass

### Milestone 6: RAG Pipeline Tests
1. Test `RAGRetrievalService._stage_0_expand_queries`:
   - Gemini returns valid list → used directly
   - Gemini returns empty list → interpreted as "no search needed"
   - Gemini fails → fallback to `[user_message]`
   - Gemini returns non-list → fallback to `[user_message]`
2. Test `RAGRetrievalService._stage_1_vector_search`:
   - Embeds queries, calls chroma.vector_search per embedding
   - Tags hits with `source="vector"` and `query_index`
   - Handles embedding failure gracefully (per-query fallback)
3. Test `RAGRetrievalService._stage_2_fulltext_search`:
   - Scores tokens against article index
   - Returns hits sorted by score
   - Empty/missing index → returns empty
4. Test `RAGRetrievalService._stage_3_merge_and_dedup`:
   - Same chunk_id from vector + fulltext → keeps lower distance
   - Unique chunks merged correctly
   - Fulltext-only chunks enriched from chroma.get_by_ids
5. Test `RAGRetrievalService.retrieve` (integration of all stages):
   - Full pipeline with mocked sub-stages
   - Pre-expanded queries → skips stage 0
   - Empty expansion → returns empty
   - Quota enforcement: max 15 laws + 8 cases
   - Threshold injection at the front
6. Test `RAGRetrievalService.search_law`:
   - Exact metadata match by article_number + code_name
   - Semantic fallback when no exact match
   - Article number normalization (`"77"` → `"მუხლი 77"`)
7. **Verify**: All RAG tests pass

### Milestone 7: Legal Analysis & Formatting Tests
1. Test `LawContextFormatter.format`:
   - Georgian laws → numbered format with code/article/title/URL/content
   - Court practice → case_id/category/year/section format
   - Grand chamber → ⚠️ prefix, binding_rule, norm_interpreted
   - Mixed sources → grouped by type with correct headers
   - Empty chunks → "No relevant legal context was found."
2. Test `ConversationHistoryFormatter.format`:
   - Normal history → USER/ASSISTANT labeled
   - Max turns truncation
   - Empty history → empty string
3. Test `LegalAnalysisService._build_system_prompt`:
   - Laws-only → base prompt unchanged
   - Laws + court_practice → court instructions appended
   - Laws + grand_chamber → GC instructions appended
   - Threshold chunks present → threshold instructions appended
   - All sources → all instructions appended
4. Test `LegalAnalysisService._build_user_prompt`:
   - With conversation_status metadata → included at top
   - With case_context → included before law context
   - With history → history formatted and included
   - Just user message → clean output
5. **Verify**: All legal analysis tests pass

### Milestone 8: Agent Pipeline Tests
1. Test `AgentPipelineService._history_to_contents`:
   - Empty → empty list
   - Normal alternating → correct Content objects
   - Consecutive same-role → merged
   - Starts with model → first entry popped
   - Truncated to last 20 messages
2. Test `AgentPipelineService._format_law_context`:
   - Formats chunks with numbering, code, article, URL, content
   - Caps at 30 chunks
   - Content truncated at 2000 chars
   - Empty chunks → empty string
3. Test `AgentPipelineService._select_tools`:
   - With case_file_id → FULL_CASE_TOOLS
   - With is_case_chat (no case_id) → CASE_CREATION_TOOLS
   - Neither → ALWAYS_TOOLS
4. Test `AgentPipelineService._phase_1_plan`:
   - Legal question → `needs_rag=True`, search_queries populated
   - Greeting → `direct_response` set, `needs_rag=False`
   - Flash model failure → fallback plan with raw message
5. Test `AgentPipelineService._phase_2_execute`:
   - RAG retrieval + Gemini response (no tools)
   - Tool call → execute → feed result back → final text
   - Multiple tool iterations
   - `search_law` tool special handling
6. Test `AgentPipelineService._phase_3_verify`:
   - All citations verified → no correction needed
   - Some citations not found → Flash corrects
   - Corpus-found citations → added to chunks
   - Max iterations respected
   - Empty response → skip verification
7. Test `AgentPipelineService.run` (full pipeline):
   - Direct response path (greeting) → skip phases 2+3
   - Full legal question path → all 3 phases
   - Tool call path → tool results in output
8. **Verify**: All agent pipeline tests pass

### Milestone 9: Case Builder & Document Generator Tests
1. Test `CaseFileRenderer.render`:
   - Full case data → all 8 sections rendered with emojis
   - Missing sections → skipped gracefully
   - Empty case data → minimal output with disclaimer
2. Test `LawContextFormatter.format` (case_builder version):
   - Formats chunks for case builder prompts
   - Empty → "No law articles retrieved."
3. Test `CaseBuilderService._format_conversation`:
   - Formats history as `ROLE: content` lines
4. Test `CaseBuilderService._auto_retrieve_chunks`:
   - Expands user messages via Flash → runs RAG per query → merges/deduplicates
   - Empty user messages → empty result
5. Test `CaseBuilderService._expand_for_rag`:
   - Gemini returns query list → used
   - Gemini fails → fallback to raw text
6. Test `DocumentGeneratorService._create_docx_from_markdown`:
   - Headings (# ## ###) → correct heading levels
   - Bold (**text**) → bold runs
   - Empty lines → empty paragraphs
   - Returns valid bytes
7. **Verify**: All case builder / document generator tests pass

### Milestone 10: Complex User Flow Tests
1. **Flow: First message → conversation phase transition**
   - Create conversation (GREETING) → send message → phase becomes INTAKE → send more → ANALYSIS → ADVICE → FOLLOW_UP
2. **Flow: RAG → Analysis → Citation Verification → Response**
   - Mock full pipeline: expand queries → vector search → merge → rerank → analyze → extract citations → verify
3. **Flow: Agent pipeline with tool calls**
   - Plan says needs_rag → RAG retrieves → Gemini calls `add_fact` tool → result fed back → final response
4. **Flow: Case builder end-to-end**
   - Conversation with 5 messages → _auto_retrieve_chunks → _generate_full_analysis → _generate_case_data → render → persist
5. **Flow: WebSocket authentication paths**
   - dev mode → auto-auth
   - admin API key → auth as admin
   - user API key → auth as api-user
   - invalid API key → 1008 close
   - no auth in production → 1008 close
6. **Verify**: All flow tests pass

### Milestone 11: Final Verification & Cleanup
1. Run full test suite: `pytest tests/ --ignore=tests/scripts -v`
2. Count total tests — should be ~350+ (204 existing + ~150 new)
3. Verify 0 failures, 0 errors
4. Check for any warnings and resolve them
5. **Verify**: Clean run, all green
