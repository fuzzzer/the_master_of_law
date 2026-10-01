# Stabilization — Technical Specs & Acceptance Criteria

## 1. Test Architecture

### Testing Strategy
All tests are **pure unit tests** with mocked external dependencies:
- No PostgreSQL, no Redis, no ChromaDB, no Gemini API calls
- External services mocked via `unittest.mock.AsyncMock` / `MagicMock`
- Tests run in <30s total on CI with no infrastructure

### Mock Strategy

| External Dependency | Mock Type | Returns |
|---------------------|-----------|---------|
| `AsyncSession` (SQLAlchemy) | `AsyncMock` | Mock ORM objects with `.id`, `.phase`, `.created_at`, etc. |
| `VertexAIClient.generate()` | `AsyncMock` | Predefined Georgian legal text |
| `VertexAIClient.generate_json()` | `AsyncMock` | Predefined JSON (queries list, case dict, etc.) |
| `VertexAIClient.create_chat()` | `MagicMock` | Chat object with `.send_message()` returning mock response |
| `ChromaClient.vector_search()` | `MagicMock` | List of chunk dicts with metadata |
| `ChromaClient.search_by_metadata()` | `MagicMock` | List of exact-match chunks |
| `VertexEmbeddingClient.embed_query()` | `MagicMock` | `[0.1] * 768` |
| `ConversationRepository` | `AsyncMock` | Mock conversation ORM objects |
| `MessageRepository` | `AsyncMock` | Mock message ORM objects |
| `CaseFileRepository` | `AsyncMock` | Mock case file ORM objects |

### Shared Fixtures (`tests/conftest.py`)

```python
# Key fixtures to create:
@pytest.fixture
def mock_db():
    """AsyncMock of AsyncSession with flush/commit/rollback."""

@pytest.fixture
def mock_gemini():
    """AsyncMock of VertexAIClient with default returns."""

@pytest.fixture
def mock_chroma():
    """MagicMock of ChromaClient with vector_search/get_by_ids."""

@pytest.fixture
def sample_law_chunks():
    """3 georgian_laws chunks with full metadata."""

@pytest.fixture
def sample_court_chunks():
    """2 court_practice chunks with case_id/category/year."""

@pytest.fixture
def sample_grand_chamber_chunks():
    """1 grand_chamber chunk with binding_rule/norm_interpreted."""

@pytest.fixture
def sample_history():
    """5-message conversation history [user, assistant, user, ...]."""
```

---

## 2. Test Specifications by Component

### Rate Limiting (`tests/test_rate_limit_middleware.py`)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Within FREE limit | 5 requests in 60s | All return 200 |
| Exceed FREE limit | 6th request in 60s | 429 + `Retry-After` header |
| PRO tier limit | 30 requests in 60s | All return 200 |
| ADMIN tier limit | 120 requests | All return 200 |
| Window reset | 5 requests, wait 60s, 5 more | All return 200 |
| Public path bypass | `/health` with no auth | 200 (no rate check) |
| Cleanup removes expired | Fill + wait → verify internal dict shrunk | Counter reset |

### API Key Auth (`tests/test_api_key_auth.py`)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Generate key | `generate_api_key()` | `sk_` prefix, 32+ hex chars, persisted |
| Valid key check | `is_valid_api_key(valid_key)` | `True` |
| Invalid key check | `is_valid_api_key("fake")` | `False` |
| Missing key file | `load_api_keys()` with no file | Empty set |
| Corrupt JSON | `load_api_keys()` with invalid file | Empty set |
| Admin key check endpoint | `GET /check` + valid admin key header | `{"status": "ok"}` |
| Admin key check invalid | `GET /check` + wrong key | 403 |
| Create key endpoint | `POST /api-keys` + valid admin key | `{"api_key": "sk_..."}` |
| Create key unauthorized | `POST /api-keys` + wrong admin key | 403 |

### Firebase Auth Middleware (`tests/test_auth_middleware.py`)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Public path | `GET /health` | Pass through, no auth |
| Dev mode no token | Request with no auth in dev | `dev-user-001` in `X-User-ID` |
| Admin API key | `X-API-Key: {admin_key}` | `admin-api-key` user, SUPERADMIN tier |
| User API key | `X-API-Key: {user_key}` | `api-user-{key[:8]}` |
| Invalid API key | `X-API-Key: fake` | 401 |
| Missing auth in prod | No token, no key, `app_env=production` | 401 |

