# 🚀 Master of Law — Backend Startup Guide

## Quick Start (Copy-Paste)

```bash
cd backend

# 1. Clean start (use this every time for reliability)
docker compose down
docker compose up --build -d

# 2. Wait for healthy containers, then run migrations
docker compose exec api alembic upgrade head

# 3. Verify it works
curl -s http://localhost:8000/api/v1/conversations \
  -X POST -H "Content-Type: application/json" \
  -d '{"title": "test"}' | python3 -c \
  "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```

## 🧪 Test Case Prompts (Copy-Paste)

After verifying the API is up, use these to test the full RAG pipeline:

```bash
# Save conversation ID for reuse
CONV_ID=$(curl -s -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "ტესტი"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Created conversation: $CONV_ID"
```

### Case 1: Criminal (Drug possession — პროვოკაცია)
```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/${CONV_ID}/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "გამარჯობა. 0.5 გრამი ჰაშიში მქონდა ნაყიდი, დამალული იყო მიწაში, ვეძებდი როცა მოვიდნენ ჩემსავით ჩაცმული 2 პირი და მითხრეს დაგეხმარებითო მოძებნაში, როგორც კი ვიპოვნე ხელი გამიყარეს და მითხრეს პოლიცია ვართო. ექსპერტიზამ თქვა რომ აღმოჩნდა 0.63 გრამი. მე ეგ მხოლოდ ჩემთვის მქონდა, არც გაყიდვას ვაპირებდი. თან პირველი შემთხვევაა. რა მელის ახლა? როგორ დავიცვა თავი?"}' \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```

### Case 2: Labor (შვებულება — vacation rights)
```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/${CONV_ID}/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "დამსაქმებელი არ მაძლევს კუთვნილ შვებულებას, მიუხედავად იმისა რომ 11 თვეზე მეტია ვმუშაობ, ასევე მიცხადებს რომ ვერ მომცემს შვებულებას ვერც მომავალ წელს. რა შეიძლება მოვიმოქმედო? აქვს თუ არა უფლება შემიზღუდოს შვებულებაში გასვლა?"}' \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```

### Case 3: Build case file from conversation
```bash
curl -s -X POST http://localhost:8000/api/v1/case-files/build \
  -H "Content-Type: application/json" \
  -d "{\"conversation_id\": \"${CONV_ID}\"}" \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```

> ⏱ Chat takes **10-30 seconds** (RAG pipeline + Gemini). Case build takes **20-60 seconds**.

---

## 🔍 Root Cause: "Missing X-API-KEY" Ghost Error (2026-05-05)

### What happened
After running `docker compose up`, all API requests returned:
```json
{"detail": "Missing X-API-KEY header"}
```
But **NO code in the codebase** contained "X-API-KEY" — searched all `.py`, middleware, 
configs, `.env`, and git history. Zero matches.

### Root cause: Stale Docker image with cached old code

The error came from an **old Docker image layer** that was never rebuilt. Here's the chain:

1. **No `.dockerignore` existed** → Docker's `COPY . .` was copying everything 
   including `__pycache__/`, `.pyc` files, `.venv/`, and any temp files
2. At some point, an older version of the middleware (or a test/experiment) had an 
   API key check that got compiled into `.pyc` bytecode
3. Docker's layer caching kept serving the old image — `docker compose up` does NOT 
   rebuild images by default, it reuses the existing image
4. Even `docker compose down` doesn't remove images — only containers/networks
5. The stale container was sitting on port 8000 with the old code

### How it was fixed
```bash
docker compose down -v          # Kill containers + remove volumes
docker compose build --no-cache # Rebuild image from scratch
docker compose up -d            # Start fresh
```

### Preventive measures applied
- Created `.dockerignore` (see below)
- This guide documents the correct startup procedure

---

## ⚠️ Common Pitfalls

### 1. Port 8000 already in use
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```
**Fix:**
```bash
# Find what's using port 8000
lsof -i :8000 -P

# If it's an old Docker container:
docker compose down

# If it's something else (another uvicorn, a different project):
kill <PID>
```

### 2. "relation does not exist" (500 error)
The DB is fresh but has no tables. Migrations haven't been run.
```bash
docker compose exec api alembic upgrade head
```

### 3. Docker using stale code (changes not reflected)
`docker compose up` reuses existing images. You need `--build`:
```bash
docker compose up --build -d
```
For nuclear option (after major changes):
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose exec api alembic upgrade head
```

### 4. `.pyc` / `__pycache__` contamination
Without `.dockerignore`, old bytecode from host can leak into the image.
Always ensure `.dockerignore` exists (see below).

### 5. Unicode in curl JSON
Georgian text in terminal shows as `\u10xx` escapes. Use:
```bash
| python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))"
```
instead of `| python3 -m json.tool`

### 6. Multiline text in curl JSON body
JSON strings cannot have literal newlines. Either:
- Keep the message on a single line
- Use `\n` escape sequences
- Read from a file: `-d "{\"message\": \"$(cat case.md)\"}"`

---

## 🏗️ Architecture Reminder

```
Host Machine (macOS)
  │
  ├── localhost:8000 ──► Docker: api container (uvicorn)
  │                        ├── connects to postgres:5432 (internal)
  │                        ├── connects to redis:6379 (internal)  
  │                        └── Gemini API (outbound HTTPS)
  │
  └── Postgres & Redis are NOT exposed to host
```

- **Auth in dev mode**: Bypassed. Mock user `dev-user-001` with `ADMIN` tier
- **Auth in prod**: Firebase JWT required in `Authorization: Bearer <token>` header
- **APP_ENV**: Set in `.env`. Must be `development` for local testing

---

## 📁 Required .dockerignore

If missing, create `backend/.dockerignore`:
```
__pycache__
*.pyc
*.pyo
.venv
.env
.git
.gitignore
*.md
.mypy_cache
.pytest_cache
.coverage
htmlcov
```

---

## 🔄 Lifecycle Commands

| Action | Command |
|--------|---------|
| Start | `docker compose up --build -d` |
| Stop | `docker compose down` |
| Logs | `docker compose logs api -f` |
| Shell | `docker compose exec api bash` |
| Migrate | `docker compose exec api alembic upgrade head` |
| New migration | `docker compose exec api alembic revision --autogenerate -m "desc"` |
| Full reset | `docker compose down -v && docker compose build --no-cache && docker compose up -d` |
| Check port | `lsof -i :8000 -P` |
