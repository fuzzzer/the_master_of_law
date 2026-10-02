# Handoff — find the root causes of the Georgian QA findings and fix them fully

You are picking up a bug-fixing job on Fuzzzy Law. A Georgian end-to-end QA run
against production on 2026-10-01 found the problems listed in
`docs/qa/2026-10-01_georgian_qa_findings.md`. **Read that report first, in full** —
it has the symptoms, the exact evidence (log lines, payloads, article numbers) and,
where known, the file and line. This prompt tells you how to work and in what order.

## Before you write any code

1. Follow `CLAUDE.md`: read `.agents/context/mindset_and_principles.md`,
   `.agents/context/backend.md`, `.agents/debug_surgeon/context.md`,
   `.agents/workflows/02_bug_to_fix.md`; for the corpus items also
   `.agents/context/law_corpus.md` and `.agents/rag_specialist/context.md`;
   for the client items `frontend/.agents/orchestrator.md`.
2. Work on a new branch from `main` (not `chore/production-preparation`).
3. Get the test suite green locally first (`backend/scripts/test-db.sh up`, then
   `pytest tests/ -q`; frontend `fvm flutter test`) so you know your baseline.

## How to work — root causes, not symptom patches

For every finding:
1. **Reproduce** it (a failing test, or `scripts/qa/` against a local backend —
   `QA_BASE=http://localhost:8000`). The local Docker image is stale (2026-09-20);
   rebuild it from your branch, don't test against it as-is.
2. **Find the root cause and state it in one sentence** before fixing. Ask "why"
   until you reach a design decision, not just the line that crashed. Several
   findings share a cause — fix the cause once.
3. **Write a regression test that fails before the fix** and passes after.
4. Fix only what the finding needs; no drive-by refactors.
5. Record per finding: root cause, fix, test name, and how you verified it.

Do not hide failures to make numbers look good: an empty answer, a provider error
or an unverifiable citation must surface honestly, never as a soothing message
that pretends success.

## Order of work

**1. Quick, clear correctness bugs (small, independent):**
- Empty answer when the tool loop ends on a `function_call`
  (`backend/app/services/agent_pipeline_service.py`, tool loop). After the last
  allowed round the model must be made to answer in text (e.g. a final call with
  tools disabled), and an empty final answer must never be sent as `done` or saved
  as the assistant message.
- "Create case" tool saves the login uid into a UUID column
  (`backend/app/services/case_tool_executor.py`, `_handle_create_case`). Resolve
  the user the way `case_builder_service` does. Also make sure one failed write
  inside a turn cannot poison the session and kill the whole turn.
- Document generation returns HTTP 500 with Google's raw English error
  (`POST /case-files/{id}/generate-document`). Route provider errors through the
  same classification the WebSocket uses — ideally in one shared place so no
  REST route can leak a raw provider error again.
- Daily vs per-minute quota: `backend/app/utils/provider_errors.py` must read the
  `quotaId` and say "the daily free limit for this model is used up — choose
  another model or key" for per-day buckets, and "try again in N seconds" only for
  per-minute ones. Log the parsed `quotaId`/`quotaValue` explicitly (production log
  lines are truncated, so the raw body is useless there).

**2. Safety:**
- A deterministic emergency path that does **not** depend on any model call:
  messages signalling immediate danger (violence happening now, threats, suicide)
  get an immediate Georgian reply with 112 and the domestic-violence hotline
  116 006 — before the guardrail/RAG/model, and also as the fallback text when the
  model call fails for such a message. Verify the hotline numbers against an
  official Georgian source before shipping and cite where you checked. Keep the
  keyword list in one place, test it with realistic Georgian phrasings (including
  Latin-script Georgian), and make sure it does not fire on ordinary legal
  questions that merely mention violence in the past tense.

**3. Client timeout:**
- The server sends nothing during a long model call; the app kills the turn after
  60 s of silence. Fix it at the protocol level (e.g. a periodic progress/heartbeat
  frame from the server while a turn is running that the client's timer counts),
  keep the client and server in agreement, and test a model call that takes > 60 s.

**4. The big one — calls per question (needs a design decision from the owner):**
Measure first: count model calls and input tokens per turn from traces for a
labour, a rental and a case-chat question. Then answer, with evidence: why does the
model search 5 more times when 16–23 articles (or the whole code) are already in
the prompt? Does a tool-initiated `search_law` need its own Gemini query expansion
and rerank? Is full-code injection plus retrieval plus tool search all needed?
Propose 2–3 options with the call/token count each would produce and what quality
risk each carries; **bring them to the owner before implementing** — this changes
answer quality and must be evaluated with `eval/` before and after. The target is
that a free-tier key can answer a realistic number of questions per day.

**5. Legal accuracy:**
- Citation verification must check the **paragraph/sub-point**, not just that the
  article exists (cases: 47(1)(გ) vs 47(5)(გ); 48(4) vs 48(9)). A citation whose
  paragraph does not exist or does not say what the sentence claims must not get
  `verified: true`.
- Stop invented numbers: compensation ranges attributed to court cases, "success
  likelihood %", unsupported statements (court-fee exemption). Find where the
  prompts invite these (case builder sections, strategy fields) and either ground
  them in retrieved text or remove them.
- The 7-day/30-day deadline confusion and the missed art. 48(7) rule are good eval
  cases — add them to `eval/`.
- Language quality: foreign-script fragments, English headings, internal "case
  agent" wording, formal/informal switching. Find the prompt/model cause; add an
  automatic check that rejects foreign-script characters inside Georgian answers.

**6. Corpus — superscript article numbers:**
Superscript articles are flattened (52⁴ → `524`, 199¹ → `1991`) and collide with
real articles; `get_article(civil_code, 491)` returns art. 49¹. Fix it at the
source (the corpus build in `law_corpus/scripts/`, article ids, `article_norm`),
not with another tie-break. Then rebuild the article store and the affected
Chroma metadata, and update citation parsing, `get_article`, citation verification,
matsne anchors and the law browser display (show "მუხლი 199¹"). Check how matsne
itself anchors superscript articles before choosing a format. The corpus is
907 MB and not in git — plan the rebuild and the production data update explicitly
and get the owner's go-ahead before touching production data.

**7. Small items:** law search de-duplication per article; empty code-level
`source_url`; "Updating your case file" label on plain law lookups; model list
offering models a free key cannot use (`gemini-2.5-flash`, Pro models).

## Definition of done

- Every finding in the report is either fixed with a regression test, or explicitly
  deferred with the reason and the owner's agreement.
- `pytest tests/ -q` and `fvm flutter test` / `fvm flutter analyze` pass; numbers
  in `CLAUDE.md` and `.agents/context/backend.md` updated (`.agents/workflows/09_doc_sync.md`).
- `scripts/qa/` re-run against a local build of your branch: no empty answers, no
  internal errors in the case chat, the emergency message answers instantly without
  a model, provider errors are Georgian and correct about daily vs per-minute.
- `eval/` run before and after the accuracy and calls-per-question changes, with
  the comparison in your report.
- Update `docs/qa/2026-10-01_georgian_qa_findings.md`: mark each finding fixed /
  deferred with the commit that fixed it.
- Do not deploy to production yourself; hand the owner a short plain-language
  summary (no internal codes — see `CLAUDE.md` "Talking to the owner") of what
  changed, what was verified, and what still needs their decision.
