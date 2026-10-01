# User Notes

- Focus on perceived speed first (streaming the response) to make the app feel instantly responsive.
- RAG is currently taking way too long based on recent logs:
  - `rag_stage_0` (Expansion): ~15s-18s
  - `rag_stage_1` (Vector): ~11s-12s
  - Reranking/Finalizing: ~39s
  - Total pipeline time before generation starts: > 1 minute.
- Look into parallelizing the retrieval steps and optimizing the reranker.
- Furthermore, `case_analysis` (the actual Gemini generation phase) takes another ~45 seconds (`case_build_auto_rag` at 14:20:24 to `case_analysis_done` at 14:21:09). Total time is upwards of 2 full minutes. Streaming is absolutely vital here.
- Make sure that reducing context size or speeding up reranking does not negatively impact the accuracy of the legal analysis.
