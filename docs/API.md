# API Reference

> **Last updated:** 2026-05-09
> **Base URL:** `http://localhost:8000` (local) / `https://api.kanonis-ostati.ge` (production)
> **Version:** `v1`
> **Prefix:** `/api/v1`

---

## Authentication

Most endpoints require a Firebase ID token in the `Authorization` header:

```bash
Authorization: Bearer <firebase_id_token>
```

In development (`APP_ENV=development`), no token is required. The backend uses a mock `ADMIN` user.

---

## Error Codes

| HTTP | Code | Meaning |
|------|------|---------|
| 200 | — | Success |
| 201 | — | Created |
| 204 | — | No Content (deleted) |
| 400 | `bad_request` | Invalid input |
| 401 | `unauthorized` | Missing or invalid Firebase token |
| 402 | `insufficient_credits` | Not enough credits for this action |
| 404 | `not_found` | Resource does not exist |
| 422 | `validation_error` | Pydantic validation failed |
| 429 | `rate_limited` | Too many requests for your tier |
| 500 | `internal_error` | Server error |
| 503 | `service_unavailable` | Credit check or dependency unavailable |

---

## Rate Limiting

Rate limits are enforced per-tier, per-minute:

| Tier | Limit |
|------|-------|
| FREE | 5 requests/minute |
| PRO | 30 requests/minute |
| ADMIN | 120 requests/minute |

Rate-limited responses include:
```json
{
  "error": "rate_limited",
  "message": "Rate limit exceeded. Try again in 12s.",
  "retry_after": 12
}
```

---

## Endpoint Groups

### Health

#### `GET /api/v1/health`
Liveness probe. Returns 200 if the server is running.

- **Auth:** None
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/health
```

**Response:**
```json
{"status": "ok"}
```

---

#### `GET /api/v1/health/ready`
Readiness probe. Checks ChromaDB and Vertex AI embedding client.

- **Auth:** None
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/health/ready
```

**Response:**
```json
{
  "status": "ok",
  "components": [
    {"name": "chromadb", "status": "ok", "detail": "20712 documents across 3 collection(s)"},
    {"name": "vertex_embedding", "status": "ok", "detail": "Client initialized"}
  ]
}
```

> **Gotcha:** If status is `degraded`, check `docker compose logs api` for the failing component.

---

### Auth

#### `POST /api/v1/auth/verify-token`
Verify a Firebase ID token and sync the user to PostgreSQL.

- **Auth:** None (this IS the auth endpoint)
- **Credits:** 0

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-token \
  -H "Content-Type: application/json" \
  -d '{"id_token": "<firebase_id_token>"}'
```

**Request Body:**
```json
{"id_token": "string"}
```

**Response:**
```json
{
  "uid": "abc123",
  "email": "user@example.com",
  "display_name": "User Name",
  "tier": "FREE",
  "credits_remaining": 5,
  "daily_credits_used": 0
}
```

---

#### `GET /api/v1/auth/me`
Get the current authenticated user's profile.

- **Auth:** Firebase ID Token
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:** Same as `/auth/verify-token`.

---

### Account & Credits

#### `GET /api/v1/account/credits`
Get credit balance and daily usage.

- **Auth:** Required
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/account/credits \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:**
```json
{
  "tier": "FREE",
  "credit_balance": 5,
  "daily_credits_used": 0,
  "daily_limit": 5
}
```

---

#### `GET /api/v1/account/transactions`
Get credit transaction history.

- **Auth:** Required
- **Credits:** 0
- **Query Params:** `limit` (default 50, max 100), `offset` (default 0)

```bash
curl "http://localhost:8000/api/v1/account/transactions?limit=10&offset=0" \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:**
```json
{
  "transactions": [
    {
      "amount": -1,
      "transaction_type": "chat",
      "description": "Chat in conversation 550e8400...",
      "created_at": "2026-05-09T02:00:00"
    }
  ],
  "total": 42
}
```

---

### Conversations

#### `POST /api/v1/conversations`
Start a new conversation.

- **Auth:** Required
- **Credits:** 0

```bash
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_id_token>" \
  -d '{"title": "Property Dispute"}'
```

