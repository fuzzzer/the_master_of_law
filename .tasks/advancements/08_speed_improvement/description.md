# Task: Generation Speed Improvement

> **Covers:** Backend optimizations, streaming responses, infrastructure tuning
> **Dependencies:** None

---

## Purpose

Currently, AI generations take too long, leading to a degraded user experience. The goal of this task is to significantly reduce the time it takes for users to receive answers from the legal AI. This includes backend pipeline optimization, potential query restructuring, and enabling streaming to provide immediate feedback to the user while the full generation completes.

This ensures the platform feels snappy and responsive, which is critical for user trust.

---

## Multi-Step Guide

### Milestone 1: Benchmarking & Profiling
1. Add telemetry/timing logs to each stage of the RAG pipeline (Expand → Vector → FullText → Merge → Rerank).
2. Measure Gemini API call latency.
3. Identify the main bottlenecks (e.g., is it retrieval, reranking, or Gemini generation?).
4. **Verify:** Clear metrics are available showing time spent in each phase.

### Milestone 2: Streaming Generation
1. Implement streaming generation in `VertexAIClient`.
2. Update backend endpoints to yield Server-Sent Events (SSE) or WebSockets for streaming text.
3. Update Flutter frontend to consume the stream and display characters as they arrive (typewriter effect).
4. **Verify:** Users see the first token of the response within 2-3 seconds, even if the full answer takes longer.

### Milestone 3: RAG Pipeline Optimization
1. Optimize retrieval steps:
   - Reduce top-K if it doesn't degrade quality.
   - Run parallel queries instead of sequential.
   - Cache common query results in Redis.
2. Optimize reranking (e.g., use a faster/smaller model or limit the number of documents passed to the reranker).
3. **Verify:** Overall RAG pipeline time (excluding Gemini generation) is reduced by at least 30%.

### Milestone 4: Prompt & Context Tuning
1. Review prompts to ensure they are concise.
2. Reduce the context window size by providing only the most relevant snippets.
3. Explore Gemini model parameters (e.g., adjusting temperature, max output tokens) to optimize speed.
4. **Verify:** Generation speed is faster without sacrificing the quality of legal advice.

### Milestone 5: Testing & Verification
1. Run end-to-end load tests.
2. Compare new latency metrics against baseline.
3. Ensure no regression in accuracy or legal grounding.
4. **Verify:** Significant measurable improvement in perceived and actual response times.
