# Current Steps — Law Corpus Pipeline Setup

> Use this as your checklist. Work through each task in order.
> GCP project is **NOT needed** until Step 5 (embed). Steps 1–4 are fully local.

---

## Task 1 — Install dependencies ✅

```bash
cd law_corpus
pip install -e ".[dev]"
```

**Done.** All packages installed successfully.

---

## Task 2 — Start PostgreSQL via Docker

```bash
cd law_corpus
docker compose up -d postgres
```

**What this does:** Starts a local PostgreSQL 16 container with:
- Database: `law_corpus`
- User: `corpus`
- Password: `corpus_dev_pw`
- Port: `5432` (mapped to localhost)

**Verify it's running:**
```bash
docker compose ps
# Should show postgres service as "Up"
```

**Try connecting (optional):**
```bash
docker compose exec postgres psql -U corpus -d law_corpus -c "SELECT 1;"
```

> **Is this safe?** Yes. The Docker PostgreSQL is bound to `localhost:5432` — it's NOT accessible from the internet. For <2 GB of law data on your local machine, this is perfectly fine. When you move to production with payments, you'd switch to a managed service (GCP Cloud SQL), but for now Docker is ideal.

> **PostgreSQL URL explained:**
> ```
> postgresql+asyncpg://corpus:corpus_dev_pw@localhost:5432/law_corpus
>                      ^^^^^^ ^^^^^^^^^^^^^^ ^^^^^^^^^:^^^^  ^^^^^^^^^^
>                      user   password       host     port   database
> ```
> - `asyncpg` = the async PostgreSQL driver Python uses
> - All these values come from `docker-compose.yml` — you don't need to configure anything extra
> - Think of it like SQLite but the "file path" is replaced by `user:pass@host:port/dbname`

**Status:** ⬜ Not started

---

## Task 3 — Set up `.env`

```bash
cd law_corpus
cp .env.example .env
```

Now edit `.env`. Since PostgreSQL is already running (Task 2), you know the URL:

```bash
# These work out of the box:
VECTOR_STORE_BACKEND=chroma
LOG_LEVEL=INFO
SCRAPE_DELAY_SECONDS=2

# PostgreSQL — matches docker-compose.yml exactly:
DATABASE_URL=postgresql+asyncpg://corpus:corpus_dev_pw@localhost:5432/law_corpus

# GCP — leave commented out, fill in before Task 5 (embed):
# GOOGLE_CLOUD_PROJECT=your-gcp-project-id
# GOOGLE_CLOUD_LOCATION=us-central1
```

> **You do NOT need GCP credentials for tasks 1–4.** Only the embed step calls Vertex AI.

**Status:** ⬜ Not started

---

## Task 4 — Scrape P0 + P1 laws

Scrape the 8 critical codes first (Constitution, Civil, Criminal, etc.):
```bash
cd law_corpus
python -m pipeline.main scrape --source matsne --priority P0
```

Then the 4 additional codes (Tax, Labour, etc.):
```bash
python -m pipeline.main scrape --priority P1
```

**What to expect:**
- ~19 HTTP requests total (one per law — downloads the full consolidated text)
- ~40 seconds with 2-second rate limiting between requests
- Raw HTML saved to `data/raw/html/`
- Metadata saved to `data/raw/metadata/`
- Total download: ~50–80 MB

**Troubleshooting:**
- If matsne.gov.ge is slow → scraper auto-backs off (2s → 4s → 8s → 60s max)
- If it crashes → re-run — the scraper skips already-downloaded files (resumable)

**Status:** ⬜ Not started

---

## Task 5 — Parse → Chunk → Embed → Index

Parse and chunk are local (no GCP needed):
```bash
python -m pipeline.main parse
python -m pipeline.main chunk
```

> ⚠️ **STOP HERE** if you haven't set up GCP. The next commands need Vertex AI.

**GCP setup (one-time, before embed):**
1. Create or select a GCP project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable the **Vertex AI API**
3. Run: `gcloud auth application-default login`
4. Add to `.env`:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   ```

Then embed and index:
```bash
python -m pipeline.main embed
python -m pipeline.main index --backend chroma
```

**What to expect:**
- Parse: ~30 seconds, produces JSON in `data/parsed/`
- Chunk: ~10 seconds, produces chunks in `data/chunks/`
- Embed: ~2–5 minutes (Vertex AI `text-embedding-005`), costs ~$0.06
- Index: ~30 seconds into ChromaDB at `data/chroma/`

**Status:** ⬜ Not started

---

## Task 6 — Validate

```bash
python -m pipeline.main validate
python -m pipeline.main stats
```

**Expected:** No P0 or P1 laws missing. Stats show raw, parsed, chunks > 0.

**Status:** ⬜ Not started

---

## Task 7 — Verify chunks have citation data

```bash
cd law_corpus
python3 -c "
import json, pathlib
chunks_dir = pathlib.Path('data/chunks')
for f in sorted(chunks_dir.glob('*.json'))[:1]:
    data = json.loads(f.read_text())
    chunk = data[0]
    print('chunk_id:', chunk.get('chunk_id'))
    print('source_url:', chunk.get('source_url'))
    print('article_url:', chunk.get('article_url'))
    print('document_number:', chunk.get('document_number'))
    print('citation_text:', chunk.get('citation_text'))
    print('article_number:', chunk.get('article_number'))
"
```

**Expected:** Every field populated with real matsne.gov.ge URLs and official document numbers.

**Status:** ⬜ Not started

---

## What Comes After

Once all 7 tasks are ✅ → **Step 2: Backend** (`master_plan/02_backend_system_prompt.md`):
- FastAPI + Gemini 3.1 Pro via Vertex AI
- Firebase Authentication (not custom JWT)
- Free tier with limited interactions (marketing phase)
- Pro tier with credits + payments (later)
- Admin tier with 10,000 credits (unlimited)
- Hybrid RAG search + citation verification