**Request Body:**
```json
{"title": "string (optional)"}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Property Dispute",
  "phase": "GREETING",
  "legal_domain": "",
  "created_at": "2026-05-09T02:00:00",
  "updated_at": "2026-05-09T02:00:00"
}
```

---

#### `GET /api/v1/conversations`
List user's conversations.

- **Auth:** Required
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/conversations \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:**
```json
{
  "conversations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Property Dispute",
      "phase": "GREETING",
      "legal_domain": "",
      "created_at": "2026-05-09T02:00:00",
      "updated_at": "2026-05-09T02:00:00"
    }
  ],
  "total": 1
}
```

---

#### `GET /api/v1/conversations/{id}`
Get a conversation with all messages.

- **Auth:** Required
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/conversations/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Property Dispute",
  "phase": "ANALYSIS",
  "legal_domain": "property",
  "messages": [
    {"role": "user", "content": "...", "created_at": "..."},
    {"role": "assistant", "content": "...", "citations": [...], "created_at": "..."}
  ],
  "created_at": "2026-05-09T02:00:00"
}
```

---

#### `DELETE /api/v1/conversations/{id}`
Delete a conversation and its messages.

- **Auth:** Required
- **Credits:** 0

```bash
curl -X DELETE http://localhost:8000/api/v1/conversations/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:** `204 No Content`

---

### Chat

#### `POST /api/v1/chat/{conversation_id}/send`
Send a message and get an AI legal analysis response. Costs 1 credit.

- **Auth:** Required
- **Credits:** 1

```bash
curl -X POST http://localhost:8000/api/v1/chat/550e8400-e29b-41d4-a716-446655440000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_id_token>" \
  -d '{
    "message": "ჩემს მეზობელს სახლი დავანგრიე და სასამართლოში მიმყავს. რა უფლებები მაქვს?",
    "rag_config": {"legal_codes": true, "court_practice": true, "grand_chamber": false}
  }'
```

**Request Body:**
```json
{
  "message": "string (1-10000 chars)",
  "conversation_history": [],
  "rag_config": {
    "legal_codes": true,
    "court_practice": true,
    "grand_chamber": true
  }
}
```

**Response:**
```json
{
  "response": "📋 SITUATION SUMMARY...\n⚖️ APPLICABLE LAWS...",
  "citations": [
    {
      "article_number": "მუხლი 11",
      "code_name": "სისხლის სამართლის კოდექსი",
      "raw_text": "სისხლის სამართლის კოდექსი, მუხლი 11",
      "verified": true,
      "article_url": "https://matsne.gov.ge/..."
    }
  ],
  "retrieved_chunks": [
    {
      "chunk_id": "civil_code_45_1",
      "content": "მუხლი 45. ქონების უფლება...",
      "code_name": "სამოქალაქო კოდექსი",
      "article_number": "მუხლი 45",
      "article_title": "ქონების უფლება",
      "citation_text": "სამოქალაქო კოდექსი, მუხლი 45",
      "article_url": "https://matsne.gov.ge/...",
      "distance": 0.12
    }
  ],
  "credits_remaining": 4
}
```

> **Gotcha:** The response is in Georgian by default. If the user writes in English, the AI responds in English.

---

#### `WS /api/v1/chat/{conversation_id}/ws`
WebSocket streaming endpoint for real-time chat.

- **Auth:** None at connection level (send token in first message if needed)
- **Credits:** 1 (deducted server-side)

**Protocol:**

```javascript
// Client → Server
{"message": "ჩემს მეზობელს სახლი დავანგრიე...", "rag_config": {"legal_codes": true}}

// Server → Client (status updates)
{"type": "status", "message": "Searching laws..."}
{"type": "status", "message": "Found 42 relevant articles. Analyzing..."}

// Server → Client (content chunks)
{"type": "chunk", "content": "📋 SITUATION SUMMARY\n"}
{"type": "chunk", "content": "You described a property dispute...\n"}

// Server → Client (final message)
{
  "type": "done",
  "full_response": "📋 SITUATION SUMMARY...",
  "citations": [...],
  "chunk_count": 42
}

// Server → Client (error)
{"type": "error", "message": "An error occurred during analysis."}
```

```bash
# Test with wscat:
npm install -g wscat
wscat -c ws://localhost:8000/api/v1/chat/550e8400-e29b-41d4-a716-446655440000/ws
> {"message": "ჩემს მეზობელს სახლი დავანგრიე..."}
```

