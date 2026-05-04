# 📜 Georgian Law Corpus Pipeline

Production-grade data pipeline that scrapes, parses, chunks, embeds, and indexes all Georgian legislation into a searchable vector store.

## Architecture

```
DISCOVER → DOWNLOAD → PARSE → CHUNK → EMBED → INDEX
  │           │          │        │        │       │
  │           │          │        │        │       ├─ ChromaDB (dev)
  │           │          │        │        │       ├─ Vertex AI Vector Search (prod)
  │           │          │        │        │       └─ PostgreSQL (metadata + FTS)
  │           │          │        │        │
  │           │          │        │        └─ gemini-embedding-001 (via google-genai SDK)
  │           │          │        │
  │           │          │        └─ Structure-aware legal chunking
  │           │          │
  │           │          └─ HTML/PDF/DOCX → Hierarchical legal structure
  │           │
  │           └─ HTTP with retry, rate limiting, caching
  │
  └─ Seed data + dynamic discovery from matsne.gov.ge
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16+ (for metadata/FTS)
- Google Cloud project with Vertex AI enabled (for embeddings)

### Installation

```bash
cd law_corpus

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

### Docker (recommended)

```bash
docker-compose up -d postgres   # Start PostgreSQL
docker-compose run pipeline run --priority P0   # Run pipeline
```

## CLI Commands

```bash
# Full pipeline run (scrape → parse → chunk → embed → index)
python -m pipeline.main run --priority P0 --priority P1

# Individual stages
python -m pipeline.main scrape --source matsne --priority P0
python -m pipeline.main parse
python -m pipeline.main chunk
python -m pipeline.main embed
python -m pipeline.main index --backend chroma

# Utilities
python -m pipeline.main stats       # Corpus statistics
python -m pipeline.main validate    # Completeness check
python -m pipeline.main update --since 2024-01-01  # Incremental
```

## Project Structure

```
law_corpus/
├── pipeline/
│   ├── main.py              # CLI entry point
│   ├── config.py             # Configuration (env vars)
│   ├── scraper/              # Web scraping (matsne.gov.ge)
│   ├── parser/               # HTML/PDF → structured legal docs
│   ├── models/               # Pydantic data models
│   ├── chunker/              # Structure-aware text splitting
│   ├── embedder/             # Vertex AI embedding generation
│   ├── indexer/              # Vector store + PostgreSQL indexing
│   └── utils/                # Georgian text, logging, progress
├── data/                     # Pipeline output (git-ignored)
├── scripts/                  # Shell scripts for execution
├── tests/                    # Unit + integration tests
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Georgian Legal Hierarchy

The pipeline respects the structural hierarchy of Georgian legislation:

```
კოდექსი (Code)
  └── წიგნი (Book)
       └── კარი (Part/Title)
            └── თავი (Chapter)
                 └── მუხლი (Article) ← PRIMARY UNIT
                      └── პუნქტი (Paragraph)
                           └── ქვეპუნქტი (Sub-point)
```

## Key Features

- **Structure-aware chunking**: Never splits mid-article; respects legal hierarchy
- **Contextual headers**: Every chunk includes its full path (Code → Book → Chapter → Article)
- **Cross-reference linking**: Detects and preserves "მუხლი 123"-style references
- **Resumable**: Crashes don't require restart — checkpoints save progress
- **Rate-limited**: Respects matsne.gov.ge with ≥2s delay between requests
- **Dual vector store**: ChromaDB (dev) ↔ Vertex AI Vector Search (prod)
- **Embedding cache**: SHA-256 based — never re-embeds unchanged content

## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=pipeline --cov-report=html
```

## Environment Variables

See `.env.example` for the full list. Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `VECTOR_STORE_BACKEND` | `chroma` or `vertex` | `chroma` |
| `EMBEDDING_MODEL` | Gemini embedding model | `gemini-embedding-001` |
| `SCRAPE_DELAY_SECONDS` | Min delay between requests | `2` |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI | — |

## Legal Disclaimer

ეს მასალა მხოლოდ საინფორმაციო მიზნებისთვისაა.
ოფიციალური ტექსტისთვის იხილეთ [matsne.gov.ge](https://matsne.gov.ge)
