# Quick Start Guide

> **Zero-to-running in under 30 minutes.** 

This guide covers both **local development** and **production deployment** for Fuzzzy Law (ბუნდოვანი კანონი).

## System Requirements

Ensure you have the following installed before starting:
- **OS:** macOS or Linux (Windows via WSL2)
- **Python:** 3.11 or higher
- **Flutter:** 3.x
- **Docker & Docker Compose**
- **Git**
- **Firebase CLI:** `npm install -g firebase-tools`
- **Google Cloud SDK:** `gcloud` (for Vertex AI)

## 1. Clone and Initial Setup

```bash
git clone https://github.com/fuzzzer/fuzzzy_law.git
cd fuzzzy_law
```

## 2. Law Corpus Data Setup

The `law_corpus/data` directory containing the ChromaDB collections is ignored by Git due to its size. You must generate or download this data before starting the backend.

**Option A: Generate it locally (Requires GCP Vertex AI setup)**

To generate the corpus yourself, you will need to run the data pipeline. The pipeline consists of six stages:
1. **Scrape:** Downloads raw HTML documents from `matsne.gov.ge`.
2. **Parse:** Converts HTML into structured JSON documents with articles.
3. **Chunk:** Splits the parsed documents into semantic chunks.
4. **Embed:** Calls Vertex AI (`gemini-embedding-001`) to generate vector embeddings.
5. **Index:** Loads the embeddings into ChromaDB for search.
6. **Thresholds:** Ingests additional pre-extracted catalog data (e.g., drug quantities, fines) into the database.

```bash
cd law_corpus
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# Authenticate with Google Cloud for Vertex AI
gcloud auth application-default login
# Edit .env and ensure GOOGLE_CLOUD_PROJECT is set
```

**To generate the core P0 laws only (fastest setup):**
```bash
python -m pipeline.main run --priority P0
```

**To run the entire pipeline and embed ALL laws (takes longer):**
```bash
python -m pipeline.main run
```

You can also run individual steps manually if needed (e.g., `python -m pipeline.main scrape`, `python -m pipeline.main embed`).

```bash
cd ..
```

**Option B: Ask for a backup**
If you are part of the core team, ask a team member for the latest `law_corpus/data.zip` archive and extract it into the `law_corpus/` directory:
```bash
unzip data.zip -d law_corpus/
```

## 3. Backend Setup (Local Development)

The backend uses FastAPI, PostgreSQL, Redis, and ChromaDB. We use Docker to make local development easy.

```bash
cd backend

# Create your local environment variables
cp .env.example .env

# Edit .env and ensure:
# - GCP_SA_KEY_PATH points to your gcloud credentials
#   (typically: ~/.config/gcloud/application_default_credentials.json)
# - APP_ENV=development (enables mock auth, no API key needed)

# Start the services in the background
docker compose up -d

# Initialize database tables
docker compose exec api python -c "
import asyncio
from app.models.database import Base, get_engine
from app.models import conversation, user, feedback, case_file, message, questionnaire, user_credits
async def init():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('All tables created!')
asyncio.run(init())
"
```

Verify the backend is running:
```bash
curl http://localhost:8000/api/v1/health
```
You should receive a `{"status": "ok", ...}` response.

## 4. Frontend (Flutter) Setup

The frontend is a Flutter mobile/web application located in the `frontend/` directory (package name `fuzzzy_law`).

```bash
cd ../frontend

# Get dependencies
flutter pub get

# Run the app in development mode
flutter run --target lib/main_development.dart --flavor development

# Or for web:
flutter run -d chrome --target lib/main_development.dart
```

## 5. First API Call

Test the RAG collections endpoint to ensure the law corpus is available:

```bash
curl http://localhost:8000/api/v1/rag/collections
```
You should see a list of available legal sources (e.g., `georgian_laws`, `court_practice`, `grand_chamber`).

---

## Common Errors and Fixes

- **Port 8000 is in use:** `lsof -i :8000` on macOS to find what's using it.
- **Docker RAM limit:** Ensure Docker Desktop has at least 4GB of RAM.
- **Flutter build errors:** Run `flutter clean && flutter pub get`.
- **Database "table does not exist":** Run the table creation script from Section 3.
- **Missing API Keys:** If testing LLM features without the mock auth bypass, ensure `GOOGLE_API_KEY` or GCP credentials are set.

## Verify Your Setup Checklist

- [ ] Backend is running (`docker compose ps` shows `api`, `postgres`, `redis` as Up/Healthy)
- [ ] `curl http://localhost:8000/api/v1/health` returns `ok`
- [ ] Database tables are created
- [ ] Flutter app compiles and opens on a device/emulator
- [ ] `curl http://localhost:8000/api/v1/rag/collections` returns the legal data sources

If you've checked all these boxes, you are ready to start developing! See [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines.
