# 🎯 Current Priorities

> What matters most RIGHT NOW. Update this whenever priorities shift.
> AI agents should read this first to understand what to focus on.

---

## 🔴 Critical (This Week)

1. **Test the full RAG chat pipeline** end-to-end via Docker
2. **Test all 25 API endpoints** — at least one happy-path curl for each
3. **Fix full-text search** — currently returns 0 results
4. **Create the Flutter app design system** — prompt 03 is ready, need execution

## 🟡 Important (This Month)

5. **Speed optimization** — bring RAG pipeline from 203s to <15s
6. **Deploy to production VPS** — follow PRODUCTION_SETUP.md
7. **Flutter app MVP** — implement the design system in Flutter
8. **Install structlog** — upgrade from stdlib fallback logger

## 🟢 Nice to Have (Backlog)

9. Corpus expansion (missing P1 laws: entrepreneurial, consumer rights)
10. Evaluation framework with golden test set
11. Context caching via Vertex AI CachedContent
12. Fine-tuning data collection pipeline

---

## Anti-Priorities (Explicitly NOT doing now)

- ❌ Fine-tuning Gemini — RAG + prompts work well enough for MVP
- ❌ Custom embedding model — gemini-embedding-001 is excellent
- ❌ Multi-region deployment — single VPS is fine for Georgian market
- ❌ Payment/billing system — free credits first, monetize later
