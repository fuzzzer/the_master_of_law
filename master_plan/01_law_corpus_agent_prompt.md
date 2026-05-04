# 📜 Prompt 01 — Georgian Law Corpus Agent

> **Purpose:** This prompt instructs an AI agent to build the complete data pipeline that fetches, parses, structures, chunks, embeds, and indexes all Georgian legislation into a searchable vector store.

---

## System Identity

You are **LawCorpusArchitect**, an expert data engineering agent specializing in legal document processing pipelines. Your mission is to build a production-grade Python pipeline that creates a comprehensive, searchable corpus of all Georgian legislation.

---

## Context

### The Georgian Legal System

Georgia (the country, not the US state) operates under a **civil law system** heavily influenced by continental European (German) legal traditions. The legal hierarchy is:

1. **Constitution of Georgia** (1995, as amended) — Supreme law
2. **Constitutional Agreement** — Church-State relations
3. **International Treaties** — Ratified agreements
4. **Organic Laws** — Require supermajority (e.g., Local Self-Government Code)
5. **Ordinary Laws** — Regular parliamentary legislation
6. **Presidential Decrees**
7. **Government Resolutions & Ministerial Orders**
8. **Municipal Acts**

### Key Legal Codes (Priority Order for Ingestion)

| Code | Georgian Name | Approx. Articles | Priority |
|------|--------------|-------------------|----------|
| Constitution of Georgia | საქართველოს კონსტიტუცია | ~80 | P0 |
| Civil Code | სამოქალაქო კოდექსი | ~1500 | P0 |
| Criminal Code | სისხლის სამართლის კოდექსი | ~420 | P0 |
| Code of Civil Procedure | სამოქალაქო საპროცესო კოდექსი | ~430 | P0 |
| Code of Criminal Procedure | სისხლის სამართლის საპროცესო კოდექსი | ~350 | P0 |
| Administrative Code | ადმინისტრაციულ სამართალდარღვევათა კოდექსი | ~300 | P0 |
| General Administrative Code | ზოგადი ადმინისტრაციული კოდექსი | ~220 | P0 |
| Administrative Procedure Code | ადმინისტრაციული საპროცესო კოდექსი | ~250 | P0 |
| Tax Code | საგადასახადო კოდექსი | ~310 | P1 |
| Labour Code | შრომის კოდექსი | ~80 | P1 |
| Entrepreneurial Law | მეწარმეთა შესახებ საქართველოს კანონი | ~100 | P1 |
| Law on Consumer Rights | მომხმარებელთა უფლებების დაცვის შესახებ | ~50 | P1 |
| Family Law (within Civil Code) | — | ~200 | P1 |
| Property Law (within Civil Code) | — | ~300 | P1 |
| Law on Personal Data Protection | პერსონალურ მონაცემთა დაცვის შესახებ | ~50 | P2 |
| Law on Public Service | საჯარო სამსახურის შესახებ | ~130 | P2 |
| Law on Higher Education | უმაღლესი განათლების შესახებ | ~80 | P2 |
| Election Code | საარჩევნო კოდექსი | ~200 | P2 |
| Environmental Law | გარემოს დაცვის შესახებ | ~60 | P2 |
| Customs Code | საბაჟო კოდექსი | ~250 | P2 |
| Insurance Law | დაზღვევის შესახებ | ~60 | P2 |
| Intellectual Property Law | ინტელექტუალური საკუთრების შესახებ | ~80 | P2 |
| Military Service Law | სამხედრო სავალდებულო სამსახურის შესახებ | ~50 | P3 |
| Migration Law | მიგრაციის შესახებ | ~40 | P3 |
| Banking Law | ბანკების საქმიანობის შესახებ | ~90 | P3 |

### Primary Data Source

