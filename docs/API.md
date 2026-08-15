# API Reference

> Complete reference for the 32 REST and WebSocket endpoints in the backend.

**Base URL:** `http://localhost:8000` (Local) / `https://api.fuzzzy-law.ge` (Production)
**Authentication:** Pass a Firebase ID token in the header: `Authorization: Bearer <TOKEN>`

## Rate Limiting

The API applies rate limiting based on the user's tier:
- **FREE:** 5 requests/minute
- **PRO:** 30 requests/minute
- **ADMIN:** 120 requests/minute

When a rate limit is exceeded, the server returns a `429 Too Many Requests` status code.

## Error Codes

- `400 Bad Request`: Invalid request parameters or body.
- `401 Unauthorized`: Missing or invalid Firebase token.
- `402 Payment Required`: Insufficient credits for the requested action.
- `403 Forbidden`: User lacks permission to access the resource.
- `404 Not Found`: Resource does not exist.
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: An unexpected error occurred on the server.

---

## Health

### `GET /api/v1/health`
Check if the API is running.
- **Auth:** No
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/health`

### `GET /api/v1/health/ready`
Check if the API is ready to serve requests (reports ChromaDB collection counts).
- **Auth:** No
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/health/ready`

---

## Auth & Account

### `POST /api/v1/auth/verify-token`
Verifies a Firebase token and returns the corresponding user profile. Creates the user if they don't exist.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl -X POST http://localhost:8000/api/v1/auth/verify-token -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/auth/me`
Get the current authenticated user's profile.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/account/credits`
Get the current user's credit balance and tier.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/account/credits -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/account/transactions`
Get the user's credit transaction history.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/account/transactions -H "Authorization: Bearer <TOKEN>"`

---

## Chat & Conversations

### `POST /api/v1/conversations`
Start a new conversation.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl -X POST http://localhost:8000/api/v1/conversations -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/conversations`
List user's conversations.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/conversations -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/conversations/{id}`
Get a specific conversation along with its messages.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/conversations/123 -H "Authorization: Bearer <TOKEN>"`

### `DELETE /api/v1/conversations/{id}`
Delete a conversation.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl -X DELETE http://localhost:8000/api/v1/conversations/123 -H "Authorization: Bearer <TOKEN>"`

### `POST /api/v1/chat/{id}/send`
Send a message in a conversation and get an AI response.
- **Auth:** Yes
- **Credits:** 1
- **Body:** `{"message": "Hello", "rag_config": {"legal_codes": true, "court_practice": false, "grand_chamber": true}}`
- **Example:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/123/send \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my rights?", "rag_config": {"legal_codes": true}}'
```

### `WS /api/v1/chat/{id}/ws`
WebSocket endpoint for streaming chat responses.
- **Auth:** Yes (Token passed in query param or initial WS message depending on client setup)
- **Credits:** 1 per interaction

---

## Cases

### `POST /api/v1/case-files/build`
Build a defense case from provided facts.
- **Auth:** Yes
- **Credits:** 3
- **Body:** `{"facts": "...", "rag_config": {...}}`
- **Example:**
```bash
curl -X POST http://localhost:8000/api/v1/case-files/build \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"facts": "Car accident...", "rag_config": {"legal_codes": true}}'
```

### `GET /api/v1/case-files`
List user's case files.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/case-files -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/case-files/{id}`
Get a specific case file.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/case-files/123 -H "Authorization: Bearer <TOKEN>"`

### `PATCH /api/v1/case-files/{id}`
Update case file notes/status.
- **Auth:** Yes
- **Credits:** 0
- **Example:**
```bash
curl -X PATCH http://localhost:8000/api/v1/case-files/123 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Follow up next week"}'
```

### `DELETE /api/v1/case-files/{id}`
Delete a case file.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl -X DELETE http://localhost:8000/api/v1/case-files/123 -H "Authorization: Bearer <TOKEN>"`

---

## Law Retrieval (RAG)

### `GET /api/v1/rag/collections`
List available RAG sources and their availability status. Used by the Flutter app to display toggles.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/rag/collections -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/laws/search`
Search the legal corpus directly.
- **Auth:** Yes
- **Credits:** 0
- **Query:** `?q=search term`
- **Example:** `curl "http://localhost:8000/api/v1/laws/search?q=theft" -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/laws/codes`
List all indexed legal codes.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/laws/codes -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/laws/codes/{id}`
Get the structure of a specific legal code.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/laws/codes/civil_code -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/laws/articles/{id}`
Get the full text of a specific article.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/laws/articles/civil_code_article_1 -H "Authorization: Bearer <TOKEN>"`

---

## Feedback

### `POST /api/v1/feedback`
Submit feedback for an AI generation or case file.
- **Auth:** Optional
- **Credits:** 0
- **Example:**
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"target_id": "conv_123", "rating": 5, "comment": "Great analysis"}'
```

### `GET /api/v1/feedback/{target_id}`
Get feedback associated with a specific target.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/feedback/conv_123 -H "Authorization: Bearer <TOKEN>"`

### `GET /api/v1/feedback/summary`
Get aggregated feedback summary. (ADMIN only)
- **Auth:** Yes (Admin)
- **Credits:** 0
- **Example:** `curl http://localhost:8000/api/v1/feedback/summary -H "Authorization: Bearer <TOKEN>"`

### `PATCH /api/v1/feedback/{id}`
Update your own feedback (allowed within a 24h window).
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl -X PATCH ...`

### `DELETE /api/v1/feedback/{id}`
Delete your own feedback.
- **Auth:** Yes
- **Credits:** 0
- **Example:** `curl -X DELETE http://localhost:8000/api/v1/feedback/123 -H "Authorization: Bearer <TOKEN>"`
