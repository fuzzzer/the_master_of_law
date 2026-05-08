# Law Corpus Documentation

> **Last updated:** 2026-05-09
> **Location:** `law_corpus/`
> **Status:** Complete — DO NOT MODIFY directly

---

## What Legal Sources Are Included

The corpus covers three types of legal sources, totaling **20,712 chunks** across **3 ChromaDB collections**.

### 1. Georgian Legal Codes (`georgian_laws`)
**15,338 chunks** — 12 legal codes scraped from [matsne.gov.ge](https://matsne.gov.ge) (საქართველოს საკანონმდებლო მაცნე / Legislative Herald of Georgia).

| # | Code | Georgian Name | Approx. Articles |
|---|------|--------------|------------------|
| 1 | Constitution of Georgia | საქართველოს კონსტიტუცია | ~80 |
| 2 | Civil Code | სამოქალაქო კოდექსი | ~1,500 |
| 3 | Criminal Code | სისხლის სამართლის კოდექსი | ~420 |
| 4 | Code of Civil Procedure | სამოქალაქო საპროცესო კოდექსი | ~430 |
| 5 | Code of Criminal Procedure | სისხლის სამართლის საპროცესო კოდექსი | ~350 |
| 6 | Administrative Offences Code | ადმინისტრაციულ სამართალდარღვევათა კოდექსი | ~300 |
| 7 | General Administrative Code | ზოგადი ადმინისტრაციული კოდექსი | ~220 |
| 8 | Administrative Procedure Code | ადმინისტრაციული საპროცესო კოდექსი | ~250 |
| 9 | Tax Code | საგადასახადო კოდექსი | ~310 |
| 10 | Labour Code | შრომის კოდექსი | ~80 |
| 11 | Juvenile Justice Code | სს სამართალწარმოების კოდექსი | — |
| 12 | Entrepreneurial Law | მეწარმეთა შესახებ საქართველოს კანონი | ~100 |

### 2. Supreme Court Practice (`court_practice`)
**5,197 chunks** — Rulings from the Supreme Court of Georgia (2022–2026), covering criminal, civil, and administrative cases.

Metadata per chunk: `case_id`, `category` (criminal/civil/administrative), `year`, `section`, `chunk_index`.

### 3. Grand Chamber Decisions (`grand_chamber`)
**177 chunks** — Binding decisions from the Grand Chamber of the Supreme Court.

Metadata per chunk: `case_id`, `category`, `year`, `norm_interpreted`, `binding_rule`, `section`.

> **Note:** Grand Chamber decisions are **binding** and override all lower court interpretations.

---

## How Scraping Works

### Primary Source: matsne.gov.ge

The pipeline scrapes the official Legislative Herald of Georgia portal:

```
https://matsne.gov.ge
```

Operated by LEPL under the Ministry of Justice. No official public API exists. Data is obtained via respectful web scraping.

### Scraping Rules

- **Minimum delay:** 2 seconds between requests
- **Backoff:** Exponential on errors (2s → 4s → 8s → 16s → max 60s)
- **User-Agent:** Proper identification string
- **Caching:** ALL responses cached locally to minimize repeat requests
- **Resumable:** Progress tracked; can restart from last position

### Scraping Strategies

1. **Direct Web Scraping** — Navigate hierarchical law index, download consolidated (კონსოლიდირებული) versions
2. **PDF Downloads** — Fallback for documents where HTML parsing fails
3. **Open Data Portal** — Check [data.gov.ge](https://data.gov.ge) for structured datasets
4. **Manual Seed Data** — Curated `seed_laws.json` with URLs to critical laws

### Code Structure Extracted

Georgian legal documents follow a strict hierarchy:

```
კოდექსი (Code)
  └── წიგნი (Book)
       └── კარი (Part/Title)
            └── თავი (Chapter)
                 └── მუხლი (Article) ← PRIMARY UNIT
                      └── პუნქტი (Paragraph/Point)
                           └── ქვეპუნქტი (Sub-point)
```

The scraper preserves this hierarchy and assigns unique IDs (e.g., `civil_code.book_1.chapter_3.article_45.paragraph_2`).

---

## How Chunking Works

### Philosophy

**DO NOT use naive text splitting** (e.g., split every 500 tokens). Legal text requires structure-aware chunking.

### Chunking Strategy

1. **Article-level chunks (PRIMARY)** — Each `მუხლი` (article) becomes one chunk
   - If an article exceeds 1000 tokens, split at `პუნქტი` (paragraph) boundaries
   - If a single paragraph exceeds 1000 tokens, split at sentence boundaries with overlap

2. **Contextual header injection** — Every chunk includes:
   - Full hierarchical path (Code → Book → Chapter → Article)
   - Article number and title
   - Document metadata (name, adoption date)

3. **Cross-reference chunks** — When an article references another:
   - Create a supplementary chunk with both referencing and referenced articles

4. **Overlap strategy:**
   - 10-15% overlap between adjacent chunks within the same chapter
   - Include preceding article's number/title as context

### Chunk Model

Each chunk is a `LegalChunk` with fields:
- `chunk_id` — Unique identifier
- `content` / `content_ka` — Georgian text
- `code_name`, `book`, `part`, `chapter`, `article_number`, `article_title`
- `chunk_index`, `total_chunks_in_article`, `token_count`
- `legal_domains`, `keywords_ka`, `keywords_en`, `cross_references`
- `effective_date`, `last_updated`, `is_current`

---

## How Embeddings Are Generated

### Model Configuration

| Setting | Value |
|---------|-------|
| Model | `gemini-embedding-001` |
| Dimensions | 768 (downscaled from native 3,072) |
| Task type (corpus) | `RETRIEVAL_DOCUMENT` |
| Task type (queries) | `RETRIEVAL_QUERY` |
| Batch size | 100 (Vertex AI limit: 250/request) |

### Critical Rule

**Query embeddings MUST use `RETRIEVAL_QUERY`. Corpus embeddings use `RETRIEVAL_DOCUMENT`.** Mismatched task types severely degrade retrieval quality.

### Batch Processing

```python
# Process embeddings in batches of 100
# Rate limit: max 600 requests/minute for embedding API
# Cache all embeddings locally (keyed by chunk_id + content_hash)
# Checkpoint every 100 batches
# Resume from last checkpoint on failure
```

### Cost Tracking

Embedding costs are logged per batch:
```
input_tokens × pricing = cost_per_batch
```

---

## How to Add a New Legal Source

### Step 1: Source Discovery

Identify the source URL and document type:
- `code` — Legal code
- `organic_law` — Requires supermajority
- `law` — Regular parliamentary legislation
- `decree` — Presidential decree
- `resolution` — Government resolution

### Step 2: Add to Pipeline Config

Add the source to `law_corpus/pipeline/config.py` or `seed_laws.json`:

```json
{
  "title_ka": "ახალი კანონის სახელი",
  "title_en": "New Law Name",
  "source_url": "https://matsne.gov.ge/...",
  "document_type": "law",
  "priority": "P1"
}
```

### Step 3: Run Pipeline Stages

```bash
cd law_corpus
source .venv/bin/activate

# Stage 1: Scrape
python -m pipeline.main scrape --source matsne --laws new_law

# Stage 2: Parse
python -m pipeline.main parse --input-dir data/raw

# Stage 3: Chunk
python -m pipeline.main chunk --input-dir data/parsed

# Stage 4: Embed
python -m pipeline.main embed --input-dir data/chunks

# Stage 5: Index
python -m pipeline.main index --backend chroma
```

### Step 4: Validate

```bash
python -m pipeline.main validate
python -m pipeline.main stats
```

### Step 5: Update Backend

1. Update `app/integrations/chroma_client.py` collection metadata if needed
2. Update `docs/LAW_CORPUS.md` with the new source
3. Update `docs/API.md` collection counts
4. Restart backend: `docker compose restart api`

---

## How to Re-embed the Corpus

### Full Re-embed (all collections)

```bash
cd law_corpus
source .venv/bin/activate

# Regenerate embeddings from existing chunks
python -m pipeline.main embed --input-dir data/chunks --force

# Re-index to ChromaDB
python -m pipeline.main index --backend chroma --force
```

### Single Collection Re-embed

```bash
# TBD — current pipeline indexes all collections together
# For targeted updates, use the embedder module directly:
python -c "
from pipeline.embedder.vertex_embedder import VertexEmbedder
from pipeline.indexer.vector_store_indexer import ChromaIndexer
# ... custom logic
"
```

---

## Data Quality Guarantees

### Completeness
- **P0 laws:** 100% included before backend deployment
- **P1 laws:** ≥95% included
- All article numbers, cross-references, and hierarchical paths verified against source

### Accuracy
- Consolidated (current) versions only — all amendments merged
- Amendment history stored as metadata
- Repealed articles flagged (`is_current = false`)

### Freshness
- Pipeline supports incremental updates (`--since YYYY-MM-DD`)
- Recommended: monthly update check for new amendments

### Resilience
- Pipeline is fully resumable at every stage
- Crash at any stage does not require restarting from scratch
- Backups created before destructive operations

### Verification Process

```bash
# Run validation script
python -m pipeline.main validate

# Expected output:
# - Total documents scraped: N
# - Total articles parsed: N
# - Total chunks generated: N
# - Total embeddings created: N
# - Coverage by legal domain: {...}
# - Errors and warnings: [...]
```

---

## Metadata Reference

### `georgian_laws` Collection Metadata

| Field | Description | Example |
|-------|-------------|---------|
| `code_name` | Name of the legal code | `სამოქალაქო კოდექსი` |
| `article_number` | Article identifier | `მუხლი 45` |
| `article_title` | Article title | `ქონების უფლება` |
| `citation_text` | Full citation string | `სამოქალაქო კოდექსი, მუხლი 45` |
| `source_url` | URL to the code on matsne.gov.ge | `https://matsne.gov.ge/...` |
| `article_url` | URL to the specific article | `https://matsne.gov.ge/...` |
| `document_number` | Official document number | `0100lk` |

### `court_practice` Collection Metadata

| Field | Description | Example |
|-------|-------------|---------|
| `case_id` | Case identifier | `CRIM-1051ap-24` |
| `category` | Case type | `criminal`, `civil`, `administrative` |
| `year` | Ruling year | `2024` |
| `section` | Document section | `facts`, `reasoning`, `resolution` |
| `chunk_index` | Position in case | `3` |

### `grand_chamber` Collection Metadata

| Field | Description | Example |
|-------|-------------|---------|
| `case_id` | Case identifier | `GC-2023-15` |
| `category` | Legal domain | `constitutional` |
| `year` | Decision year | `2023` |
| `norm_interpreted` | Law being interpreted | `Constitution, Article 42` |
| `binding_rule` | The binding legal rule | `The right to fair trial includes...` |
| `section` | Document section | `reasoning` |

---

## Querying the Corpus Directly

```python
import chromadb

client = chromadb.PersistentClient(path="law_corpus/data/chroma")

# List collections
print(client.list_collections())

# Query a collection
laws = client.get_collection("georgian_laws")
results = laws.query(
    query_embeddings=[embedding_vector],
    n_results=50,
    include=["documents", "metadatas", "distances"]
)
```

> **Gotcha:** ChromaDB uses SQLite with WAL mode. Even read-only queries may write journal files. Mount the chroma directory as `rw` in Docker, not `ro`.
