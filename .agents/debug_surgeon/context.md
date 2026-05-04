# 🔬 Debug Surgeon — Skill Context

> **When to load:** Something is broken, tests are failing, production is misbehaving, or behavior doesn't match expectations.

---

## Debug Philosophy

> *"Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it."* — Kernighan

### The Cardinal Rule

**Never guess. Always verify.**

The moment you think "it's probably X", you've already lost 30 minutes. Instead:
1. **Reproduce** the exact failure
2. **Isolate** to the smallest possible scope
3. **Hypothesize** with evidence (not intuition)
4. **Test** the hypothesis with a minimal experiment
5. **Fix** only what's broken, nothing else
6. **Verify** the fix doesn't break anything else

---

## Hypothesis-Driven Debugging Protocol

### Step 1: Reproduce (MANDATORY)

```bash
# Can you trigger the exact error?
# Write the EXACT command/request that fails:

curl -X POST http://localhost:8000/api/v1/chat/CONV_ID/send \
  -H "Content-Type: application/json" \
  -d '{"message": "ტესტი"}'

# What EXACTLY is the error? (Copy the full error, not a summary)
# Status code? Response body? Stack trace?
```

**If you can't reproduce it, you can't debug it.** Stop and find a way to reproduce first.

### Step 2: Isolate

Ask these questions in order (stop at the first "yes"):

```
1. Is the problem in the request? (wrong URL, missing header, bad JSON)
2. Is the problem in the middleware? (auth, rate limit, credit gate)
3. Is the problem in the route handler? (parsing, validation)
4. Is the problem in the service? (business logic, AI call)
5. Is the problem in the repository? (SQL query, ORM mapping)
6. Is the problem in an integration? (ChromaDB, Vertex AI, Firebase)
7. Is the problem in configuration? (.env, constants, Docker volumes)
8. Is the problem environmental? (network, disk, memory, permissions)
```

### Step 3: The Five Whys

```
Problem: Chat endpoint returns 500

Why? → LegalAnalysisService raised an exception
Why? → Gemini API returned an error
Why? → The API key was invalid
Why? → .env had VERTEX_AI_API_KEY set but docker-compose overrides with GOOGLE_APPLICATION_CREDENTIALS
Why? → We switched to ADC but forgot to remove the old API key code path

Root cause: Auth method conflict between API key and ADC
Fix: Remove API key fallback, use ADC exclusively
```

---

## Common Failure Patterns in THIS Project

### 1. Vertex AI / Gemini Errors

```python
# Symptom: "403 Forbidden" or "401 Unauthorized"
# Check:
# - Is GOOGLE_APPLICATION_CREDENTIALS pointing to valid SA key?
# - Is the SA key mounted correctly in docker-compose.yml?
# - Does the service account have roles/aiplatform.user?
# - Is the GCP project ID correct?

# Quick test:
docker compose exec api python -c "
from google import genai
client = genai.Client(vertexai=True, project='gen-lang-client-0225498420', location='us-central1')
response = client.models.generate_content(model='gemini-3.1-pro', contents='Hello')
print(response.text)
"
```

### 2. ChromaDB Issues

```python
# Symptom: "Collection not found" or 0 search results
# Check:
# - Is CHROMA_PERSIST_DIR correct? (should be /app/law_corpus_data/chroma in Docker)
# - Is the volume mounted? Check docker-compose.yml volumes
# - Is the collection name correct? Must be "georgian_laws"
# - Are embeddings the right dimensions? Must be 768

# Quick test:
docker compose exec api python -c "
import chromadb
client = chromadb.PersistentClient(path='/app/law_corpus_data/chroma')
collection = client.get_collection('georgian_laws')
print(f'Documents: {collection.count()}')
print(f'Sample: {collection.peek(1)}')
"
```

### 3. PostgreSQL Connection Errors

