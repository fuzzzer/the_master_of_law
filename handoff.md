# 🏛️ The Master of Law — Full Project Handoff

> **Last updated:** 2026-05-04T06:28 (Tbilisi time, UTC+4)
> **Status:** Embedding pipeline running (`gemini-embedding-001` via Vertex AI). Indexing is the immediate next step.

---

## 1. Project Overview

**"The Master of Law" (კანონის ოსტატი)** is an AI-powered legal advocate for Georgian citizens. It uses the full text of Georgian legislation, combined with Gemini 3.1 Pro's reasoning, to build defense strategies — citing exact law articles, identifying every applicable defense, and explaining in plain language.

### Architecture (3-layer)

```
Flutter App ←→ FastAPI Backend (Gemini 3.1 Pro + RAG) ←→ Law Corpus Pipeline (offline)
```

| Layer | Status |
|-------|--------|
| **Law Corpus Pipeline** | 🔄 Embedding in progress (~60 min remaining) |
| **Backend (FastAPI)** | ⬜ Not started — next major build phase |
| **Flutter App** | ⬜ Not started |

---

## 2. Repository Structure

```
/Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/
├── current_steps.md                    # Step-by-step checklist
├── init.md / init_v1.md                # Original project specs
├── master_plan/                        # Design docs (read these first!)
│   ├── README.md                       # Architecture overview & principles
│   ├── 01_law_corpus_agent_prompt.md   # Corpus pipeline agent spec
│   ├── 02_backend_system_prompt.md     # FastAPI backend spec (863 lines!)
│   └── 03_design_system_prompt.md      # Flutter UI/design system spec
│
└── law_corpus/                         # THE ACTIVE WORK AREA
    ├── .env                            # Environment config (GCP creds active)
    ├── pyproject.toml                  # Python project config
    ├── Dockerfile / docker-compose.yml
    ├── pipeline/                       # Python pipeline package
    │   ├── main.py                     # CLI entry point (Typer)
    │   ├── config.py                   # Pydantic Settings (all config)
    │   ├── scraper/                    # Downloads from matsne.gov.ge
    │   ├── parser/                     # HTML → structured LegalDocument
    │   ├── chunker/                    # Document → LegalChunks (by article)
    │   ├── embedder/                   # Gemini embedding via google-genai SDK
    │   │   ├── vertex_embedder.py      # Wrapper: supports Vertex AI ADC + API key auth
    │   │   ├── batch_embedder.py       # Sequential batches, retry, caching, checkpointing
    │   │   └── embedding_cache.py      # File-backed dedup cache
    │   ├── indexer/                    # ChromaDB / Vertex AI Vector Search
    │   │   ├── vector_store_indexer.py # Writes to ChromaDB (dev) or Vertex (prod)
    │   │   ├── search_index_builder.py # JSON inverted index for hybrid search
    │   │   └── metadata_indexer.py     # Metadata-based lookup indices
    │   ├── models/                     # Pydantic data models
    │   │   ├── legal_chunk.py          # LegalChunk — the atomic embedding unit
    │   │   ├── legal_document.py       # Parsed document model
    │   │   ├── legal_article.py        # Article within a document
    │   │   ├── document_metadata.py    # Source provenance metadata
    │   │   └── scrape_result.py        # Raw scrape output model
    │   └── utils/                      # Logger, progress tracker
    │
    └── data/                           # All pipeline data (gitignored)
        ├── raw/html/                   # Downloaded HTML from matsne.gov.ge
        ├── raw/metadata/              # Scrape metadata per document
        ├── parsed/                     # Parsed JSON (LegalDocument)
        ├── chunks/                     # Chunked JSON (list[LegalChunk])
        ├── embeddings/                 # Cached embedding vectors (.emb.json)
        ├── checkpoints/               # Resume state for each pipeline stage
        ├── chroma/                     # ChromaDB persistent storage
        └── index/                      # JSON inverted indices
```

---

## 3. Pipeline Stages (scrape → parse → chunk → embed → index)