### Conversation State Machine (`tests/test_conversation_service.py`)

| Test | Input | Expected |
|------|-------|----------|
| Create conversation | `user_id, title` | Phase = GREETING |
| Valid transition GREETING→INTAKE | `transition_phase(INTAKE)` | Returns True |
| Valid transition INTAKE→QUESTIONNAIRE | `transition_phase(QUESTIONNAIRE)` | Returns True |
| Valid transition INTAKE→ANALYSIS | `transition_phase(ANALYSIS)` | Returns True |
| Invalid transition GREETING→ADVICE | `transition_phase(ADVICE)` | Logs warning, still returns True (soft) |
| Determine next phase: GREETING + 1 msg | `determine_next_phase(id, 1)` | INTAKE |
| Determine next phase: QUESTIONNAIRE | `determine_next_phase(id, N)` | ANALYSIS |
| Determine next phase: ANALYSIS | `determine_next_phase(id, N)` | ADVICE |
| Determine next phase: ADVICE | `determine_next_phase(id, N)` | FOLLOW_UP |
| Parse invalid UUID | `_parse_uuid("not-a-uuid")` | None |
| Delete conversation | `delete_conversation(id)` | Messages deleted first, then conversation |
| Get history truncation | `get_conversation_history(id, max=3)` | Returns ≤3 messages |

### RAG Pipeline (`tests/test_rag_retrieval_service.py`)

| Test | Input | Expected |
|------|-------|----------|
| Stage 0: valid expansion | Gemini returns `["query1", "query2"]` | Returns both queries |
| Stage 0: empty list | Gemini returns `[]` | Returns `[]` (no search needed) |
| Stage 0: failure | Gemini raises Exception | Returns `[user_message]` fallback |
| Stage 3: dedup same ID | vector hit `A` + fulltext hit `A` | Single entry, lower distance kept |
| Stage 3: merge unique | vector `A` + fulltext `B` | Both in output |
| Stage 3: fulltext enrichment | fulltext-only IDs | `chroma.get_by_ids()` called to fill content |
| Full pipeline: pre-expanded | `pre_expanded_queries=["q"]` | Stage 0 skipped |
| Full pipeline: quotas | 20 law + 12 case chunks | Output: 15 laws + 8 cases max |
| Full pipeline: thresholds | threshold_service.search returns hits | Threshold hits prepended |
| search_law: exact match | `article_number="მუხლი 77"` | Metadata search called |
| search_law: normalize | `article_number="77"` | Converted to `"მუხლი 77"` |

### Agent Pipeline (`tests/test_agent_pipeline_service.py`)

| Test | Input | Expected |
|------|-------|----------|
| `_history_to_contents`: empty | `[]` | `[]` |
| `_history_to_contents`: consecutive roles | `[user, user, model]` | Merged to `[user, model]` |
| `_history_to_contents`: starts with model | `[model, user]` | Model popped → `[user]` |
| `_select_tools`: with case_file_id | `case_file_id="abc"` | `FULL_CASE_TOOLS` |
| `_select_tools`: case chat | `is_case_chat=True` | `CASE_CREATION_TOOLS` |
| `_select_tools`: default | Neither | `ALWAYS_TOOLS` |
| Phase 1: legal question | `"რა სასჯელი ეკისრება..."` | `needs_rag=True`, queries populated |
| Phase 1: greeting | `"გამარჯობა"` | `direct_response` set |
| Phase 1: flash fails | Exception raised | Fallback plan |
| Phase 3: all verified | All citations in chunks | 0 iterations, response unchanged |
| Phase 3: hallucination found | Citation not in corpus | Flash corrects, max 2 iterations |
| Full `run`: direct response | Greeting intent | Response from plan, no RAG |
| Full `run`: legal question | Legal intent | All 3 phases, response + chunks + citations |

### Case Builder (`tests/test_case_builder_service.py`)

