# 🛤️ Workflow: New Endpoint Builder

> **Use when:** Adding a new REST API endpoint to the backend.
> **Philosophy:** Endpoints are thin. Logic lives in services. Data lives in repos.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for quality standards.
Read `AI_GUIDE.md` for architecture and existing endpoints.
Read `.agents/code_architect/context.md` for patterns.

## New Endpoint

**Method & Path:** [e.g., "POST /api/v1/case-files/{id}/export"]

**Purpose:** [ONE SENTENCE — what does this endpoint do?]

**Request Body:**
[DESCRIBE FIELDS, OR "none"]

**Response:**
[DESCRIBE THE RESPONSE SHAPE]

**Auth Required:** [yes/no]
**Credits Cost:** [0/1/2/3]
**Rate Limited:** [yes/no — which tier?]

## Execute This Workflow:

### Step 1 — Schema (app/schemas/)
Create or update Pydantic request/response models.
All fields typed. Optional fields have defaults.

### Step 2 — Model (app/models/) — if new table needed
Create SQLAlchemy model. Add to alembic/env.py imports.
Generate migration: `alembic revision --autogenerate -m "add_X"`

### Step 3 — Repository (app/repositories/)
Add data access methods. One repo per model. Inject `AsyncSession`.
Use `select()`, `update()`, `delete()` — never raw SQL.

### Step 4 — Service (app/services/)
Add business logic method. Singleton pattern.
Call repository for DB. Call integrations for external APIs.
Never import SQLAlchemy here.

### Step 5 — Route (app/routes/)
Create thin route handler (max 15 lines).
Parse request → call service → return response.
Add error handling: 404, 400, 422, 500.

### Step 6 — Wire Up
Register router in `app/main.py` if new file.
Add to `CREDIT_ROUTES` in middleware if costs credits.

### Step 7 — Test
Write test in `tests/`. Cover: happy path, 404, invalid input, auth.

### Step 8 — Document
Add to endpoint table in `AI_GUIDE.md`.
Provide curl example for manual testing.
```
