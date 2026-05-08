# Development Guide

> **Last updated:** 2026-05-09

---

## Code Style and Conventions

### Language & Formatting

- **Python:** 3.11+, formatted with `ruff` (line length 100)
- **Dart/Flutter:** Follows the project lint rules in `analysis_options.yaml`
- **Imports:** Grouped as `stdlib → third-party → local`, sorted alphabetically within groups
- **Type hints:** Required on all public functions and method signatures
- **Docstrings:** All modules, classes, and public functions must have docstrings

### Naming Conventions

| Layer | Pattern | Example |
|-------|---------|---------|
| Routes | `{resource}_router.py` | `chat_router.py` |
| Services | `{resource}_service.py` | `rag_retrieval_service.py` |
| Repositories | `{resource}_repository.py` | `credit_repository.py` |
| Models | `{resource}.py` (singular) | `user.py`, `conversation.py` |
| Schemas | `{resource}_schema.py` | `chat_schema.py` |

### Key Principles (from `GEMINI.md`)

1. **Simplicity First** — Minimum code that solves the problem. No speculative abstractions.
2. **Surgical Changes** — Touch only what you must. Match existing style.
3. **Goal-Driven Execution** — Transform tasks into verifiable goals with success criteria.
4. **Self-Documenting Code** — If you need a comment, the name isn't descriptive enough.

### Running Linters

```bash
cd backend
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format .
```

---

## How to Add a New Endpoint

Use the **Endpoint Builder Workflow** (`.agents/workflows/07_endpoint_builder.md`) for the full structured process. Below is the condensed version.

### Step 1: Schema (`app/schemas/`)

Create or update Pydantic request/response models:

```python
# app/schemas/my_feature_schema.py
from pydantic import BaseModel, Field

class MyFeatureRequest(BaseModel):
    name: str = Field(..., min_length=1)
    value: int = Field(default=0)

class MyFeatureResponse(BaseModel):
    id: str
    name: str
    computed: bool
```

### Step 2: Model (`app/models/`) — if new table needed

```python
# app/models/my_feature.py
import uuid
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.database import Base

class MyFeature(Base):
    __tablename__ = "my_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

Add the new model to `alembic/env.py` imports, then generate a migration:

```bash
cd backend
docker compose exec api alembic revision --autogenerate -m "add_my_features"
docker compose exec api alembic upgrade head
```

### Step 3: Repository (`app/repositories/`)

```python
# app/repositories/my_feature_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.my_feature import MyFeature

class MyFeatureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str) -> MyFeature:
        obj = MyFeature(name=name)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def get_by_id(self, id: uuid.UUID) -> MyFeature | None:
        result = await self.db.execute(select(MyFeature).where(MyFeature.id == id))
        return result.scalar_one_or_none()
```

### Step 4: Service (`app/services/`)

```python
# app/services/my_feature_service.py
from app.repositories.my_feature_repository import MyFeatureRepository

class MyFeatureService:
    def __init__(self, db: AsyncSession):
        self.repo = MyFeatureRepository(db)

    async def create_feature(self, name: str) -> dict:
        obj = await self.repo.create(name)
        return {"id": str(obj.id), "name": obj.name}
```

Use the singleton pattern:

```python
_my_feature_service: MyFeatureService | None = None

def get_my_feature_service(db: AsyncSession) -> MyFeatureService:
    global _my_feature_service
    if _my_feature_service is None:
        _my_feature_service = MyFeatureService(db)
    return _my_feature_service
```

### Step 5: Route (`app/routes/`)

```python
# app/routes/my_feature_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.schemas.my_feature_schema import MyFeatureRequest, MyFeatureResponse
from app.services.my_feature_service import get_my_feature_service

router = APIRouter(prefix="/api/v1/my-features", tags=["my-features"])

