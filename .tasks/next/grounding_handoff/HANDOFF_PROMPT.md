# HANDOFF PROMPT — Grounding Hardening Executor

You are the **implementing agent** for the grounding-hardening initiative of ბუნდოვანი კანონი
(Fuzzzy Law) — an AI legal advocate for Georgian citizens. A planner/debugger agent has
already audited the live system, built a pipeline transparency suite for you to verify with,
and produced the plan you will now execute **end to end in this run**.

## Your mission

Execute every phase of `.tasks/next/grounding_hardening_plan.md` (Phases 0 → 4), then run the
**final certification audit** proving the system gives grounded, correct, complete Georgian
legal advice. You are done only when certification passes or every failure is documented with
root cause.

## Mandatory reading order (before ANY code)

1. `CLAUDE.md` (repo root) — project rules; follow its context-file table.
2. `.agents/context/mindset_and_principles.md` — non-negotiable coding principles.
3. `.agents/context/backend.md` — backend map (includes the transparency/trace suite section).
4. `.tasks/next/grounding_handoff/CONTEXT.md` — system map, environment specifics, gotchas.
   **The environment has sharp edges (broken-path history, free-tier limits) — read every line.**
5. `.tasks/next/grounding_handoff/VERIFICATION_PROTOCOL.md` — how you verify every task and
   run the final certification. This is your definition of done.
6. `.tasks/next/grounding_hardening_plan.md` — the plan itself.
7. The audit that motivated everything: `scratchpad copy is gone — findings are summarized in
   CONTEXT.md §6` (original trace `f9112db5-09eb-4ea8-a4ea-fd4419c8f796` is still in the DB —
   view it via the trace API).

## Rules of engagement

- **Default behavior is sacred.** Production runs Vertex AI (ADC). All your changes must be
  no-ops when their flags/keys are unset. The local `.env` has a marked "debug mode" block
  (free-tier `GEMINI_API_KEY` + cheap models) — that is your local runtime; never remove the
  Vertex path, never commit secrets.
- **The law_corpus ingestion pipeline (fetch/scrape/parse/embed) already exists.** You may add
  an output artifact step (article store build) and populate empty parsed fields
  (`paragraphs`, `cross_references`) inside the existing parser — you may NOT redesign ingestion.
- **Surgical changes** per the mindset doc: touch only what the plan requires; match existing
  style; every new feature gets tests.
- **Trace-verified E2E is part of every task's definition of done** — not just unit tests.
  A task is complete when: (a) unit tests pass, (b) full suite green (2 known pre-existing
  failures allowed, see CONTEXT §7), (c) the plan's "Verify" criterion is demonstrated in an
  actual `pipeline_traces` record and you have inspected that trace.
- **Instrument what you build.** Every new pipeline mechanism (article-store lookup,
  navigation tool call, full-code injection, retrieval-repair, faithfulness verdicts) MUST emit
  its own `record_step(...)` so the dashboard shows it. The trace suite is how this system is
  debugged forever — extend it as you go.
- **Free-tier rate limits are real** (~10-15 requests/min; one chat = 4-6 model calls +
  embeddings). Serialize E2E runs, sleep between them, treat 429 as expected and retry.
  Never conclude "broken" from a 429.
- **After structural changes, sync docs**: `.agents/context/backend.md` numbers and sections
  (see `.agents/workflows/09_doc_sync.md`).
- Georgian text everywhere is UTF-8 Mkhedruli; the answer language must remain 100% Georgian —
  certification checks this programmatically.

## Execution order

1. Bootstrap check (VERIFICATION_PROTOCOL §1) — prove the stack runs and traces record
   before touching anything.
2. Phase 0 (five audit fixes) — after EACH fix, re-run the golden question affected by it and
   inspect the trace.
3. Phase 1 (mechanisms A, B, C) → Phase 2 (generation contract) → Phase 3 (verification net) →
   Phase 4 (eval loop). Respect the dependency graph in the plan.
4. **Final certification audit** (VERIFICATION_PROTOCOL §4) — the full rubric over the golden
   question set, producing `.tasks/audits/certification_<date>.md` with attached trace exports.
5. Doc sync + final report: what shipped, what's proven (with trace IDs), what remains.

## Deliverables

- All plan tasks implemented with tests.
- New/updated trace steps for every new mechanism.
- `eval/golden_retrieval.yaml` (validated against the corpus, per protocol §3).
- Certification audit report in `.tasks/audits/` with per-question scorecards and trace IDs.
- Updated `.agents/context/backend.md`.
- Final summary distinguishing **proven** (trace-verified) from **implemented-but-unproven**,
  with zero unexplained gaps.