---

### Case Files

#### `POST /api/v1/case-files/build`
Build a structured defense case file from a conversation. Costs 3 credits.

- **Auth:** Required
- **Credits:** 3

```bash
curl -X POST http://localhost:8000/api/v1/case-files/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_id_token>" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "rag_config": {"legal_codes": true, "court_practice": true, "grand_chamber": true}
  }'
```

**Request Body:**
```json
{
  "conversation_id": "string",
  "rag_config": {"legal_codes": true, "court_practice": true, "grand_chamber": true}
}
```

**Response:**
```json
{
  "id": "660f9511-f30c-52e5-b827-557766551111",
  "title": "Property Dispute — Defense Case",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "facts": {"what_happened": "...", "when": "...", "where": "..."},
  "evidence": {"has": [...], "needs": [...]},
  "applicable_laws": {"favorable": [...], "unfavorable": [...], "procedural": [...]},
  "defense_strategies": [...],
  "prosecution_args": [...],
  "action_checklist": [...],
  "lawyer_brief": {...},
  "citations": [...],
  "rendered_text": "📁 DEFENSE CASE FILE...",
  "status": "draft",
  "user_notes": "",
  "created_at": "2026-05-09T02:00:00",
  "updated_at": "2026-05-09T02:00:00"
}
```

---

#### `GET /api/v1/case-files`
List user's case files.

- **Auth:** Required
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/case-files \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:**
```json
{
  "case_files": [
    {
      "id": "660f9511-f30c-52e5-b827-557766551111",
      "title": "Property Dispute — Defense Case",
      "status": "draft",
      "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-05-09T02:00:00",
      "updated_at": "2026-05-09T02:00:00"
    }
  ],
  "total": 1
}
```

---

#### `GET /api/v1/case-files/{id}`
Get a specific case file with all sections.

- **Auth:** Required
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/case-files/660f9511-f30c-52e5-b827-557766551111 \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:** Same shape as `POST /case-files/build`.

---

#### `PATCH /api/v1/case-files/{id}`
Update case file notes or status.

- **Auth:** Required
- **Credits:** 0

```bash
curl -X PATCH http://localhost:8000/api/v1/case-files/660f9511-f30c-52e5-b827-557766551111 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_id_token>" \
  -d '{"user_notes": "Called lawyer on May 10.", "status": "active"}'
```

**Request Body:**
```json
{"user_notes": "string (optional)", "status": "draft|active|resolved (optional)"}
```

**Response:** Full `CaseFileDetail` object.

---

#### `DELETE /api/v1/case-files/{id}`
Delete a case file.

- **Auth:** Required
- **Credits:** 0

```bash
curl -X DELETE http://localhost:8000/api/v1/case-files/660f9511-f30c-52e5-b827-557766551111 \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Response:** `204 No Content`

---

### Laws (Free — No Auth Required)

#### `GET /api/v1/laws/search`
Search laws by query text.

- **Auth:** None
- **Credits:** 0
- **Query Params:** `q` (required), `domain` (optional), `top_k` (default 20, max 100)

```bash
curl "http://localhost:8000/api/v1/laws/search?q=მუხლი%2011&top_k=5"
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "criminal_code_11_1",
      "content": "მუხლი 11. სისხლის სამართლის კოდექსის მიზანი...",
      "metadata": {"code_name": "სისხლის სამართლის კოდექსი", "article_number": "მუხლი 11"}
    }
  ],
  "query": "მუხლი 11",
  "total": 5
}
```

---

#### `GET /api/v1/laws/codes`
List all available legal codes.

- **Auth:** None
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/laws/codes
```

**Response:**
```json
{
  "codes": [
    {"id": "civil_code", "name_ka": "სამოქალაქო კოდექსი", "name_en": "Civil Code", "article_count": 1500},
    {"id": "criminal_code", "name_ka": "სისხლის სამართლის კოდექსი", "name_en": "Criminal Code", "article_count": 420}
  ],
  "total": 12
}
```

---

#### `GET /api/v1/laws/codes/{code_id}`
Get a specific legal code structure (books → chapters → articles).

- **Auth:** None
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/laws/codes/civil_code
```

---

#### `GET /api/v1/laws/articles/{article_id}`
Get all chunks for a specific article.

- **Auth:** None
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/laws/articles/civil_code_45
```

