# ⚡ Workflow: Performance Optimization

> **Use when:** An endpoint is slow, pipeline latency is high, or resource usage is concerning.
> **Philosophy:** Measure first, optimize second. Never optimize without a baseline.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for quality standards.
Read `.agents/rag_specialist/context.md` if this involves the RAG pipeline.

## Performance Issue

**What's slow:** [ENDPOINT, FUNCTION, OR PIPELINE STAGE]

**Current performance:** [MEASURED VALUE — e.g., "chat/send takes 203 seconds"]

**Target performance:** [GOAL — e.g., "< 15 seconds with streaming"]

**Context:** This runs [HOW OFTEN] with [DATA SIZE].

## Execute This Workflow:

### Phase 1 — Profile (MANDATORY — no guessing)
1. Add timing instrumentation to each stage:
   ```python
   import time
   t0 = time.perf_counter()
   # ... operation ...
   elapsed = time.perf_counter() - t0
   logger.info("stage_timing", stage="vector_search", elapsed_ms=elapsed*1000)
   ```
2. Run the slow operation 3 times, collect timings
3. Build a breakdown table:
   | Stage | Time (ms) | % of Total | Optimizable? |
   |-------|-----------|-----------|--------------|
4. Identify the #1 bottleneck (usually 80/20 rule applies)

### Phase 2 — Analyze (STOP — show me the breakdown)
5. For the top bottleneck, explain:
   - WHY it's slow (not just "it's slow")
   - What the theoretical minimum time is
   - What's causing the gap between current and theoretical
6. Propose optimizations ranked by: impact × ease

### Phase 3 — Optimize (after I approve)
7. Apply the top optimization ONLY (one at a time)
8. Re-measure with same instrumentation
9. Compare before/after in a table
10. If target not met, propose next optimization

### Phase 4 — Verify
11. Run full test suite (optimizations must not break behavior)
12. Check edge cases (empty input, maximum load)
13. Remove instrumentation (or leave behind structured log timings)

### Rules:
- NEVER optimize without measuring first
- NEVER optimize two things at once
- Cache invalidation is hard — document your caching strategy
- Async is not always faster — profile to verify
- The fastest code is the code that doesn't run (can you skip a stage?)
```
