# Specs: Legal Thresholds in RAG + Hard Guardrails

---

## Behavioral Specifications

### Legal Thresholds

| Behavior | Specification |
|----------|---------------|
| Data scope | Criminal Code thresholds first; expand to civil/labor after validation |
| Threshold types | drug quantities, sentences, fines, deadlines, monetary limits, age limits |
| Accuracy requirement | Every threshold must cite its exact source article and paragraph |
| Freshness | Each threshold entry has a `last_verified` date. Flag entries older than 6 months. |
| Retrieval boost | When a query involves quantities/amounts, threshold chunks get 1.5x rerank score |
| Missing data | If no threshold data exists for a query, AI must NOT invent numbers — say "specific thresholds not in our database" |

### Hard Guardrails

| Behavior | Specification |
|----------|---------------|
| Latency budget | < 300ms for guardrail classification (Gemini Flash) |
| False positive rate | < 5% — legal questions must NOT be blocked |
| False negative rate | < 10% — most off-topic messages should be caught |
| Credit cost | 0 credits — guardrails are free (they save credits by preventing unnecessary RAG) |
| Bypass | ADMIN users skip guardrails entirely |
| Logging | Every decision logged with: `user_id`, `message_hash` (not full text for privacy), `decision`, `confidence` |
| Greeting handling | "გამარჯობა" (hello) → respond with greeting + prompt to describe legal situation |
| Edge case | Legal terminology in casual phrasing (e.g., "my boss fired me") must be classified as `legal` |

---

## Technical Constraints

### Threshold Data Storage

**Option A — Enriched chunks in `georgian_laws` (recommended):**
- Add threshold chunks as additional documents in the existing collection
- Metadata tag: `"chunk_type": "threshold"` to distinguish from statute text
- Pro: no new collection, no changes to `RAGCollectionConfig`
- Con: might dilute regular law retrieval if too many threshold chunks

**Option B — New `legal_thresholds` collection:**
- Separate ChromaDB collection
- Requires updating `RAGCollectionConfig` and all RAG pipeline stages
- Pro: clean separation, easy to manage independently
- Con: more code changes, another collection to maintain

**Decision:** Start with Option A. Migrate to Option B only if retrieval quality degrades.

### Threshold Chunk Schema
```python
class ThresholdChunk(BaseModel):
    chunk_type: Literal["threshold"] = "threshold"
    code_name: str                    # e.g., "criminal_code"
    article_number: str               # e.g., "260"
    threshold_type: str               # e.g., "drug_quantity", "sentence_range", "filing_deadline"
    description_ka: str               # Georgian description
    values: dict[str, str]            # structured threshold values
    consequence_ka: str               # what happens at each threshold
    source_url: str                   # matsne.gov.ge URL
    last_verified: date               # when data was last confirmed accurate
```

### Guardrail Service

```python
class GuardrailService:
    PROMPT = """You are a legal topic classifier for a Georgian law application.
    Classify the user's message into exactly one category:
    - "legal": related to Georgian law, legal rights, court procedures, legal situations
    - "greeting": hello, how are you, etc.
    - "off_topic": weather, sports, recipes, coding, anything non-legal
    - "harmful": requests for illegal activity, threats, abuse
    
    Respond with JSON: {"category": "...", "confidence": 0.0-1.0}
    
    IMPORTANT: Err on the side of "legal". If there's any chance the message 
    relates to a legal situation, classify as "legal"."""

    async def classify(self, message: str) -> GuardrailDecision:
        # Use Gemini Flash for speed
        # Temperature: 0.0 (deterministic classification)
        # Max tokens: 50 (just need the JSON)
        ...
```

### Integration Point

```python
# In chat_service.py or chat_router.py, BEFORE RAG:
guardrail = await guardrail_service.classify(message)
if guardrail.category == "harmful":
    return blocked_response()
if guardrail.category == "off_topic":
    return redirect_response()  # "I can only help with legal questions"
if guardrail.category == "greeting":
    return greeting_response()  # "Hello! Describe your legal situation"
# else: proceed with RAG pipeline
```

### Gemini Model Usage
- **Guardrails:** `gemini-2.0-flash` (cheap, fast, < 300ms)
- **Threshold embedding:** `gemini-embedding-001` (same as rest of corpus)
- **Analysis:** `gemini-3.1-pro` (no change — only runs after guardrails pass)

### Response Messages (Georgian)

| Category | Response |
|----------|----------|
| `greeting` | "გამარჯობა! 👋 მე ვარ კანონის ოსტატი — თქვენი იურიდიული ასისტენტი. აღწერეთ თქვენი სამართლებრივი სიტუაცია და დაგეხმარებით." |
| `off_topic` | "ბოდიში, მე მხოლოდ სამართლებრივ საკითხებში შემიძლია დახმარება. გთხოვთ, აღწერეთ თქვენი იურიდიული სიტუაცია." |
| `harmful` | "ბოდიში, ამ ტიპის მოთხოვნაზე პასუხის გაცემა არ შემიძლია." |

### Testing

- 20 test messages: 10 legal (Georgian), 5 off-topic, 3 greetings, 2 harmful
- All test messages in `tests/fixtures/guardrail_test_messages.json`
- Each message has expected classification
- Mock Gemini Flash responses in unit tests
- Real Gemini Flash in integration tests (flagged as slow)
