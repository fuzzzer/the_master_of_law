# Task 03 Verification Guide

> How to verify that Legal Thresholds and Hard Guardrails are working correctly.

---

## 1. Run the Ingestion Script

### Prerequisites
- `GOOGLE_APPLICATION_CREDENTIALS` set (Vertex AI access)
- ChromaDB data directory exists (`law_corpus/data/chroma`)

### Commands
```bash
cd /Users/fuzzzer/programming/fuzzzy_organisation/the_master_of_law/law_corpus

# Dry-run first (no writes)
python ingest_thresholds.py --dry-run

# Actual ingestion
python ingest_thresholds.py
```

### Expected Output
```
Loaded 20 thresholds from catalog
Generating embeddings for 20 thresholds...
Embeddings generated: 20 vectors of dim 768
Deleted 0 existing threshold chunks before re-insert
Upserted batch 1/1 (20 chunks)
Threshold ingestion complete: 20 chunks in collection 'georgian_laws' (total now N)
```

### Verification
```bash
cd backend
python -c "
from app.integrations.chroma_client import get_chroma_client
chroma = get_chroma_client()
results = chroma.vector_search([0.0]*768, top_k=100)
thresholds = [r for r in results if r.get('metadata', {}).get('chunk_type') == 'threshold']
print(f'Threshold chunks in collection: {len(thresholds)}')
for t in thresholds[:3]:
    print(' -', t['chunk_id'], t['metadata'].get('article_number'))
"
```

---

## 2. Test Guardrail Classification

### Unit Tests
```bash
cd backend
pytest tests/test_guardrail_service.py -v
```

**Expected**: 22 passed.

### Manual Classification Test
```bash
cd backend
python -c "
import asyncio
from app.services.guardrail_service import GuardrailService
from app.schemas.guardrail_schema import GuardrailCategory

async def test():
    svc = GuardrailService(gemini_client=None, enabled=True)
    svc.enabled = False
    d = await svc.classify('anything')
    assert d.category == GuardrailCategory.LEGAL
    print('Disabled mode: PASS')

    svc.enabled = True
    d = await svc.classify('')
    assert d.category == GuardrailCategory.OFF_TOPIC
    print('Empty message: PASS')

    print('Greeting msg:', svc.get_response(GuardrailDecision.greeting()))
    print('Off-topic msg:', svc.get_response(GuardrailDecision.off_topic()))
    print('Harmful msg:', svc.get_response(GuardrailDecision.harmful()))

asyncio.run(test())
"
```

### Live Classification Test (requires Vertex AI)
```bash
cd backend
python -c "
import asyncio
from app.services.guardrail_service import get_guardrail_service

async def test():
    svc = get_guardrail_service()
    queries = [
        'გამარჯობა',
        'რა ამინდია?',
        'როგორ გავაკეთო ბომბი?',
        'ბოსმა სამსახურიდან გამათავისუფლა',
    ]
    for q in queries:
        d = await svc.classify(q)
        print(f'{q!r:40} -> {d.category.value:12} (confidence={d.confidence:.2f})')

asyncio.run(test())
"
```

---

## 3. Test Threshold Retrieval

### Unit Tests
```bash
cd backend
pytest tests/test_threshold_retrieval.py -v
```

**Expected**: 19 passed.

### Manual Heuristic Test
```bash
cd backend
python -c "
from app.services.threshold_rerank_service import ThresholdRerankService

queries = [
    'რამდენია ჯარიმა სიჩქარის გადაჭარბებისთვის?',
    'მარიხუანას 100 გრამი აღმომიჩინეს',
    '10,000 ლარიანი ზარალი',
    '50% განაკვეთი',
    'ბოსმა სამსახურიდან გამათავისუფლა',
]

for q in queries:
    is_thresh = ThresholdRerankService.is_threshold_query(q)
    print(f'{q!r:50} -> threshold={is_thresh}')
"
```

