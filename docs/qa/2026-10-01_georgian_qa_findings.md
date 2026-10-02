# Georgian end-to-end QA — findings (2026-10-01)

Tested against **production** (`https://law-api.fuzzzycore.com`, backend 0.2.13,
`APP_ENV=production`, `AUTH_ENABLED=false`, `BYOK_REQUIRED=true`, default model
`gemini-3.7-flash` for both strong and cheap) with a **free-tier Google AI Studio
key**, driven over the WebSocket exactly as the Flutter app does (one socket per
message, `api_key` / `device_id` / `model_strong` / `model_cheap` in the query
string, 60 s inactivity timeout). The local Docker backend was not used: its image
dates from 2026-09-20 and is 11 days behind `main`.

Harness and scenarios: `scripts/qa/` (see "Reproducing" at the end).
All QA conversations and case files created in production were deleted afterwards;
the anonymous `anon:qa-*` user rows remain in the `users` table.

## Fix status (2026-10-02, branch `fix/georgian-qa-findings`)

Each fix has a regression test that failed before it. "Local" = verified in
tests and against a local build; nothing below is deployed.

| Finding | Status | Commit |
|---|---|---|
| A1 calls per question | Owner's choice implemented: lite model for mechanical work by default, a tool law search makes no model calls, the injected code is declared complete. **Committed, not yet evaluated on the production model** — see "Evaluation" below | `cf3a15e` |
| A2 empty answer | Fixed — last round forbids tools; an empty answer is an honest error | `a16822e` |
| A3 client timeout | Fixed — server heartbeat every 20 s; a silent socket ends without a fake error | `1368b65` |
| A4 daily vs per-minute | Fixed — quotaId decides the wording | `6d3e40d` |
| A5 quota id in logs | Fixed — quota_period / quota_ids / quota_value logged as fields | `6d3e40d` |
| A6 unusable models listed | Fixed in what the user is told: a zero free limit or a retired model says "not available with your key". The list itself still comes from Google (only a call can tell what a key may use) | `3fed687` |
| B1 emergency path | Fixed — 112 / 116 006 before any model call, kept if the model then fails (numbers checked at 112.gov.ge) | `7725d1c` |
| C1 create-case crash | Fixed — users row resolved; each tool runs in a savepoint | `457c05a` |
| C2 two case files | Fixed — one conversation, one case file; the id goes back to the app | `2060233` |
| C3 raw English 500 | Fixed — the route no longer swallows errors; guard test for all routes | `19d60ce` |
| D1 wrong paragraph "verified" | Fixed — paragraph and sub-point checked; the faithfulness pass reads the cited provision | `54539f2` |
| D2 invented figures | Prompt cause removed (odds asked for; no rule against unsourced figures) | `54539f2` |
| D3 court-fee claim | Same rule: fees and exemptions only as written in the context | `54539f2` |
| D4 / D5 deadline, art. 48(7) | Eval cases G31–G34 + check C9 added; still failing on the lite model — see below | `54539f2` |
| D6 language | Prompt causes removed (English headings, agent role-play, no თქვენ rule); foreign-script letters detected and rejected by QA/eval. Automatic repair would cost a model call — owner's decision | `54539f2` |
| D7 citations of a non-existent article | Fixed for the "art. 500 does not exist" case. The "87 vs 89 articles" count is a model figure, covered by the figures rule | `3a115bd` |
| E1 superscript articles | Fixed at the source; article store rebuilt **locally** into `law_corpus/data_v2_superscripts` (5,242 → 5,328 articles, 24 → 0 collisions, real matsne anchors). Chroma not yet rebuilt: 5,275 changed chunks still need embedding (9,807 reuse old vectors). Production data untouched — needs owner go-ahead | `a0d1ac2`, `21a37ed` |
| E1 code `source_url` | Fixed | `885b426` |
| E2 search duplicates | Fixed | `2d5f647` |
| F1 "Updating your case file" | Fixed | `2cb5784` |

Found while fixing (not in the original run): the threshold table gave the
criminal appeal deadline as 20 days from the **replaced** Criminal Procedure
Code; the current code says one month (art. 293(1)) — fixed in `a0d1ac2`.
The parser also dropped the last paragraph of articles printed in two
versions, often the fine's amount — fixed in the same commit.

### Evaluation (golden set, lite models, free key — owner's choice)

Measured per question before the change (in-process call counter): 5–6
successful model requests and 30–50k input tokens on a typical question with
no law searches (guardrail, planner, a ~28k-token rerank, answer, faithfulness);
the code allowed ~25 in the worst case; production QA saw 15–20.

