# Test Results & Regression Coverage

> Test suite status after all fixes applied.

---

## Backend Tests

```
$ cd backend && python -m pytest tests/ --ignore=tests/scripts -q
436 passed in 16.15s
```

**0 failures, 0 xfails.** Full pass.

### New Tests Added (This Task)

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_chroma_real_data.py` | 97 | All 13 legal codes present, article_number format, code_name format, content verification |
| `test_citation_extraction_real.py` | 27 | Citation extraction from real AI output, code name resolution, abbreviation handling |
| `test_rag_edge_cases.py` | 23 | RAG retrieval edge cases, empty queries, mixed-language input |
| `test_rag_retrieval_service.py` | 15 | Search by article, code_name normalization, multi-collection search |
| `test_agent_pipeline_service.py` | 18 | Agent tool calls, law lookup, citation verification flow |
| `test_legal_analysis_service.py` | 12 | Legal analysis prompting, source attribution |
| `test_case_builder_service.py` | 10 | Case building flow, evidence linking |
| `test_conversation_service.py` | 14 | Conversation management, context windowing |
| `test_document_generator_service.py` | 8 | Document generation, template rendering |
| `test_rate_limit_middleware.py` | 11 | Rate limiting by tier, burst handling |
| `test_api_key_auth.py` | 17 | API key CRUD, authentication flows |
| `test_complex_flows.py` | 13 | Multi-step user flows, credit consumption |

**Total: 265 new tests added** across 12 new test files.

---

## Pipeline Tests (law_corpus)

```
$ cd law_corpus && python -m pytest tests/test_parser.py::TestArticleNumberFallback tests/test_parser.py::TestThresholdCodeNameCanonical -v
9 passed in 0.41s
```

### New Pipeline Regression Tests

| Class | Tests | What It Covers |
|-------|-------|----------------|
| `TestArticleNumberFallback` | 3 | No-space article header → correct `მუხლი N` format |
| `TestThresholdCodeNameCanonical` | 6 | Short-form → full canonical code name mapping |

### Pre-existing Pipeline Test Status

The following pre-existing tests have known failures unrelated to this task:
- `TestStructureExtractor::test_extract_articles` — fixture `sample_article.html` uses plain `<p>` tags without `muxlixml` CSS classes
- `TestStructureExtractor::test_extract_with_books` — same fixture issue
- `TestHtmlParser::test_parse_sample_html` — same fixture issue

These failures exist because the test fixture HTML doesn't use matsne.gov.ge CSS class conventions. They are NOT regressions from our changes — they existed before this task.

---

## Integration Test Coverage for Fixed Bugs

### Bug 1: Malformed article_number
```
test_parser.py::TestArticleNumberFallback::test_no_space_article_header      ✅
test_parser.py::TestArticleNumberFallback::test_no_space_with_superscript    ✅
test_parser.py::TestArticleNumberFallback::test_standard_article_still_works ✅
test_chroma_real_data.py::TestArticleFormatting::test_article_number_format   ✅
```

### Bug 2: Short-form code_name
```
test_parser.py::TestThresholdCodeNameCanonical::test_canonicalize_*          ✅ (6 tests)
test_parser.py::TestThresholdCodeNameCanonical::test_build_metadata_uses_*   ✅
test_chroma_real_data.py::TestCodeNameConsistency::test_code_name_uses_*     ✅
```

### Bug 3-5: Citation service fixes
```
test_citation_extraction_real.py::TestCitationExtraction::*                  ✅ (27 tests)
```

---

## How to Run Tests

### Backend (from project root)
```bash
cd backend
python -m pytest tests/ --ignore=tests/scripts -q --tb=short
```

### Pipeline regression tests (from project root)
```bash
cd law_corpus
python -m pytest tests/test_parser.py -v --tb=short
```

### Integration tests only (requires ChromaDB data)
```bash
cd backend
python -m pytest tests/test_chroma_real_data.py -v -m integration --tb=short
```

### All tests with coverage
```bash
cd backend
python -m pytest tests/ --ignore=tests/scripts --cov=app --cov-report=term-missing -q
```