| Test | Input | Expected |
|------|-------|----------|
| CaseFileRenderer: full data | Complete case dict | All 8 sections + disclaimer |
| CaseFileRenderer: missing sections | Only facts + laws | Only those 2 sections |
| CaseFileRenderer: empty | `{}` | Minimal output + disclaimer |
| `_format_conversation` | 3-message history | `USER: ...\nASSISTANT: ...\nUSER: ...` |
| `_expand_for_rag`: success | Gemini returns queries | Used directly |
| `_expand_for_rag`: failure | Exception | Fallback to raw text |
| `_auto_retrieve_chunks` | 2 user messages | Parallel RAG, merged, deduped |

### Document Generator (`tests/test_document_generator_service.py`)

| Test | Input | Expected |
|------|-------|----------|
| `_create_docx_from_markdown`: headings | `# Title\n## Sub` | H1 + H2 in DOCX |
| `_create_docx_from_markdown`: bold | `**bold text**` | Bold run in paragraph |
| `_create_docx_from_markdown`: empty lines | `\n\n` | Empty paragraphs |
| `_create_docx_from_markdown`: output | Any markdown | Returns `bytes`, len > 0 |

### Legal Analysis (`tests/test_legal_analysis_service.py`)

| Test | Input | Expected |
|------|-------|----------|
| `LawContextFormatter.format`: empty | `[]` | "No relevant legal context was found." |
| `LawContextFormatter.format`: laws | 2 law chunks | `[1] Code, Article...` format |
| `LawContextFormatter.format`: court | 1 court chunk | Case ID + category + year |
| `LawContextFormatter.format`: mixed | All 3 sources | Grouped by source type |
| `_build_system_prompt`: laws only | Only law chunks | Base prompt unchanged |
| `_build_system_prompt`: with court | Court chunks present | Court instructions appended |
| `_build_system_prompt`: with GC | Grand chamber present | GC instructions appended |
| `_build_system_prompt`: with thresholds | Threshold chunks present | Threshold instructions appended |
| `_build_user_prompt`: full | All params present | Status + case + law + history + message |
| `_build_user_prompt`: minimal | Just message + chunks | Law context + message |

---

## 3. Complex Flow Specifications

### Flow 1: Conversation Lifecycle

```
create_conversation("user1")
  → assert phase == GREETING
save_user_message(conv_id, "hello")
  → determine_next_phase(conv_id, 1) == INTAKE
  → transition_phase(conv_id, INTAKE)
save_user_message(conv_id, "legal question")
  → ... (more messages) ...
  → determine_next_phase == ANALYSIS → ADVICE → FOLLOW_UP
```

### Flow 2: RAG → Analysis End-to-End

```
rag.retrieve("legal question")
  → stage 0: expand to 3 queries
  → stage 1: vector search returns 10 hits per query
  → stage 2: fulltext returns 5 hits
  → stage 3: merge → 25 unique chunks
  → stage 4: rerank → top 20
  → quota: 15 laws + 5 cases = 20
  → threshold: 0 injected
analysis.analyze(user_msg, chunks)
  → returns text with citations + disclaimer
```

### Flow 3: Agent Pipeline with Tool Calls

```
pipeline.run(user_message="add fact: officer didn't read rights")
  → Phase 1: plan → intent=case_modification, needs_rag=True
  → Phase 2: RAG retrieves chunks → Gemini calls add_fact tool → result returned → Gemini generates response text
  → Phase 3: verify citations → 0 corrections needed
  → Result: response_text + chunks + 1 tool_result
```

---

## 4. Go/No-Go Criteria

- [ ] All pre-existing failures fixed (204/204 → clean)
- [ ] `tests/conftest.py` with shared fixtures created
- [ ] Rate limiting middleware: ≥7 tests, all passing
- [ ] API key auth: ≥9 tests, all passing
- [ ] Conversation state machine: ≥12 tests, all passing
- [ ] RAG pipeline: ≥11 tests, all passing
- [ ] Agent pipeline: ≥13 tests, all passing
- [ ] Case builder: ≥7 tests, all passing
- [ ] Document generator: ≥4 tests, all passing
- [ ] Legal analysis: ≥10 tests, all passing
- [ ] Complex flows: ≥5 tests, all passing
- [ ] Total test count: ≥300 (204 existing + ~100+ new)
- [ ] Full suite runs in <60s
- [ ] 0 failures, 0 errors, 0 collection errors
- [ ] `pytest tests/ --ignore=tests/scripts -q` → clean
