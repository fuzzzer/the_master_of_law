# 👁️ Observations & Notes

> Things you noticed during testing, usage, or research. Raw signal — no need to be formal.

---

## 2026-05-04

- RAG pipeline took ~203s in PoC — way too slow for production. Mostly embedding rate limits.
- Full-text search returned 0 results — index keys are article names (მუხლი 45), not semantic terms. Needs rethinking.
- Query expansion was excellent — Gemini found great formal legal terms from casual Georgian input.
- Vector search found exactly the right articles for a drug possession case (260, 273, 63).
- Docker stack works: 3 containers (api, postgres, redis) all healthy.
- Alembic migrations applied cleanly — 6 tables created.
- Health endpoint responds immediately.
- Law search works with URL-encoded Georgian text.
- Chat/send endpoint with full RAG pipeline needs more testing.

---

<!-- Add new observations above this line, grouped by date -->