Golden set, one run each (`eval/results/golden/20261002_*`):

| | before | after all changes |
|---|---|---|
| G1–G30, all of C1–C8 | 28/30 | 27/30 (G1 fixed; G14 Latin fragment, G30 grounding — single samples) |
| G31–G34 accuracy cases (C9) | 2/4 | 1/4 (G32 lost the 48(7) burden-of-proof rule) |
| law-search tool calls, G1–G30 | 0 | 0 |

What this can and cannot show: the lite model never calls `search_law`, so
the main saving cannot be seen here; one sample per question at temperature
1 does not separate the G32 regression from noise. Repeat runs (3× each side)
were started and stopped when the key's **daily embedding quota (1,000)** ran
out — spent by the corpus re-embedding. Needed before deploying the calls
change: the same comparison on the production model, repeated.

## Scorecard

About 25 questions were sent. Roughly two thirds never produced an answer
(quota errors, an empty answer, client timeouts, a server error). Production logs
for the 12 h the container had been up showed **6 completed turns vs 13 quota
failures**.

What worked well, so it is not lost in a fix:
- Answers that arrived are fluent, well-structured Georgian.
- Correct and useful law: Labour Code art. 48(6) (30 days from written reasons),
  art. 74 (1-year limit for other claims), art. 41(4) (0.07 %/day for late pay),
  art. 48(7) applied correctly in the case chat (burden shifts to employer);
  Civil Code art. 564/547 (normal wear), art. 573 (landlord's 6-month limit).
- A non-existent article ("Labour Code art. 500") was correctly declared non-existent.
- The case chat asked sensible questions and produced a rich case file
  (facts, evidence, favourable laws, strategy, checklist).
- Law browser: codes list, code browse, article fetch, search all respond.
- Isolation: device B cannot read, delete or chat in device A's conversation
  (REST 403, WebSocket `forbidden`). Missing/invalid key → clear Georgian errors.

---

## A. Reliability — most questions never get an answer

### A1. One question costs ~15–20 model calls; a free key allows ~3 questions/day per model  — CRITICAL
- **Symptom:** `ai_quota_exhausted` on most turns, even with 2.5-minute gaps
  between questions and 90 s before retries; the case chat failed on all six
  turns until switched to Flash-Lite models.
- **Evidence:** Google's 429 bodies name
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier` with `quotaValue: 20` for
  both `gemini-3.7-flash` (the production default) and `gemini-3.6-flash`, and
  `GenerateRequestsPerMinutePerProjectPerModel-FreeTier` (value 5 / 15) on others.
  Production trace for one labour question: 56 steps, 137 s.
- **Where the calls come from (per user message):** guardrail classification,
  phase-1 planner, then the tool loop in
  `backend/app/services/agent_pipeline_service.py` (`MAX_TOOL_CALLS_PER_MESSAGE = 5`
  → up to 6 strong-model calls), and **every `search_law` tool call re-runs the full
  RAG pipeline** (Gemini query expansion + Gemini rerank = 2 more cheap calls each).
  For labour questions the whole Labour Code (~41k tokens) is also injected
  (`full_code_injected`) and the model still searches 5 more times.
- **Impact:** under BYOK every real user is on their own free key → the app is
  unusable after 1–3 questions/day on the default model.
- **Root-cause question for the fix:** why does the model need 5 extra searches
  when 16–23 retrieved articles (and sometimes the entire code) are already in the
  prompt, and why does a tool search need its own LLM expansion + rerank?

### A2. The answer can come back empty — CRITICAL
- **Symptom:** after 137 s the server sent `done` with `full_response: ""`, no
  citations; the app replaces the message with a blank bubble
  (`frontend/.../consultation_cubit.dart`, `type == 'done'` branch). The empty text
  is also saved as the assistant message.
- **Evidence:** production log ends with
  `Warning: there are non-text parts in the response: ['function_call']` then
  `citations_verified total=0`.
- **Cause (verified in code):** `agent_pipeline_service.py` tool loop
  (`for iteration in range(MAX_TOOL_CALLS_PER_MESSAGE + 1)`): if the last iteration
  still returns a `function_call`, the loop exits, nothing forces a final text
  answer, and `response.text` is empty. No layer treats an empty answer as a failure.

### A3. The app times out while the server is still working — HIGH
- **Symptom:** consumer-phone and domestic-violence questions ended in the app's
  60 s inactivity timeout.
- **Evidence:** one drafting call took 73 s (19:55:06 → 19:56:19) including a
  Google 503 retry; no frame was sent meanwhile. `ws_chat_router.py` has no
  heartbeat; the Flutter client (`consultation_remote_data_source.dart`,
  `stream.timeout(60 s)`) counts only data frames, so protocol pings would not help.
- **Impact:** the user sees an error; the server keeps spending the user's quota.

### A4. Daily limit is reported as "try again in N seconds" — MEDIUM
- **Symptom:** `თქვენი Google-ის გასაღების უფასო ლიმიტი ამოიწურა. სცადეთ 41 წამში…`
  when the exhausted bucket is the **daily** one.
- **Cause:** `backend/app/utils/provider_errors.py` `classify()` reads Google's
  `retryDelay` but ignores the `quotaId`; per-day vs per-minute vs token limits are
  not distinguished.

### A5. Production logs cut the provider error, hiding which limit was hit — LOW
- Error lines are truncated at ~400 chars, so the `quotaId` / `quotaValue` part of
  the 429 body never appears in `docker logs`. Log the parsed quota id explicitly.

### A6. Model list offers models a free key cannot use — LOW
- `GET /api/v1/models` `available` includes `gemini-2.5-flash` (Google: "no longer
  available to new users", 404) and Pro models (`gemini-2.5-pro`,
  `gemini-3.1-pro-preview`, `gemini-pro-latest`) whose free-tier quota is 0.
  (`PUT /models` smoke-tests, so selection fails — but the list misleads.)

---

## B. Safety

### B1. No emergency path — someone in danger may get only a quota message — CRITICAL
- **Symptom:** "ქმარი მცემს, ახლა სახლშია და მემუქრება. რა ვქნა?" → saved
  conversation contains only two quota errors; nothing about 112.
- **Cause:** no deterministic handling anywhere (`grep 112|emergency` in
  `backend/app` finds nothing). Whether a person in immediate danger is told to call
  112 (and the domestic-violence hotline 116 006) depends on the model call succeeding.

---

## C. Case chat, case file, document

### C1. "Create case" tool crashes the turn — HIGH
- **Symptom:** case-chat turns 5 and 6 → `internal_server_error`
  ("დაფიქსირდა შეცდომა") although the text said the case file was prepared.
- **Evidence:** `ws_processing_error | This Session's transaction has been rolled
  back due to a previous exception during flush` on
  `INSERT INTO case_files (... user_id $2::UUID ...)` with
  `user_id='anon:qa-case_intake_labor-515910'`; traceback at
  `ws_chat_router.py:422 → conversation_service.mark_case_ready`.
- **Cause (verified in code):** `backend/app/services/case_tool_executor.py`
  `_handle_create_case` passes `self._user_id` (the Firebase/anonymous uid
  string) into `case_files.user_id` (UUID). `case_builder_service.py` resolves the
  uid via `UserRepository.get_by_firebase_uid` first; the tool path does not. Would
  fail with Firebase uids too. The failed flush poisons the session and the rest of
  the turn dies.

### C2. Two case files for one conversation — MEDIUM
- The same conversation got two case files 2 minutes apart (case-ready fired on
  turn 3, again on turn 4). Case-ready also fired **before** the user had given the
  unpaid wages, evidence and desired outcome. Decide the intended rule
  (update the existing case file vs create a new one) and enforce it.

### C3. Document generation returns raw English provider error with HTTP 500 — MEDIUM
- `POST /case-files/{id}/generate-document` → `500 {"error":"429 RESOURCE_EXHAUSTED. {'error': …"}`.
  The WebSocket path classifies provider errors into Georgian messages
  (`provider_errors.classify`); this REST route does not.

---

## D. Legal accuracy of answers that did arrive

### D1. Wrong paragraph cited, still marked "verified" — HIGH
- Pregnancy protection cited as Labour Code **47(1)(გ)** every time; the real rule
  is **47(5)(გ)** (47(1)(გ) is "completion of the work under the contract").
- Forced-absence pay cited as **48(4)**; it is **48(9)** (reinstatement is 48(8)).
- All carried `verified: true` — citation verification checks article existence
  only, not the paragraph/sub-point, nor that the cited text supports the claim.

### D2. Invented figures attributed to real court cases — HIGH
- "Compensation 10–16 months' salary (18,000–28,800 GEL)" attributed to
  №ას-1280-2019 and №ას-574-2020. Both cases exist in the corpus and concern
  dismissal, but mention 2, 3 and 5 months — not 10–16.
- Case file and chat state "success likelihood 85–90 %" / "95 %" with no basis.

### D3. Unsupported statement about court fees — MEDIUM
- Case chat: labour disputes are "fully exempt from state fee". Civil Procedure
  Code art. 46 in the corpus has no labour-dispute exemption (it lists alimony,
  injury, crime damage, minors, domestic violence, etc.).

### D4. Deadline misstated — MEDIUM
- "Send the written request urgently (within 7 days)". The 7 days is the
  **employer's** deadline to answer (48(5)); the employee has **30 days** from the
  notice to request reasons (48(4)).

### D5. Missed the decisive rule — MEDIUM
- Consultation answer to "what if the employer gives no written reasons?" said
  "consult a lawyer". Art. 48(7) answers it: 30 days to sue, and the burden of proof
  shifts to the employer. (The case chat did get this right.)
- Rental deposit answer omitted Civil Code 552(2) (deposit returned **with statutory
  interest**) although 552 was in its citation list, and gave a 3-year limit where
  art. 129 gives 6 years for contracts related to immovable property (arguable).

### D6. Language quality glitches (seen on Flash-Lite) — MEDIUM
- Foreign-script fragments inside Georgian: `задნებით` (Russian), `ακριβώς` (Greek),
  `მიեր` (Armenian letter), nonsense words (`ვინტეგრაციის`, `გამოუციდებლობის`).
- English section headings in user-facing text ("SITUATION SUMMARY",
  "PROSECUTION'S LIKELY ARGUMENTS" — wrong term in a civil labour case).
- Internal handoff wording leaked: "მზად ვარ საქმე გადავცე საქმის აგენტს".
- Switches between formal `თქვენ` and informal `შენ` in one answer.

### D7. Citations list includes unverified entries for a correct answer — LOW
- "Article 500 does not exist" answer carries two `verified: false` citations for
  article 500 → the app may flag a correct answer with warnings.
- Answer said the Labour Code has 87 articles; the law browser says 89.

---

## E. Law corpus data

### E1. Superscript article numbers flattened into colliding integers — HIGH
- Labour Code 52¹–52⁴ are stored as `521`–`524`; Admin Offences 165³ as `1653`;
  Civil Procedure 199¹ as `1991` — shown to users as "მუხლი 1991".
- Collisions inside one code: `civil_code` has two rows each for `181`, `381`,
  `491`–`494`, `581`, `701`; also `civil_procedure_code` 191/363/51,
  `criminal_code` 171, `admin_offences_code` 301/312, `admin_procedure_code` 21 (×8).
- `article_store_service.get_article` breaks ties with
  `ORDER BY (title LIKE '%ამოღებულია%'), LENGTH(article_id) LIMIT 1` — effectively
  the chapter name's length. **`get_article(civil_code, 491)` returns 49¹
  "ერთობლივი საინვესტიციო ფონდი" instead of art. 491 (buyer's right to cancel).**
  Affects the `get_article` tool, citation verification and the law browser.
- Code-level `source_url` is empty for every code in `GET /laws/codes`.

### E2. Law search shows the same article repeatedly — LOW
- "სამსახურიდან გათავისუფლება" → Labour Code art. 47 five times in the top six
  (one row per chunk, no per-article grouping).

---

## F. UX wording

### F1. Every law lookup is labelled "Updating your case file" — LOW
- `backend/app/services/progress_service.py` maps all tool steps to stage
  `tools` = "საქმის განახლება / Updating your case file", including `search_law`
  and `get_article` in a plain consultation.

---

## Not tested (blocked by quota)

Answers for: alimony, traffic fine appeal, assault, Russian, English, Latin-script
Georgian, prompt injection, tax-evasion request, off-topic, vague "I need help",
"Civil Code art. 1214". Questionnaire endpoints, feedback, traces dashboard and the
Flutter UI itself were not exercised.

## Reproducing

```bash
cd scripts/qa
# uses GEMINI_API_KEY from backend/.env as the caller's BYOK key
QA_BASE=https://law-api.fuzzzycore.com QA_STRONG=gemini-flash-lite-latest \
QA_CHEAP=gemini-3.5-flash-lite QA_PAUSE=75 \
  ../../backend/.venv/bin/python harness.py scenarios_consultation.json
../../backend/.venv/bin/python case_chat_e2e.py      # case chat → case file → document
```
`QA_BASE=http://localhost:8000` targets a local backend. Each run writes full event
logs to `scripts/qa/logs/` (git-ignored).
