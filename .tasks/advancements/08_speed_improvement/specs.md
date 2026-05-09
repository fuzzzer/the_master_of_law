# Specs: Generation Speed Improvement

## Goals
- Drastically reduce Time to First Token (TTFT).
- Reduce overall Time to Complete (TTC) for AI responses.
- Optimize the RAG pipeline to minimize overhead before generation starts.
- Implement UI feedback to keep users engaged during processing.

## Current Bottlenecks
Based on recent logs:
- `rag_stage_0` (Query Expansion/Generation) takes ~15-18 seconds.
- `rag_stage_1` (Vector Search) takes ~12 seconds.
- `rag_stage_3` to `rag_pipeline_done` takes ~35-50 seconds (Reranking / Finalizing).
- Overall RAG pipeline (before LLM answers) takes ~1 minute or more.
- Synchronous RAG pipeline operations block the main response.
- Waiting for the entire Gemini generation to complete before sending the response to the client.

## Proposed Changes
1. **Parallel Processing:**
   - Run ChromaDB vector searches in parallel across different collections or chunked queries.
2. **Optimize `rag_stage_0`:**
   - Review the prompt for query generation, see if a smaller/faster model or fewer queries can be generated.
3. **Optimize `rag_stage_3` (Reranking/Merge):**
   - Reranking seems to take a massive amount of time (~35-40s). Consider batching, parallelizing, or using a faster reranker.
4. **Streaming Generation:** 
   - Backend: Use `stream=True` in Gemini API calls once RAG is done.
   - Transport: SSE (Server-Sent Events) or WebSocket for real-time text delivery.
   - Frontend: Stream handler in `CaseDetailCubit` or `ConsultationCubit`.
5. **Caching:**
   - Redis caching for identical/similar query expansions and retrievals.
6. **UI/UX Polish:**
   - Skeleton loaders during the retrieval phase indicating exactly which stage is running.
   - Smooth text rendering during the streaming phase.

## Dependencies
- Backend FastAPI router updates.
- RAG retrieval service parallelization.
- Flutter Chat UI stream integration.