### Stage 1: Scrape ✅ DONE
- **Command:** `python -m pipeline.main scrape`
- **Source:** [matsne.gov.ge](https://matsne.gov.ge) (official Georgian legislation portal)
- **Output:** `data/raw/html/*.html` + `data/raw/metadata/*.json`

### Stage 2: Parse ✅ DONE
- **Command:** `python -m pipeline.main parse`
- **Output:** `data/parsed/*.json` — Structured `LegalDocument` models

### Stage 3: Chunk ✅ DONE
- **Command:** `python -m pipeline.main chunk`
- **Output:** `data/chunks/*.json` — Lists of `LegalChunk` objects
- **Total: 9,450 chunks across 12 documents:**

| Document | Chunks | Description |
|----------|--------|-------------|
| `admin_offences_code` | 365 | Administrative offences |
| `admin_procedure_code` | 79 | Administrative procedure |
| `civil_code` | 2,285 | Civil law (largest) |
| `civil_procedure_code` | 780 | Civil procedure |
| `constitution` | 228 | Georgian Constitution |
| `criminal_code` | 874 | Criminal code |
| `criminal_procedure_code` | 1,078 | Criminal procedure |
| `election_code` | 1,156 | Election law |
| `general_admin_code` | 566 | General administrative code |
| `labour_code` | 140 | Labour law |
| `personal_data_law` | 180 | Data protection |
| `tax_code` | 1,719 | Tax code |

### Stage 4: Embed 🔄 IN PROGRESS
- **Command:** `python -m pipeline.main embed`
- **Model:** `gemini-embedding-001` via Vertex AI (768 dimensions, 3,072 native)
- **SDK:** `google-genai` (modern SDK — replaces deprecated `vertexai.language_models`)
- **Output:** `data/embeddings/*.emb.json` (one file per chunk)
- **Progress as of 06:25:** ~700 embeddings cached. Processing civil_code (2,285 chunks).
- **Rate limiting:** Vertex AI project quota limits to ~12 RPM, handled via sequential batches with 429 backoff + 60s cooldown
- **Estimated completion:** ~60 minutes from 06:25

### Stage 5: Index ⬜ NEXT
- **Command:** `python -m pipeline.main index --backend chroma`
- **What it does:**
  1. Loads all chunks from `data/chunks/*.json`
  2. Loads their embeddings from cache
  3. Upserts into ChromaDB (`data/chroma/`) with full metadata
  4. Builds JSON inverted indices (`data/index/`)
- **Expected time:** ~30 seconds

---

## 4. Key Data Model: LegalChunk

This is the atomic unit stored in ChromaDB. Every field matters for the RAG pipeline:

```python
class LegalChunk(BaseModel):
    chunk_id: str           # e.g. "civil_code_book_1_chapter_3_article_45_chunk_0"
    document_id: str        # e.g. "civil_code"
    content: str            # Full Georgian text for embedding
    content_ka: str         # Georgian text (may differ if header injected)
    content_en: str | None  # English translation (if available)

    # Structural metadata
    code_name: str          # e.g. "სამოქალაქო კოდექსი"
    book: str | None
    part: str | None
    chapter: str | None
    article_number: str     # e.g. "მუხლი 45"
    article_title: str | None
    paragraph_number: str | None

    # Source provenance (for AI citations)
    source_url: str         # Canonical matsne.gov.ge URL
    article_url: str        # Deep-link to specific article
    document_number: str    # Official registration number
    adoption_date: date | None
    citation_text: str      # Pre-formatted Georgian citation

    # Chunk position
    chunk_index: int
    total_chunks_in_article: int
    token_count: int

    # Legal metadata
    legal_domains: list[str]
    keywords_ka: list[str]
    keywords_en: list[str]
    cross_references: list[str]

    # Versioning
    effective_date: date | None
    last_updated: datetime | None
    is_current: bool

    # Embedding (populated by embedder, excluded from JSON by default)
    embedding: list[float] | None
    content_hash: str | None   # SHA-256 for change detection
```

---

## 5. Embedding Infrastructure Details

### Vertex AI Configuration
- **Project:** `gen-lang-client-0225498420`
- **Region:** `us-central1`
- **Model:** `gemini-embedding-001` (via `google-genai` SDK)
- **Dimensions:** 768 (downscaled from native 3,072)
- **Auth:** `gcloud auth application-default login` (ADC)
- **SDK:** `google-genai` with `vertexai=True` (replaces deprecated `google-cloud-aiplatform`)

### Model Selection Rationale

| Model | Why chosen / rejected |
|-------|----------------------|
| ~~`text-embedding-005`~~ | **Deprecated** — legacy model, replaced by Gemini embedding family |
| ~~`gemini-embedding-2`~~ | **Best quality** but project quota limited to 50 RPM (locked, no increase available). Would take ~4 hours for 9,450 chunks. |
| ✅ **`gemini-embedding-001`** | **Production choice.** Same 3,072 native dimensions, excellent multilingual quality, UNLIMITED RPM on this project via regional endpoints. Batched embedding (50 texts/call). Completes in ~60 minutes. |

### Rate Limiting Strategy
The project's actual Vertex AI quota is ~12 RPM for embedding calls. We implemented:

1. **Sequential batch processing** — 50 chunks per API call (batched embedding, 1 call returns 50 vectors)
2. **5-second delay** between batch requests (~12 RPM)
3. **Exponential backoff** on 429 errors with 60-second cooldown (quota resets per minute)
4. **5 retries** per batch before marking as failed
5. **Per-chunk caching** — `EmbeddingCache` stores each vector as individual `.emb.json` file
6. **Checkpoint tracking** — `ProgressTracker` records completed chunk IDs, enabling crash-safe resume
7. **Periodic checkpoints** — saves every 20 successful batches

> **File:** `law_corpus/pipeline/embedder/batch_embedder.py`

### Embedding Cache Layout
```
data/embeddings/
├── _cache_index.json                              # Maps "chunk_id:content_hash" → filename
├── civil_code_book_1_chapter_1_article_1_chunk_0.emb.json   # Raw float array
├── civil_code_book_1_chapter_1_article_2_chunk_0.emb.json
└── ... (growing — 9,450 files when complete)
```

---

## 6. ChromaDB Index Configuration
- **Collection name:** `georgian_laws`
- **Distance metric:** cosine
- **Persist directory:** `data/chroma/`
- **Metadata stored per chunk:** document_id, code_name, article_number, article_title, book, chapter, chunk_index, token_count, is_current, content_hash, source_url, article_url, document_number, adoption_date, citation_text

---

## 7. What Comes After Indexing

### 7a. Validate & Stats
```bash
python -m pipeline.main validate   # Checks P0/P1 law completeness
python -m pipeline.main stats      # Displays corpus statistics table
```

### 7b. Build the Backend (see `master_plan/02_backend_system_prompt.md`)

The backend is a **FastAPI application** with these key services:

1. **RAG Pipeline (5 stages):**
   ```
   User Message
     → [0] AI Query Expansion (Gemini generates Georgian legal search terms)
     → [1] Multi-Query Vector Search (top-50 per query via ChromaDB)
     → [2] Multi-Query Full-Text Search (top-50 per query)
     → [3] Merge & Deduplicate all results
     → [4] Gemini Rerank (select top-20 most relevant)
     → Return chunks with full metadata
   ```

2. **Legal Analysis Engine:** Gemini 3.1 Pro (via Vertex AI) with a specialized Georgian legal expert system prompt
3. **Query Embedding:** Uses `gemini-embedding-001` (same model as corpus) with `task_type="RETRIEVAL_QUERY"` for search
4. **Credit System:** FREE (5/day), PRO (purchased), ADMIN (10,000)
5. **Firebase Auth** for user management
6. **Conversation Orchestrator** with intake flow and multi-turn context

### 7c. Flutter App (see `master_plan/03_design_system_prompt.md`)

---

## 8. Environment & Dependencies

### .env (active values)
```env
GOOGLE_CLOUD_PROJECT=gen-lang-client-0225498420
GOOGLE_CLOUD_LOCATION=us-central1
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768
VECTOR_STORE_BACKEND=chroma
CHROMA_PERSIST_DIR=./data/chroma
DATA_DIR=./data
CHECKPOINT_DIR=./data/checkpoints
LOG_LEVEL=INFO
```

### Python environment
- Python 3.11 (Homebrew)
- Virtual env: `law_corpus/.venv`
- Key packages: `google-genai`, `chromadb`, `pydantic`, `pydantic-settings`, `typer`, `rich`, `orjson`, `httpx`

### GCP Auth
```bash
gcloud auth application-default login
# Quota project: gen-lang-client-0225498420
```

---

## 9. Known Issues & Gotchas

| Issue | Resolution |
|-------|------------|
| `gemini-embedding-2` returns 404 on `us-central1` | This model uses **global endpoints** (`location="us"`, not `us-central1`). The code auto-routes in `vertex_embedder.py`. However, project quota is only 50 RPM — switched to `gemini-embedding-001` instead. |
| `gemini-embedding-2` quota locked at 50 RPM | Cannot increase via console. GCP says "not eligible for increase at this time". Using `gemini-embedding-001` with unlimited regional RPM instead. |
| `gemini-embedding-2` returns 1 embedding for batched input | This model treats `contents=["a","b"]` as ONE multi-part content → 1 embedding. Must call per-text. Handled in `vertex_embedder.py` with model detection. |
| Vertex AI SDK deprecation | Legacy `google-cloud-aiplatform` deprecated June 2026. Migrated to `google-genai` SDK. |
| `Compute Engine Metadata server unavailable` | Expected when running locally (not on GCE). ADC handles auth instead. |
| 429 rate limit errors | Sequential batches with 5s delay + 60s cooldown on 429. Project quota is ~12 RPM. |
| `embedding` field excluded from JSON | `LegalChunk.embedding` has `exclude=True`. The indexer must load embeddings from cache separately. |

---

## 10. Immediate Action Items

### 🔄 Currently Running
```bash
python -m pipeline.main embed
# Running in: /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/law_corpus
# Model: gemini-embedding-001 | Batch size: 50 | Sequential with 429 recovery
```

### ⏭️ After Embed Completes
```bash
# 1. Index into ChromaDB
python -m pipeline.main index --backend chroma

# 2. Validate completeness
python -m pipeline.main validate
python -m pipeline.main stats
```

### 🔜 Then Build Backend
The backend spec is fully defined in `master_plan/02_backend_system_prompt.md` (863 lines). Key entry point:
- Create `backend/` directory at the project root
- FastAPI app with routes, services, repositories
- Wire up ChromaDB for RAG retrieval
- Integrate Gemini 3.1 Pro for legal analysis
- Use `gemini-embedding-001` for query embedding (same model as corpus)
- Firebase Auth + credit system

---

## 11. Critical File Quick Reference

| Purpose | Path |
|---------|------|
| **CLI entry point** | `law_corpus/pipeline/main.py` |
| **All settings** | `law_corpus/pipeline/config.py` |
| **Batch embedder** (sequential + retry) | `law_corpus/pipeline/embedder/batch_embedder.py` |
| **Gemini embedding wrapper** | `law_corpus/pipeline/embedder/vertex_embedder.py` |
| **Embedding cache** | `law_corpus/pipeline/embedder/embedding_cache.py` |
| **ChromaDB indexer** | `law_corpus/pipeline/indexer/vector_store_indexer.py` |
| **Search index builder** | `law_corpus/pipeline/indexer/search_index_builder.py` |
| **Chunk data model** | `law_corpus/pipeline/models/legal_chunk.py` |
| **Environment config** | `law_corpus/.env` |
| **Backend spec** | `master_plan/02_backend_system_prompt.md` |
| **Design spec** | `master_plan/03_design_system_prompt.md` |
| **Architecture overview** | `master_plan/README.md` |

---

## 12. Index Command Deep Dive

When `embed` finishes, the `index` command does this:

```python
# pipeline/main.py lines 191-216
def index(backend="chroma"):
    indexer = VectorStoreIndexer(backend=store_backend)
    search_builder = SearchIndexBuilder()
    all_chunks: list[LegalChunk] = []

    for json_file in sorted(settings.chunks_dir.glob("*.json")):
        raw = orjson.loads(json_file.read_bytes())
        chunks = [LegalChunk.model_validate(c) for c in raw]
        all_chunks.extend(chunks)

    count = indexer.index_chunks(all_chunks)        # → ChromaDB upsert
    search_builder.build(all_chunks)                 # → JSON inverted indices
```

> **⚠️ IMPORTANT:**
> The `index` command loads chunks from `data/chunks/` (not `data/embeddings/`).
> The `LegalChunk.embedding` field has `exclude=True`, so chunk JSON files do NOT contain embeddings.
> The indexer needs to load embeddings from the cache separately, OR the embed stage needs to
> populate the embedding field before index runs. Currently, `embed` runs first and populates
> `chunk.embedding` in memory, but `index` is a separate CLI command that reloads from disk.
>
> **This means the index command must also load embeddings from the cache.** Verify this works
> correctly before proceeding — you may need to modify the index command to load cached embeddings.