@router.post("", response_model=MyFeatureResponse, status_code=201)
async def create_my_feature(
    body: MyFeatureRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = get_my_feature_service(db)
    result = await svc.create_feature(body.name)
    return MyFeatureResponse(**result)
```

### Step 6: Wire Up

Register the router in `app/main.py`:

```python
from app.routes import my_feature_router

# In create_app():
app.include_router(my_feature_router.router)
```

If the endpoint costs credits, add it to `CREDIT_ROUTES` in `app/middleware/credit_gate_middleware.py`:

```python
CREDIT_ROUTES: dict[str, CreditAction] = {
    "/api/v1/chat/": CreditAction.CHAT,
    "/api/v1/case-files/build": CreditAction.CASE_FILE,
    "/api/v1/my-features/": CreditAction.CHAT,  # <-- add here
}
```

### Step 7: Test

```bash
cd backend
.venv/bin/python -m pytest tests/test_my_feature.py -v
```

Cover: happy path, 404, invalid input, auth.

### Step 8: Document

Add the endpoint to [`docs/API.md`](./API.md) with a curl example.

---

## How to Add a New Service

1. Create `app/services/my_service.py`
2. Use the singleton pattern (see above)
3. Inject repository instances, never SQLAlchemy directly
4. Call integrations (Vertex AI, Firebase) from services, not routes
5. Add unit tests in `tests/test_my_service.py`

---

## How to Modify the RAG Pipeline

The RAG pipeline lives in `app/services/rag_retrieval_service.py`. Key constants are in `app/config/constants.py`:

```python
RAG_VECTOR_SEARCH_TOP_K = 50      # Per expanded query
RAG_FULLTEXT_SEARCH_TOP_K = 50    # Per expanded query
RAG_RERANK_TOP_K = 20             # After merge + dedup
RAG_QUERY_EXPANSION_COUNT = 8     # Target expanded queries
```

### To Change Retrieval Parameters

Edit `app/config/constants.py` and restart the server:

```bash
cd backend
docker compose restart api
```

### To Change Query Expansion Prompt

Edit `app/prompts/rag_pipeline.py`:

```python
QUERY_EXPANSION_PROMPT = """
You are a Georgian legal search expert...
"""
```

### To Add a New ChromaDB Collection

1. Add collection metadata to `app/integrations/chroma_client.py`
2. Ensure embeddings exist in `law_corpus/data/chroma/`
3. Update `RAGCollectionConfig` in `app/schemas/rag_schema.py`
4. Update `docs/API.md` and `docs/LAW_CORPUS.md`

> **Gotcha:** Query embeddings MUST use `RETRIEVAL_QUERY` task type. Corpus embeddings use `RETRIEVAL_DOCUMENT`.

---

## How to Update the Legal Corpus

> **WARNING:** The pre-built corpus in `law_corpus/data/chroma/` should NOT be modified directly in production. Use the pipeline for updates.

### Full Re-embed

```bash
cd law_corpus
source .venv/bin/activate
python -m pipeline.main embed --input-dir data/chunks
python -m pipeline.main index --backend chroma
```

### Incremental Update

```bash
cd law_corpus
source .venv/bin/activate
python -m pipeline.main update --since 2024-01-01
```

### Add a New Legal Source

1. Add the source URL to `pipeline/config.py` or `seed_laws.json`
2. Run the scraper: `python -m pipeline.main scrape --source matsne --laws new_code`
3. Parse: `python -m pipeline.main parse --input-dir data/raw`
4. Chunk: `python -m pipeline.main chunk --input-dir data/parsed`
5. Embed: `python -m pipeline.main embed --input-dir data/chunks`
6. Index: `python -m pipeline.main index --backend chroma`
7. Validate: `python -m pipeline.main validate`

See [`LAW_CORPUS.md`](./LAW_CORPUS.md) for detailed pipeline documentation.

---

## How to Run Tests

### Backend Tests

```bash
cd backend

# All tests
.venv/bin/python -m pytest tests/ -v

# Specific test file
.venv/bin/python -m pytest tests/test_credit_service.py -v

# With coverage
.venv/bin/python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Run on 4 parallel workers (if pytest-xdist installed)
.venv/bin/python -m pytest tests/ -n 4
```

**Current test count:** 124+ tests covering services, routers, and integration.

### Test Database

Tests use the same PostgreSQL instance by default. For isolated tests, set:

```bash
export DATABASE_URL="postgresql+asyncpg://mol_user:corpus_dev_pw@localhost:5432/master_of_law_test"
```

### Flutter Tests

```bash
cd frontend
flutter test
```

---

## How to Use the Eval Pipeline

The evaluation pipeline tests the AI against 50 real Georgian Supreme Court cases.

### Prerequisites

```bash
export GOOGLE_API_KEY="your-gcp-api-key"
```

### Run Evaluation

```bash
# Step 1: Hold out eval cases from ChromaDB (prevents data contamination)
python3 eval/test_cases/holdout_eval.py holdout

# Step 2: Run evaluation
python3 eval/test_cases/run_eval.py

# Step 3: Restore eval cases after testing
python3 eval/test_cases/holdout_eval.py restore
```

### Filtered Runs

```bash
# Only criminal cases
python3 eval/test_cases/run_eval.py --only criminal

# Specific cases
python3 eval/test_cases/run_eval.py --cases "CRIM-1051ap-24,CRIM-311ap-23"

# Resume interrupted run (auto-skips completed)
python3 eval/test_cases/run_eval.py
```

### View Results

```bash
cat eval/test_cases/eval_results.json | python3 -m json.tool
```

Scoring criteria (1-5 each):
- `verdict_alignment` — Did AI predict the correct outcome?
- `legal_reasoning` — Does AI's logic match the court's?
- `article_accuracy` — Did AI cite the right laws?
- `practical_value` — Would this help a real citizen?

See `eval/steps.md` for the full runbook.

---

## Git Workflow

### Branches

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code. Protected. |
| `feature/*` | New features (e.g., `feature/case-export`) |
| `fix/*` | Bug fixes (e.g., `fix/rate-limit-cache`) |
| `docs/*` | Documentation updates |

### Commit Convention

```
<type>(<scope>): <description>

[optional body]
```

| Type | Use When |
|------|----------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding/updating tests |
| `refactor` | Code change that neither fixes nor adds |
| `chore` | Maintenance, deps, config |

Examples:
```
feat(chat): add websocket streaming endpoint
fix(rag): deduplicate chunks by article_number
docs(api): document questionnaire endpoints
test(credits): add pro tier daily reset test
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make focused, surgical changes
3. Run tests: `pytest tests/ -v`
4. Run linter: `ruff check .`
5. Update relevant docs (`docs/API.md`, `docs/ARCHITECTURE.md`)
6. Open PR with:
   - Clear description of what changed and why
   - Link to related issue/feature spec
   - Test results screenshot or paste
7. Require 1 review before merging

---

## Common Debugging Scenarios

### "401 Unauthorized" on every request

**Cause:** `APP_ENV` is not `development` and no Firebase token is provided.  
**Fix:**
```bash
# For local dev, ensure APP_ENV=development in backend/.env
docker compose restart api
```

### "402 Insufficient Credits"

**Cause:** Free tier exhausted (5/day) or credit balance is zero.  
**Fix:**
```bash
# In development, the mock user is ADMIN with 10,000 credits.
# If you see 402, check that APP_ENV=development.
```

### "429 Rate Limited"

**Cause:** Too many requests for your tier.  
**Fix:** Wait for the `Retry-After` header, or upgrade tier in the database.

### ChromaDB returns empty results

**Cause:** `CHROMA_PERSIST_DIR` is wrong or corpus is missing.  
**Fix:**
```bash
# Verify the corpus exists
ls law_corpus/data/chroma/
# Should show: chroma.sqlite3 + directories for each collection

# Verify docker-compose mounts it correctly
docker compose exec api ls /app/law_corpus_data/chroma/
```

### Gemini API errors ("Quota exceeded", "Permission denied")

**Cause:** GCP project not configured or Vertex AI API not enabled.  
**Fix:**
```bash
# Verify ADC
gcloud auth application-default print-access-token

# Enable API
gcloud services enable aiplatform.googleapis.com --project=gen-lang-client-0225498420
```

### Database migration errors

**Cause:** Model changed but migration not generated, or migration is out of order.  
**Fix:**
```bash
docker compose exec api alembic revision --autogenerate -m "describe_change"
docker compose exec api alembic upgrade head

# If stuck, check current revision
docker compose exec api alembic current
```

### Tests fail with "event loop closed"

**Cause:** `pytest-asyncio` configuration issue.  
**Fix:** Ensure `asyncio_mode = auto` is set in `pyproject.toml`.

### Flutter cannot connect to backend

**Cause:** CORS origins not configured, or wrong base URL.  
**Fix:**
```bash
# Add Flutter dev server origin to backend/.env
APP_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:49563
docker compose restart api
```

---

## Reference: Agent Workflows

The `.agents/workflows/` directory contains predefined prompts for common tasks:

| Workflow | File | When to Use |
|----------|------|-------------|
| Spec → Build | `01_spec_to_build.md` | Building a new feature from scratch |
| Bug → Fix | `02_bug_to_fix.md` | Systematic debugging |
| Code Review | `03_code_review.md` | Quality audit before merging |
| Test Generation | `04_test_generation.md` | Adding test coverage |
| Optimize | `05_optimize.md` | Performance analysis |
| Refactor | `06_refactor.md` | Structural improvements |
| Endpoint Builder | `07_endpoint_builder.md` | Adding REST endpoints |
| Deploy Checklist | `08_deploy_checklist.md` | Before production push |

Read `.agents/workflows/README.md` for usage instructions.
