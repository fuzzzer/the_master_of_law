# 🎯 RAG Specialist — Skill Context

> **When to load:** Improving search quality, retrieval accuracy, reranking, or the RAG pipeline.

---

## Pipeline Architecture

```
User Message → [S0] Query Expansion → [S1] Vector Search → [S2] Full-Text Search
  → [S3] Merge/Dedup → [S4] Gemini Rerank → Legal Analysis → Citation Verification
```

## Corpus Facts

- 9,450 chunks, 1,525 articles, 12 Georgian legal codes
- Embedding: `gemini-embedding-001`, 768-dim, cosine distance
- Corpus task_type: `RETRIEVAL_DOCUMENT` / Query task_type: `RETRIEVAL_QUERY`
- **NEVER mix task types** — degrades quality ~15-20%

## Known Issues

### Full-Text Search Returns Zero
Index keys are article titles (მუხლი 177), not semantic terms. Vector search alone is sufficient for 9,450 docs. Skip for MVP.

### Slow Pipeline (~203s)
Root cause: embedding rate limits (~155s waiting). Fix: cache embeddings, batch API calls, pre-filter before rerank (distance > 0.4 = drop).

### Missing Cross-References  
Article 260 references 273 and 63. After retrieval, extract მუხლი N references and fetch those too.

## Optimization Priorities

1. **Cache query embeddings** in Redis (TTL: 1hr)
2. **Pre-filter by cosine distance** before rerank (> 0.4 = irrelevant)
3. **Stream Gemini analysis** — perceived latency drops dramatically
4. **Parallel search stages** — vector + full-text concurrently
5. **Batch embed** — single API call for all expanded queries

## Quality Targets

| Metric | Target |
|--------|--------|
| Recall@20 | >85% |
| Precision@20 | >60% |
| Citation accuracy | 100% |
| Latency P50 | <12s |
| Latency P95 | <20s |
