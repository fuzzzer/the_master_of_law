# Grounding Hardening Plan — კანონის ოსტატი

> Goal: a **fully grounded, foolproof law master agent**.
> Context: the law_corpus pipeline (fetch → scrape → parse → chunk → embed, incl.
> `run_incremental_update.sh`) already exists and stays as-is. This plan adds the
> **grounding mechanisms on top of it** — the audit (2026-07-19, trace `f9112db5…`)
> showed similarity-RAG alone is a *finder*, not a *verifier*.
>
> Verification substrate for every phase: the transparency suite
> (`pipeline_traces` + `/api/v1/traces/dashboard`).

---

## Core idea — three grounding mechanisms beyond RAG

| Mechanism | Job | Why RAG can't do it |
|---|---|---|
| **A. Deterministic article lookup** — `(code, article, paragraph) → full consolidated text` over the pipeline's parsed JSON | Verify & complete citations before the user sees them | Similarity search can miss the exact article the model cites (proven in audit: Labor Code 48 never retrieved) |
| **B. Agentic navigation tools** — expose `law_browser_service` (`browse_code`, `get_article`) to Gemini as tools | Let the model *navigate* to law like a lawyer when retrieval is thin | One-shot embedding match has no second chance; a tool call does |
| **C. Whole-code context injection** — for the classified domain, inject the entire relevant code (codes are small; court practice stays RAG) via `context_cache_service` | Make statute-retrieval failure impossible | No retrieval step → no retrieval failure |

RAG remains the finder for court practice and cross-domain discovery. A+B+C make statutes deterministic.

---

## Phase 0 — Audit P0/P1 fixes

| # | Task | Where | Verify |
|---|------|-------|--------|
| 0.1 | Per-collection retrieval: separate top-k per collection (laws 40 / practice 25 / chamber 10), merge after | `rag_retrieval_service._stage_1_vector_search` | Golden test: pregnancy-dismissal Q → Labor Code chunk in `rag_final_selection` trace step |
| 0.2 | Deadlines rule: legal-action advice MUST state deadlines found in sources or flag them unverified | `app/prompts/chat.py`, `advocate.py` | Audit Q re-run → 30-day court deadline present |
| 0.3 | Threshold domain gate: inject threshold entries only when domain matches | `threshold_service.search` | Labor Q trace shows zero `threshold_criminal_*` chunks |
| 0.4 | Court-case citation duty in prompt (verification in Phase 3) | prompts | Audit Q response names ას-XXXX-YYYY cases |
| 0.5 | Sub-article extraction: `ARTICLE_PATTERN` captures "48.8", "48-ე მუხლის მე-8 ნაწილი" | `citation_service` | Unit tests |

---

## Phase 1 — Grounding mechanisms A/B/C

**1.1 Article Store (mechanism A)**
- Build SQLite (+FTS5) `article_store.db` from the pipeline's existing `parsed/*.json`
  as a **pipeline output step** (added to `run_full_pipeline.sh` / incremental update —
  no new fetching/parsing, just a new artifact).
- New backend `article_store_service`: `get_article(code, article, paragraph=None)`,
  `fts_search(query)`. Backs `search_law`, `law_browser_service`, and Phase-2 verification.
- Enhancement inside the existing parser (not a new pipeline): populate the already-present
  but empty `paragraphs` and `cross_references` fields from raw HTML — enables
  sub-article grounding ("48.8") and related-article expansion (48 ↔ 47).
- Verify: exact lookup returns full art. 48 with 9 paragraphs and matsne anchor.

**1.2 Navigation tools (mechanism B)**
- New Gemini tool declarations: `get_article(code, article)`, `browse_code(code, chapter?)`
  wrapping `law_browser_service` / article store; add to `ALWAYS_TOOLS`.
- Prompt guidance: "თუ საჭირო მუხლი კონტექსტში არ არის — მოიძიე ხელსაწყოთი."
- Verify: disable laws collection → trace shows the model calling `get_article` and
  answering correctly anyway.

**1.3 Whole-code injection (mechanism C)**
- After domain classification, if the domain maps to ≤2 codes and their combined size fits
  budget: inject full code text (from article store) instead of statute chunks;
  cache via `context_cache_service`. Court practice chunks continue via RAG.
- Feature flag `FULL_CODE_INJECTION` + per-code size whitelist (labour, admin offences … yes;
  tax code … no).
- Verify: labor Q trace shows `full_code_injected` step; token cost within budget; A/B the
  audit question — art. 47 prohibition now appears in answers.

---

## Phase 2 — Generation contract (needs 1.1)

**2.1 Retrieval-repair loop** (the audit's core lesson): in `_phase_3_verify`, a citation that is
NOT in context → fetch full article via store → re-invoke model to confirm/correct against real
text → only then respond. Kills the true-but-unretrieved failure mode.
Verify: laws collection disabled → answer still article-accurate; `retrieval_repair` trace step.

**2.2 Anchored-claims protocol**: legal assertions must carry `[n]` source markers; post-processor
flags/strips unanchored legal claims. Verify: unanchored-claim rate metric < 5%.

**2.3 Faithfulness pass**: one batched Flash check — each substantive sentence supported /
unsupported / general — annotate or correct. Verify: seeded-hallucination tests.

**2.4 Uncertainty policy**: statute-type question with zero statute grounding (no chunks, no tool
hit, no injection) → answer must open with explicit disclaimer. Verify: forced-empty test.

---

## Phase 3 — Verification net

**3.1 Court-case citation verification**: extract `ას-XXXX-YYYY` / `ბს-XXX` / №-forms; verify
against `court_practice` metadata; hallucinated case numbers get Phase-3 correction.
**3.2 Sub-article verification** (needs 1.1 paragraphs): verify "48.8" against paragraph 8.
**3.3 (optional) Live drift sampling**: weekly hash-compare of N random store articles vs live
matsne — belt-and-suspenders on top of the incremental-update pipeline; surfaces silent
scrape failures on the trace dashboard.

---

## Phase 4 — Continuous evaluation (can start any time)

**4.1 Grounding metrics from traces** (nightly): % citations verified, statute-grounding rate
(chunks OR tool call OR injection), deadline coverage, unanchored-claim rate → dashboard panel.
**4.2 Golden retrieval/grounding suite**: ~30 Q→must-ground-in-article pairs across 9 domains,
run in CI (`eval/golden_retrieval.yaml`).
**4.3 Scheduled auto-audit**: weekly agent replays the audit rubric over recent session exports,
files findings to `.tasks/audits/`.

---

## Order

```
Phase 0 ───────────► first
Phase 1 (A/B/C) ───► foundation      Phase 4 ──► start 4.2 now, runs forever
Phase 2 ───────────► needs 1.1
Phase 3 ───────────► 3.1 anytime; 3.2 needs 1.1
```

Execution: single continuous run, phase by phase. After Phase 0 + 1.1 + 2.1, the audit's failure mode (true citation, never
retrieved, verified by luck) is structurally impossible; after 1.3, statute retrieval
failure itself disappears for whitelisted codes.
