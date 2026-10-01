# Fuzzzy Law — Startup Guide

## Current Status (as of 2026-05-04)

### DONE:
- PostgreSQL running in Docker (container: backend-postgres-1, healthy)
- Redis running in Docker (container: backend-redis-1, healthy)
- API container running (container: backend-api-1)
- Alembic migrations applied (6 tables: users, user_credits, credit_transactions, conversations, messages, case_files)
- Health check passing: `curl http://localhost:8000/api/v1/health` returns OK
- Conversation created: ID = `19435383-f883-434b-85bf-b01ea116d8b2`
- Vertex AI API key set in backend/.env
- REDIS_PASSWORD set to `redis_dev_pw` in backend/.env

### NOT YET TESTED:
- Law search endpoint (Georgian URL encoding issue — use --data-urlencode)
- Chat/send endpoint (full RAG pipeline + Gemini)
- Case file builder
- WebSocket streaming
- Swagger docs at http://localhost:8000/docs

### Fixes Made This Session:
1. Set REDIS_PASSWORD=redis_dev_pw in backend/.env (was empty, crashed Redis)
2. Rewrote backend/alembic/env.py to use async engine + sys.path fix
3. Created backend/alembic/script.py.mako (was missing)
4. alembic.ini URL changed to use Docker hostname "postgres" instead of "localhost"

---

## How to Start Everything (from scratch)

### Step 1 — Start Docker containers:
```
cd /Users/fuzzzer/programming/fuzzzy_organisation/fuzzzy_law/backend && docker compose up -d
```

### Step 2 — Verify all 3 are healthy:
```
docker ps
```
You should see: backend-postgres-1 (healthy), backend-redis-1 (healthy), backend-api-1

### Step 3 — Verify health:
```
curl http://localhost:8000/api/v1/health
```

---

## How to Resume Testing

### Test 1 — Law search:
```
curl -G http://localhost:8000/api/v1/laws/search --data-urlencode "q=ქურდობა" --data-urlencode "top_k=3"
```

### Test 2 — Create a new conversation:
```
curl -X POST http://localhost:8000/api/v1/conversations -H "Content-Type: application/json" -d '{"title": "test"}'
```

### Test 3 — Send chat message (replace THE_ID with id from Test 2):
```
curl -X POST http://localhost:8000/api/v1/chat/THE_ID/send -H "Content-Type: application/json" -d '{"message": "ძალიან მრცხვენია ამის თქმა, მაგრამ გუშინ სუპერმარკეტიდან საჭმელი მოვიპარე. სახლში ბავშვები მყავდა მშიერი, სამსახურიდან გამომიშვეს და სხვა გზა უბრალოდ აღარ მქონდა. დაცვამ დამინახა კამერებში, გამაჩერეს და პოლიცია გამოიძახეს. რაც წამოვიღე, სულ რაღაც 40 თუ 50 ლარის პროდუქტები იქნებოდა. პირველად ჩავიდინე ასეთი რამ. დამიჭერენ ამის გამო? რა სასჯელი შეიძლება მომცენ?"}'
```

### Test 4 — Open Swagger docs in browser:
```
open http://localhost:8000/docs
```

### Test 5 — List legal codes:
```
curl http://localhost:8000/api/v1/laws/codes
```

---

## If Something Fails

- **Containers not running** → `cd backend && docker compose up -d`
- **"Connection refused"** → Check `docker ps`, restart with `docker compose restart`
- **Gemini errors** → Check VERTEX_AI_API_KEY in backend/.env
- **DB errors** → Migrations might need re-run: `docker compose exec api alembic upgrade head`
- **Need full rebuild** → `docker compose down && docker compose up -d --build`

---

## Key Files Reference
- `backend/.env` — all config (API key, DB, Redis)
- `backend/alembic/env.py` — migration config (fixed this session)
- `backend/alembic/script.py.mako` — migration template (created this session)
- `backend/alembic.ini` — DB URL for migrations
- `AI_GUIDE.md` — full architecture and all 25 endpoints
- `startup_handoff.md` — original handoff notes