**Response:**
```json
{
  "article_id": "civil_code_45",
  "chunks": [
    {
      "chunk_id": "civil_code_45_1",
      "content": "მუხლი 45. ქონების უფლება...",
      "metadata": {"code_name": "სამოქალაქო კოდექსი", "article_number": "მუხლი 45"}
    }
  ],
  "total": 1
}
```

---

### RAG Collections

#### `GET /api/v1/rag/collections`
List available RAG collections with availability and chunk counts.

- **Auth:** None
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/rag/collections
```

**Response:**
```json
{
  "collections": [
    {
      "id": "georgian_laws",
      "name_ka": "საქართველოს კანონები",
      "description": "12 legal codes from matsne.gov.ge",
      "available": true,
      "chunk_count": 15338
    },
    {
      "id": "court_practice",
      "name_ka": "სასამართლო პრაქტიკა",
      "description": "Supreme Court rulings 2022-2026",
      "available": true,
      "chunk_count": 5197
    },
    {
      "id": "grand_chamber",
      "name_ka": "დიდი პალატის გადაწყვეტილებები",
      "description": "Grand Chamber binding decisions",
      "available": true,
      "chunk_count": 177
    }
  ]
}
```

---

### Questionnaire (Dynamic Intake)

> **Note:** These endpoints are implemented but not yet registered in `app/main.py` to avoid merge conflicts with parallel agents. See `backend/app/routes/questionnaire_router.py` for the router.

#### `POST /api/v1/questionnaire/{conversation_id}/generate`
Generate a domain-specific questionnaire for a conversation.

- **Auth:** Required
- **Credits:** 0

```bash
curl -X POST http://localhost:8000/api/v1/questionnaire/550e8400-e29b-41d4-a716-446655440000/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_id_token>" \
  -d '{"context": "Property dispute with neighbor", "domain": "civil"}'
```

**Response:**
```json
{
  "questions": [
    {
      "id": "q1",
      "question_text_ka": "რა მოხდა? მოკლედ აღწერეთ სიტუაცია.",
      "question_type": "text",
      "options": [],
      "required": true,
      "purpose": "Understand the basic facts",
      "legal_relevance": "Determines applicable legal domain",
      "sort_order": 0
    }
  ],
  "total": 6,
  "required_count": 5
}
```

---

#### `GET /api/v1/questionnaire/{conversation_id}`
Get the current questionnaire state.

- **Auth:** Required
- **Credits:** 0

```bash
curl http://localhost:8000/api/v1/questionnaire/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <firebase_id_token>"
```

---

#### `POST /api/v1/questionnaire/{conversation_id}/answer`
Submit an answer to a questionnaire question.

- **Auth:** Required
- **Credits:** 0

```bash
curl -X POST http://localhost:8000/api/v1/questionnaire/550e8400-e29b-41d4-a716-446655440000/answer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_id_token>" \
  -d '{"question_id": "q1", "answer": "მეზობელმა ჩემს მიწაზე ღობე ააშენა."}'
```

---

#### `POST /api/v1/questionnaire/{conversation_id}/skip`
Skip a non-required questionnaire question.

- **Auth:** Required
- **Credits:** 0

```bash
curl -X POST http://localhost:8000/api/v1/questionnaire/550e8400-e29b-41d4-a716-446655440000/skip \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_id_token>" \
  -d '{"question_id": "q3"}'
```

---

## RAG Collection Config Usage

The `rag_config` field controls which knowledge sources are searched. It can be sent with any chat or case-building request.

```json
{
  "rag_config": {
    "legal_codes": true,
    "court_practice": true,
    "grand_chamber": true
  }
}
```

### Rules
- All fields default to `true` if omitted.
- If all are `false`, `legal_codes` is forced to `true` (always search at least legal codes).
- Changes per-request — no persistent user preference stored.

### When to Toggle Collections

| Scenario | Recommended Config |
|----------|-------------------|
| General legal question | All enabled |
| Criminal defense | `legal_codes: true, court_practice: true` |
| Constitutional rights | `legal_codes: true, grand_chamber: true` |
| Quick statute lookup | `legal_codes: true, court_practice: false, grand_chamber: false` |
