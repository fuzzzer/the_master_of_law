# 🔬 Improvement Ideas & Research

> Collected during PoC testing (2026-05-04). Prioritized by impact/effort.

---

## 1. Fine-Tuning Strategy (Phase 2-3)

### When to Fine-Tune
- **Not yet.** RAG + prompt engineering already produces excellent results.
- Fine-tune after collecting **500+ real user conversations** with feedback.
- Need consistent patterns of failure that prompt engineering can't fix.

### What to Fine-Tune
| Target | Method | Training Data Needed | Expected Benefit |
|--------|--------|---------------------|------------------|
| Gemini (supervised) | Vertex AI tuning | 500+ Georgian legal Q&A pairs | Tone, format, Georgian legal fluency |
| Domain classifier | Lightweight model | 200+ labeled queries | Faster routing, cheaper than Gemini for classification |

### What You Can't Fine-Tune
- `gemini-embedding-001` — no fine-tuning API available
- Alternative: train a custom embedding model (out of scope for MVP)

### Fine-Tuning Data Collection Plan
1. Ship the app with conversation logging (with user consent)
2. Tag conversations: correct/incorrect, helpful/unhelpful
3. Extract high-quality Q&A pairs from successful conversations
4. Create "golden" test set of 50+ scenarios with expert-verified answers
5. Fine-tune when you have enough data to see measurable improvement

---

## 2. Higher ROI Improvements (Do Before Fine-Tuning)

### A. Retrieval Quality
- **Better chunking overlap** — current 12% may miss cross-article arguments
- **Hybrid search tuning** — full-text search returned 0 hits in PoC (index keys are Georgian article names like "მუხლი 45", not semantic terms). Consider building a proper Georgian keyword index
- **Cross-reference expansion** — when retrieving article 260, auto-fetch articles it references (e.g., 273, 63)
- **Chunk metadata enrichment** — add `legal_domain` tags to improve filtered search

### B. Prompt Engineering
- **Few-shot examples** — add 2-3 example analyses in the system prompt for consistent structure
- **Chain-of-thought** — add "think step by step about applicable defenses" before the structured response
- **Temperature tuning** — test 0.05 vs 0.1 vs 0.2 for legal accuracy vs. creativity tradeoff

### C. Speed Optimization
- **Parallel embedding** — batch all queries into one API call (gemini-embedding-001 supports batched input)
- **Cache query embeddings** — same/similar questions don't need re-embedding
- **Skip rerank for small result sets** — if <30 unique chunks, send directly to analysis
- **Streaming** — WebSocket response streaming in the backend (already planned)

### D. Context Caching (Vertex AI)
- Cache the system prompt + frequently-used law chunks as `CachedContent`
- Reduces cost by ~50% for repeated conversations
- Particularly useful for the legal analysis system prompt (large, static)

---

## 3. Corpus Expansion

### Missing P1 Laws (identified during validation)
- [ ] `entrepreneurial_law` — Law on Entrepreneurs
- [ ] `consumer_rights_law` — Consumer Rights Law
- Not available via current matsne.gov.ge scraper — may need different source URL or format

### Future P2 Laws to Add
- Tax Code amendments / regulations
- Administrative sanctions regulations
- Court procedural guidelines
- Supreme Court precedent summaries (not legislation, but highly valuable for defense strategies)

---

## 4. Evaluation Framework (Build Before Fine-Tuning)

### Golden Test Set (50+ scenarios)
Create expert-verified test cases across domains:
- Criminal defense (10 cases)
- Civil disputes (10 cases)
- Labor law (8 cases)
- Administrative violations (8 cases)
- Property/inheritance (7 cases)
- Data protection / personal rights (7 cases)

### Metrics to Track
- **Citation accuracy** — % of cited articles that actually exist and are relevant
- **Coverage** — does the response find ALL applicable defenses?
- **Actionability** — are the "next steps" concrete and correct?
- **Tone** — does it advocate for the user without misleading?
- **Latency** — total pipeline time (target: <15s with streaming)

### Automated Testing
- Run `poc_tester.py --test-suite` weekly as a regression check
- Compare outputs across model versions / prompt changes
- Flag any response that fails to include the disclaimer

---

## 5. PoC Observations (2026-05-04)

### What Worked Well
- Query expansion generated excellent formal Georgian legal terms from casual input
- Vector search found highly relevant chunks (260, 273, 63 — exactly right for drug possession case)
- Legal analysis structure was clear: situation → laws → strategies → risks → next steps
- Citations were grounded in real corpus data with valid matsne.gov.ge URLs
- Advocacy tone was strong without being misleading

### What Needs Improvement
- **Speed** — 203s total is too slow for real-time use (mostly embedding rate limits)
- **Full-text search** — returned 0 hits because index keys are article names, not legal terms
- **Rerank** — sending 272 candidates is wasteful; pre-filter by distance threshold
- **No clarifying questions** — jumped straight to analysis without asking about circumstances
- **Single-turn only** — no memory of previous conversation context