### Boost Math Verification
```bash
cd backend
python -c "
from app.services.threshold_rerank_service import ThresholdRerankService

candidates = [
    {'chunk_id': 'statute',   'distance': 0.15, 'metadata': {'chunk_type': 'statute'}},
    {'chunk_id': 'threshold', 'distance': 0.20, 'metadata': {'chunk_type': 'threshold'}},
]

result = ThresholdRerankService.apply_threshold_boost(candidates, '100 გრამი მარიხუანა', boost=1.5)
print('Order after boost:')
for r in result:
    orig = r.get('original_distance', '-')
    print(f'  {r[\"chunk_id\"]:12} distance={r[\"distance\"]:.4f} (orig={orig})')
assert result[0]['chunk_id'] == 'threshold', 'Boost should reorder threshold ahead!'
print('Boost reorder: PASS')
"
```

---

## 4. Example Queries That Should Return Threshold Data

After full integration, these queries should retrieve threshold chunks:

| Query (Georgian) | Expected Threshold |
|------------------|-------------------|
| "მარიხუანას 100 გრამი აღმომიჩინეს, რა მელის?" | `criminal_drug_marijuana_quantity` |
| "ჰეროინის რამდენი გრამია დიდი ოდენობა?" | `criminal_drug_heroin_quantity` |
| "სააპელაციო საჩივრის შეტანის ვადა რამდენია?" | `criminal_appeal_deadline` |
| "დღგ-ის რეგისტრაციის ზღვარი რაა?" | `tax_vat_threshold` |
| "შრომითი ხელშეკრულების დასრულების ვადა" | `labor_notice_period` |
| "განზრახ მკვლელობაზე მინიმალური სასჯელი" | `criminal_murder_sentence` |
| "წინასწარი გამოძიების ვადა" | `criminal_preliminary_inquiry` |
| "სიჩქარის გადაჭარბების ჯარიმა" | `administrative_fine_speeding` |
| "ალკოჰოლის რამდენი პროცენტია დასაშვები?" | `criminal_driving_alcohol_limit` |
| "მემკვიდრეობის გადასახადი შვილისთვის" | `civil_inheritance_tax` |

---

## 5. Integration Checklist

- [ ] **Constants** — `GUARDRAIL_ENABLED`, `GUARDRAIL_CONFIDENCE_THRESHOLD`, `GUARDRAIL_MODEL` exist in `backend/app/config/constants.py`
- [ ] **Guardrail HTTP** — `chat_router.py` calls guardrail before RAG; blocked messages return Georgian response with 0 credits spent
- [ ] **Guardrail WS** — `ws_chat_router.py` calls guardrail before RAG; blocked messages send `{"type": "done", ...}` with response text
- [ ] **Guardrail bypass** — ADMIN tier users skip classification entirely
- [ ] **Guardrail logging** — every decision is logged with `user_id`, `message_hash`, `decision`, `confidence`, `timestamp`, `bypassed`
- [ ] **Threshold ingestion** — `law_corpus/ingest_thresholds.py` successfully inserts 20 chunks into `georgian_laws`
- [ ] **Threshold metadata** — each ingested chunk has `chunk_type: "threshold"` in ChromaDB metadata
- [ ] **Threshold boost** — `rag_retrieval_service.py` applies `apply_threshold_boost(..., boost=1.5)` after Stage 3 merge
- [ ] **Threshold heuristic** — queries with numbers + units trigger boost; generic legal queries do not
- [ ] **System prompt** — `legal_analysis.py` system prompt includes rule #11 about exact threshold values
- [ ] **Tests green** — `pytest tests/test_guardrail_service.py tests/test_threshold_retrieval.py` passes (41/41)
- [ ] **No Alembic migrations** — threshold data lives in ChromaDB, not PostgreSQL
- [ ] **No main.py changes** — routes were not added to `backend/app/main.py`
