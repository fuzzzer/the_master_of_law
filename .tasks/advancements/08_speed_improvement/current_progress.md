# Current Progress: Speed Improvement

## Status
- **Phase:** Planning / Benchmarking
- **Progress:** 5%

## Completed Actions
- [x] Task created.
- [x] Initial bottleneck identification from logs (RAG pipeline stages take ~15s, ~12s, and ~40s respectively).

## Pending Actions
- [ ] Investigate and parallelize `rag_stage_0` (Query Expansion).
- [ ] Optimize or replace the reranker in `rag_stage_3` to reduce the ~40s delay.
- [ ] Implement SSE/Streaming for Gemini API responses on the backend.
- [ ] Update Flutter app to consume streamed responses and show precise loading states.
- [ ] Test and measure latency improvements.