```python
# Symptom: "Connection refused" or "could not connect to server"
# Check:
# - Is postgres container healthy? `docker compose ps`
# - Is DATABASE_URL using Docker hostname "postgres" (not "localhost")?
# - Is POSTGRES_PASSWORD consistent between .env and docker-compose env override?

# Quick test:
docker compose exec postgres psql -U mol_user -d master_of_law -c "SELECT count(*) FROM users;"
```

### 4. Redis Connection Errors

```python
# Symptom: Rate limiter fails or "Connection refused"
# Check:
# - Is redis container healthy?
# - Is REDIS_PASSWORD set (it was empty once, caused crash)?
# - Is REDIS_URL using Docker hostname "redis"?

# Quick test:
docker compose exec redis redis-cli -a YOUR_PASSWORD ping
```

### 5. Alembic Migration Issues

```bash
# Symptom: "relation does not exist" on any DB query
# Fix: Run migrations
docker compose exec api alembic upgrade head

# If migration history is corrupt:
docker compose exec api alembic stamp head  # Mark current as "latest"
docker compose exec api alembic revision --autogenerate -m "fix"
docker compose exec api alembic upgrade head
```

### 6. Georgian Text Encoding

```python
# Symptom: Garbled text, question marks, or empty responses
# Check:
# - Is the request body UTF-8?
# - Is the database connection using UTF-8?
# - Are you URL-encoding Georgian text in curl? Use --data-urlencode

# Correct curl for Georgian:
curl -G http://localhost:8000/api/v1/laws/search \
  --data-urlencode "q=ქურდობა" \
  --data-urlencode "top_k=3"
```

---

## Debug Toolbox

### Log-Based Debugging

```python
# Add temporary debug logging (REMOVE before committing)
from app.utils.logger import get_logger
logger = get_logger(__name__)

# Use structured logging for easy grep
logger.debug("debug_checkpoint", 
    stage="vector_search",
    query_count=len(queries),
    results_count=len(results),
    elapsed_ms=elapsed * 1000,
)
```

### Docker Debug Commands

```bash
# View container logs (last 50 lines, follow)
docker compose logs --tail 50 -f api

# Execute a shell inside the API container
docker compose exec api /bin/bash

# Check container resource usage
docker stats

# Inspect container networking
docker compose exec api python -c "import socket; print(socket.gethostbyname('postgres'))"

# Check mounted volumes
docker compose exec api ls -la /app/law_corpus_data/chroma/
```

### Python Debug Commands (inside container)

```python
# Test the full import chain
import sys; sys.path.insert(0, '.')
from app.main import create_app
app = create_app()
routes = [r.path for r in app.routes if hasattr(r, 'path')]
print(f"Routes loaded: {len(routes)}")

# Test a specific service
from app.services.rag_retrieval_service import get_rag_service
rag = get_rag_service()
print(f"RAG service initialized: {rag is not None}")

# Test ChromaDB
from app.integrations.chroma_client import get_chroma_client
chroma = get_chroma_client()
print(f"ChromaDB docs: {chroma.count()}")
```

---

## The "It Works Locally" Checklist

When something works in dev but fails in Docker:

```
□ Environment variables: Are they set in docker-compose.yml AND .env?
□ File paths: Are you using container paths (/app/...) not host paths?
□ Network: Are you using Docker hostnames (postgres, redis) not localhost?
□ Permissions: Can the container user read the mounted files?
□ Dependencies: Did the Docker build install all pip packages?
□ Volume mounts: Are they correct in docker-compose.yml?
□ Port mapping: 127.0.0.1:8000:8000 means host binds to localhost only
```

---

## Post-Mortem Template

After fixing a significant bug, document it:

```markdown
### Bug: [One-line description]
**Date:** YYYY-MM-DD
**Severity:** Critical / High / Medium / Low
**Symptom:** What the user/system experienced
**Root cause:** The actual underlying issue
**Fix:** What was changed (with file paths)
**Prevention:** How to prevent similar bugs
**Detection time:** How long from report to root cause identification
```