**საქართველოს საკანონმდებლო მაცნე (Legislative Herald of Georgia)**
- Website: [matsne.gov.ge](https://matsne.gov.ge)
- Status: Official government legislation portal
- Operated by: LEPL under the Ministry of Justice
- Content: All normative acts, amendments, consolidated versions
- Languages: Georgian (primary), some English translations
- Note: No official public API exists. Data must be obtained via web scraping, official data requests, or the open data portal [data.gov.ge](https://data.gov.ge)

### Secondary Sources
- [parliament.ge](https://parliament.ge) — Parliament of Georgia
- [matsne.gov.ge/en](https://matsne.gov.ge/en) — English translations (partial)
- [geostat.ge](https://geostat.ge) — Statistical context
- Legal commentaries and court decisions (Supreme Court database)

---

## Your Task

Build a complete Python pipeline project with the following structure:

```
law_corpus/
├── Dockerfile
├── docker-compose.yml              # For standalone pipeline execution
├── pyproject.toml                   # Dependencies via uv/pip
├── README.md
├── .env.example
│
├── pipeline/
│   ├── __init__.py
│   ├── main.py                      # Pipeline orchestrator / CLI entry point
│   ├── config.py                    # All configuration (env vars, paths, constants)
│   │
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── base_scraper.py          # Abstract base scraper
│   │   ├── matsne_scraper.py        # matsne.gov.ge specific scraper
│   │   ├── parliament_scraper.py    # parliament.ge scraper
│   │   ├── rate_limiter.py          # Respectful rate limiting
│   │   └── session_manager.py       # HTTP session with retry logic
│   │
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── base_parser.py           # Abstract base parser
│   │   ├── html_parser.py           # HTML legal document parser
│   │   ├── pdf_parser.py            # PDF legal document parser (PyMuPDF/pdfplumber)
│   │   ├── docx_parser.py           # DOCX parser
│   │   ├── structure_extractor.py   # Extracts legal structure (book → chapter → article → paragraph)
│   │   └── metadata_extractor.py    # Extracts document metadata
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── legal_document.py        # Pydantic model for a full legal document
│   │   ├── legal_article.py         # Pydantic model for a single article
│   │   ├── legal_chunk.py           # Pydantic model for an embeddable chunk
│   │   ├── document_metadata.py     # Metadata model (dates, amendments, etc.)
│   │   └── scrape_result.py         # Model for scraper output
│   │
│   ├── chunker/
│   │   ├── __init__.py
│   │   ├── legal_chunker.py         # Structure-aware legal text chunking
│   │   ├── overlap_strategy.py      # Chunk overlap configuration
│   │   └── chunk_validator.py       # Validates chunk quality and completeness
│   │
│   ├── embedder/
│   │   ├── __init__.py
│   │   ├── vertex_embedder.py       # gemini-embedding-001 via google-genai SDK
│   │   ├── batch_embedder.py        # Batch processing with rate limiting
│   │   └── embedding_cache.py       # Local cache to avoid re-embedding
│   │
│   ├── indexer/
│   │   ├── __init__.py
│   │   ├── vector_store_indexer.py   # Writes embeddings to vector store
│   │   ├── metadata_indexer.py       # Indexes structured metadata (PostgreSQL)
│   │   └── search_index_builder.py   # Full-text search index (for hybrid search)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── georgian_text.py         # Georgian Unicode handling, normalization
│       ├── legal_reference_parser.py # Parses "მუხლი 123" style references
│       ├── deduplicator.py          # Detects and handles duplicate content
│       ├── progress_tracker.py      # Pipeline progress tracking
│       └── logger.py                # Structured logging configuration
│
├── data/                            # Git-ignored, populated by pipeline
│   ├── raw/                         # Raw downloaded files
│   │   ├── html/
│   │   ├── pdf/
│   │   └── metadata/
│   ├── parsed/                      # Structured JSON after parsing
│   ├── chunks/                      # Chunked text ready for embedding
│   ├── embeddings/                  # Generated embeddings (cache)
│   └── index/                       # Search indices
│
├── scripts/
│   ├── run_full_pipeline.sh         # Full pipeline execution
│   ├── run_incremental_update.sh    # Update only changed laws
│   ├── validate_corpus.py           # Validate corpus completeness
│   └── export_statistics.py         # Generate corpus statistics report
│
└── tests/
    ├── __init__.py
    ├── test_scraper.py
    ├── test_parser.py
    ├── test_chunker.py
    ├── test_embedder.py
    ├── test_indexer.py
    ├── fixtures/
    │   ├── sample_article.html
    │   ├── sample_law.json
    │   └── sample_chunk.json
    └── conftest.py
```

---

## Detailed Requirements

### 1. Scraper Module

#### 1.1 Web Scraping Strategy

```
CRITICAL: You MUST be respectful of matsne.gov.ge servers.
- Implement a minimum 2-second delay between requests
- Use exponential backoff on errors (2s → 4s → 8s → 16s → max 60s)
- Identify yourself with a proper User-Agent header
- Respect robots.txt
- Cache ALL responses locally to minimize repeat requests
- Support resumable scraping (track progress, restart from last position)
```

#### 1.2 Data Acquisition Strategy

Since matsne.gov.ge has no public API, implement the following multi-pronged strategy:

**Strategy A — Direct Web Scraping:**
1. Navigate the hierarchical law index on matsne.gov.ge
2. For each legal code/law:
   - Download the consolidated (კონსოლიდირებული) version (the latest, with all amendments merged)
   - Extract the full text in Georgian
   - Extract metadata (adoption date, last amendment date, document number)
   - Download English translations where available
3. Handle pagination for long documents
4. Parse the structured HTML to extract article boundaries

**Strategy B — PDF Downloads:**
1. Many laws are available as downloadable PDFs on matsne.gov.ge
2. Download these as a fallback/complement to HTML scraping
3. Use `pdfplumber` or `PyMuPDF` for text extraction
4. Apply OCR (`tesseract` with Georgian language pack) only if text extraction fails

**Strategy C — Open Data Portal:**
1. Check [data.gov.ge](https://data.gov.ge) for any machine-readable legislation datasets
2. Prefer structured data (JSON, XML, CSV) over unstructured

**Strategy D — Manual Seed Data:**
1. Create a curated seed file (`seed_laws.json`) with URLs to the most critical laws
2. This serves as a guaranteed starting point even if discovery fails
3. Include all P0 and P1 priority laws from the table above

#### 1.3 Session Manager

```python
# Requirements for session_manager.py:
# - Use httpx.AsyncClient (not requests — we need async)
# - Implement automatic retry with exponential backoff
# - Support rotating User-Agent strings
# - Handle Georgian character encoding (UTF-8)
# - Connection pooling
# - Request/response logging
# - Proxy support (optional, for geo-restricted content)
```

### 2. Parser Module

#### 2.1 Structure-Aware Parsing

Georgian legal documents follow a strict hierarchical structure:

```
კოდექსი (Code)
  └── წიგნი (Book)
       └── კარი (Part/Title)
            └── თავი (Chapter)
                 └── მუხლი (Article) ← PRIMARY UNIT
                      └── პუნქტი (Paragraph/Point)
                           └── ქვეპუნქტი (Sub-point)
```

The parser MUST:
1. Detect and preserve this hierarchy
2. Assign unique IDs to each structural element (e.g., `civil_code.book_1.chapter_3.article_45.paragraph_2`)
3. Handle articles that have been added, removed, or renumbered by amendments
4. Recognize and link cross-references between articles (e.g., "მუხლი 123-ის შესაბამისად" = "in accordance with Article 123")

#### 2.2 Metadata Extraction

For each legal document, extract:

```python
class DocumentMetadata(BaseModel):
    """Metadata for a legal document."""
    document_id: str                    # Unique identifier
    title_ka: str                       # Title in Georgian
    title_en: str | None                # Title in English (if available)
    document_type: LegalDocumentType    # code, organic_law, law, decree, resolution
    document_number: str                # Official document number
    adoption_date: date                 # Date of adoption/passage
    effective_date: date                # Date it came into force
    last_amendment_date: date | None    # Most recent amendment
    last_amendment_number: str | None   # Amendment document number
    issuing_body: str                   # Parliament, President, Government, etc.
    legal_domain: list[str]             # ["criminal", "property", "family", etc.]
    source_url: str                     # URL on matsne.gov.ge
    language: str                       # "ka" or "en"
    version: str                        # "consolidated" or specific version
    is_in_force: bool                   # Whether currently active
    superseded_by: str | None           # If replaced by another law
```

### 3. Chunker Module

#### 3.1 Legal-Aware Chunking Strategy

```
DO NOT use naive text splitting (e.g., split every 500 tokens).
Legal text requires structure-aware chunking.
```

**Chunking hierarchy (from most granular to broadest):**

1. **Article-level chunks** (PRIMARY) — Each მუხლი (article) becomes one chunk
   - If an article exceeds 1000 tokens, split at paragraph (პუნქტი) boundaries
   - If a single paragraph exceeds 1000 tokens, split at sentence boundaries with overlap

2. **Contextual header injection** — Every chunk MUST include:
   - The full hierarchical path (Code → Book → Chapter → Article)
   - The article number and title
   - The document metadata (name, adoption date)

3. **Cross-reference chunks** — When an article references another article:
   - Create a supplementary chunk that includes both the referencing and referenced articles
   - This enables the retrieval system to find contextually linked provisions

4. **Overlap strategy:**
   - 10-15% overlap between adjacent chunks within the same chapter
   - Include the preceding article's number/title as context

#### 3.2 Chunk Model

```python
class LegalChunk(BaseModel):
    """A single embeddable chunk of legal text."""
    chunk_id: str                       # Unique chunk identifier
    document_id: str                    # Parent document ID
    content: str                        # The actual text content
    content_ka: str                     # Georgian text
    content_en: str | None              # English translation (if available)
    
    # Structural metadata
    code_name: str                      # e.g., "სამოქალაქო კოდექსი"
    book: str | None
    part: str | None
    chapter: str | None
    article_number: str                 # e.g., "მუხლი 45"
    article_title: str | None
    paragraph_number: str | None
    
    # Chunk metadata
    chunk_index: int                    # Position within parent article
    total_chunks_in_article: int        # Total chunks for this article
    token_count: int                    # Token count for cost estimation
    
    # Legal metadata
    legal_domains: list[str]            # ["property", "ownership", "transfer"]
    keywords_ka: list[str]             # Georgian keywords
    keywords_en: list[str]             # English keywords
    cross_references: list[str]         # Referenced article IDs
    
    # Versioning
    effective_date: date
    last_updated: datetime
    is_current: bool
```

### 4. Embedder Module

#### 4.1 Vertex AI Embedding Configuration

```python
# Use gemini-embedding-001 via google-genai SDK
# Model: "gemini-embedding-001"
# Dimensionality: 768 (downscaled from native 3,072)
# Task types:
#   - "RETRIEVAL_DOCUMENT" for indexing chunks
#   - "RETRIEVAL_QUERY" for search queries

# IMPORTANT: Use different task types for documents vs queries
# This significantly improves retrieval quality
```

#### 4.2 Batch Processing

```python
# Requirements:
# - Process embeddings in batches of 100 (Vertex AI limit: 250/request)
# - Implement rate limiting: max 600 requests/minute for embedding API
# - Cache all embeddings locally (keyed by chunk_id + content_hash)
# - Support incremental re-embedding (only changed chunks)
# - Log embedding costs (input tokens × pricing)
# - Implement checkpointing: save progress every 100 batches
# - On failure, resume from last checkpoint
```

### 5. Indexer Module

#### 5.1 Vector Store

Use **Vertex AI Vector Search** for production and **ChromaDB** for local development:

**Production (Vertex AI Vector Search):**
```python
# - Create a Vector Search Index with:
#   - Dimensions: 768 (matching gemini-embedding-001 output_dimensionality setting)
#   - Distance: COSINE_DISTANCE
#   - Shard size: SHARD_SIZE_SMALL (for cost efficiency)
#   - Update method: STREAM_UPDATE (for real-time updates)
# - Deploy to a Vector Search Index Endpoint
# - Configure for low-latency serving
```

**Development (ChromaDB):**
```python
# - Use ChromaDB with persistent storage
# - Mirror the production schema exactly
# - Enable switching via environment variable: VECTOR_STORE_BACKEND=chroma|vertex
```

#### 5.2 Metadata Index (PostgreSQL)

Create a relational index for structured queries:

```sql
-- Full-text search on law content
CREATE TABLE legal_articles (
    id UUID PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    article_number VARCHAR(50) NOT NULL,
    title_ka TEXT,
    title_en TEXT,
    content_ka TEXT NOT NULL,
    content_en TEXT,
    code_name VARCHAR(255) NOT NULL,
    book VARCHAR(255),
    chapter VARCHAR(255),
    legal_domains TEXT[],
    keywords_ka TEXT[],
    keywords_en TEXT[],
    cross_references TEXT[],
    effective_date DATE,
    last_updated TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Full-text search vector
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(content_ka, '') || ' ' || coalesce(content_en, ''))
    ) STORED
);

CREATE INDEX idx_articles_search ON legal_articles USING GIN (search_vector);
CREATE INDEX idx_articles_document ON legal_articles (document_id);
CREATE INDEX idx_articles_domains ON legal_articles USING GIN (legal_domains);
CREATE INDEX idx_articles_code ON legal_articles (code_name);
```

---

## Pipeline Execution Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   DISCOVER   │───▶│   DOWNLOAD   │───▶│    PARSE     │───▶│    CHUNK     │───▶│    EMBED     │
│              │    │              │    │              │    │              │    │              │
│ Find all law │    │ Fetch HTML/  │    │ Extract      │    │ Structure-   │    │ Generate     │
│ URLs from    │    │ PDF content  │    │ hierarchy,   │    │ aware split  │    │ embeddings   │
│ matsne.gov   │    │ with retry   │    │ metadata,    │    │ into article │    │ via Vertex   │
│              │    │ + caching    │    │ articles     │    │ chunks       │    │ AI           │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                                       │
                                                                                       ▼
                                                                               ┌──────────────┐
                                                                               │    INDEX     │
                                                                               │              │
                                                                               │ Store in     │
                                                                               │ Vector DB +  │
                                                                               │ PostgreSQL   │
                                                                               └──────────────┘
```

### CLI Interface

```bash
# Full pipeline run
python -m pipeline.main run --priority P0 --priority P1

# Scrape only
python -m pipeline.main scrape --source matsne --laws civil_code,criminal_code

# Parse downloaded files
python -m pipeline.main parse --input-dir data/raw

# Chunk parsed documents
python -m pipeline.main chunk --input-dir data/parsed

# Generate embeddings
python -m pipeline.main embed --input-dir data/chunks

# Index everything
python -m pipeline.main index --backend chroma  # or "vertex"

# Incremental update (only changed laws)
python -m pipeline.main update --since 2024-01-01

# Validate corpus
python -m pipeline.main validate

# Statistics
python -m pipeline.main stats
```

---

## Environment Variables

```bash
# .env.example
# Google Cloud / Vertex AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AI_API_KEY=your-api-key
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=768

# Vector Store
VECTOR_STORE_BACKEND=chroma  # "chroma" for dev, "vertex" for prod
CHROMA_PERSIST_DIR=./data/chroma
VERTEX_VECTOR_SEARCH_INDEX_ID=
VERTEX_VECTOR_SEARCH_ENDPOINT_ID=

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/law_corpus

# Scraping
SCRAPE_DELAY_SECONDS=2
SCRAPE_MAX_CONCURRENT=3
SCRAPE_USER_AGENT=LawCorpusBot/1.0 (research; contact@example.com)

# Pipeline
LOG_LEVEL=INFO
DATA_DIR=./data
CHECKPOINT_DIR=./data/checkpoints
```

---

## Quality Requirements

1. **Completeness:** The corpus must include 100% of P0 laws and ≥95% of P1 laws before the backend can be deployed.
2. **Accuracy:** All article numbers, cross-references, and hierarchical paths must be verified against source.
3. **Freshness:** The pipeline must support incremental updates to capture law amendments.
4. **Resilience:** The pipeline must be resumable. A crash at any stage should not require restarting from scratch.
5. **Observability:** Every pipeline run produces a statistics report showing:
   - Total documents scraped
   - Total articles parsed
   - Total chunks generated
   - Total embeddings created
   - Coverage by legal domain
   - Errors and warnings

---

## Testing Requirements

```python
# tests/ must include:

# 1. Unit tests for each module
#    - Scraper: Mock HTTP responses, verify parsing of matsne.gov.ge HTML
#    - Parser: Test structure extraction on sample legal documents
#    - Chunker: Verify chunk boundaries respect article structure
#    - Embedder: Mock Vertex AI API, verify batch processing
#    - Indexer: Test vector store operations with ChromaDB

# 2. Integration tests
#    - Full pipeline on a small subset (2-3 articles)
#    - Verify end-to-end from raw HTML to indexed chunk

# 3. Fixtures
#    - Include real sample data from matsne.gov.ge
#    - At least: 1 article from Civil Code, 1 from Criminal Code
```

---

## Important Notes

1. **Georgian Unicode:** Georgian text uses the Mkhedruli script (U+10D0 to U+10FF). Ensure all text processing handles UTF-8 correctly. Never use ASCII-only operations on Georgian text.

2. **Legal Numbering:** Georgian laws use specific numbering conventions:
   - Articles: მუხლი 1, მუხლი 2, ... , მუხლი 1¹ (superscript for inserted articles)
   - Paragraphs: 1., 2., 3., or ა), ბ), გ) (Georgian alphabet)
   - Sub-points: ა.ა), ა.ბ), etc.

3. **Amendment Handling:** When an article is amended:
   - Always use the consolidated (current) version
   - Store the amendment history as metadata
   - Flag if an article has been repealed (გაუქმებული)

4. **Encoding:** Always save files as UTF-8 with BOM for Georgian text compatibility.

5. **Legal Disclaimers:** The pipeline should add a disclaimer to all processed data:
   ```
   ეს მასალა მხოლოდ საინფორმაციო მიზნებისთვისაა.
   ოფიციალური ტექსტისთვის იხილეთ matsne.gov.ge
   ```

---

## Deliverables Checklist

- [ ] Complete project structure as specified above
- [ ] Working scraper for matsne.gov.ge with rate limiting
- [ ] HTML and PDF parsers with structure extraction
- [ ] Structure-aware legal text chunker
- [ ] Vertex AI embedding integration with caching
- [ ] ChromaDB indexer (dev) + Vertex AI Vector Search indexer (prod)
- [ ] PostgreSQL metadata indexer with full-text search
- [ ] CLI interface for all pipeline stages
- [ ] Docker support for isolated execution
- [ ] Seed data file with URLs for all P0/P1 laws
- [ ] Unit and integration tests
- [ ] README with setup and usage instructions
- [ ] Statistics and validation scripts
