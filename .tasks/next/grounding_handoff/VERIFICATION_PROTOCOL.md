# VERIFICATION PROTOCOL — debugger usage & certification

How the executor verifies every task and certifies the final system. The transparency suite is
the instrument; this file is the method. Nothing counts as done without a trace you inspected.

---

## §1 Bootstrap check (run BEFORE any implementation)

```bash
cd backend
docker compose up -d                       # stack up
docker exec backend-api-1 alembic upgrade head
curl -s http://127.0.0.1:8000/api/v1/health/ready
# send a probe question:
CONV=$(curl -s -X POST http://127.0.0.1:8000/api/v1/conversations -H "Content-Type: application/json" -d '{}' | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
curl -s -X POST "http://127.0.0.1:8000/api/v1/chat/$CONV/send" -H "Content-Type: application/json" \
  -d '{"message": "რა ჯარიმა ეკისრება მძღოლს სიჩქარის გადაჭარბებისთვის 40 კმ/სთ-ით?"}' | head -c 300
```
Expected: HTTP 200, Georgian answer citing ადმინისტრაციულ სამართალდარღვევათა კოდექსი მუხლი 125.
Then confirm the trace recorded:
```bash
docker exec backend-postgres-1 psql -U mol_user -d master_of_law -c \
 "SELECT id, status, jsonb_array_length(steps), duration_ms FROM pipeline_traces ORDER BY created_at DESC LIMIT 1;"
```
Expected: status `completed`, ≥12 steps. If this fails, fix the environment before anything else
(see CONTEXT §4). **Record the baseline**: save this trace's markdown export — you will diff
post-implementation behavior against it.

## §2 Per-task verification loop (every plan task)

1. **Unit level**: new/changed tests pass; full suite = 472+new passed / 2 known failures
   (CONTEXT §5). Any third failure = your regression; stop and fix.
2. **Rebuild & migrate**: `docker-compose up --build -d api` (+ `alembic upgrade head` if you
   added a migration).
3. **E2E probe**: send the plan task's golden question (see §3), wait for 200
   (retry on 429 after 30s — free tier).
4. **Trace inspection** (the actual verification):
```bash
TID=$(docker exec backend-postgres-1 psql -U mol_user -d master_of_law -t -c \
 "SELECT id FROM pipeline_traces ORDER BY created_at DESC LIMIT 1;" | tr -d ' \n')
curl -s "http://127.0.0.1:8000/api/v1/traces/$TID" | python3 -c "
import json,sys
t=json.load(sys.stdin)
print(t['status'], t['duration_ms'],'ms')
for s in t['steps']: print(f\"{s['seq']:>2} {s['step']:<28} +{s['at_ms']}ms\")"
```
   Check the plan's "Verify" criterion **inside the step data** (fetch the full trace JSON and
   assert on it programmatically — don't eyeball long prompts). Examples:
   - 0.1: `rag_final_selection.data.chunks[*].collection` contains `georgian_laws` with the
     expected article for the golden Q.
   - 0.3: no `chunk_id` starting `threshold_criminal_` for the labor Q.
   - 1.2: a `tool_executed` step with `tool: get_article`.
   - 2.1: a `retrieval_repair` step present when the cited article was absent from context.
5. **Record evidence**: append `{task_id, trace_id, verdict}` to
   `.tasks/audits/evidence_log.md` as you go. Certification (§4) reuses these.

New mechanisms MUST add their own `record_step` calls first — if a mechanism doesn't appear in
the trace, it is unverifiable and therefore not done.

## §3 Golden question set (build then freeze)

Two questions are pre-validated by the planner (corpus + live matsne checked):

| id | Question (Georgian) | Must ground in | Must include |
|----|---------------------|----------------|--------------|
| G1 | დამსაქმებელმა სამსახურიდან გამათავისუფლა მას შემდეგ, რაც ვუთხარი რომ ორსულად ვარ. წერილობითი მიზეზი არ მოუწერია. რა უფლებები მაქვს, რა კომპენსაცია მეკუთვნის და სად უნდა ვიჩივლო? | შრომის კოდექსი მუხლი 47 + მუხლი 48 (`labour_code`), court_practice on compensation | 30-დღიანი სასამართლო ვადა; case numbers when practice used |
| G2 | რა ჯარიმა ეკისრება მძღოლს სიჩქარის გადაჭარბებისთვის 40 კმ/სთ-ით? | ადმინისტრაციულ სამართალდარღვევათა კოდექსი მუხლი 125 (threshold entry legitimate here) | concrete fine amounts from corpus |

Extend to ~30 pairs across the 9 legal domains (`legal_classifier_service`) for
`eval/golden_retrieval.yaml` (plan 4.2). **Validation rule**: never assert an expected article
from memory — confirm each via `GET /api/v1/laws/search?q=...` / the article store, and record
the matsne URL. An unvalidated golden pair is worse than none.

## §4 Final certification audit (the last thing you do)

For EVERY golden question (fresh conversation each, serialized, 429-tolerant):

**Automated checks (script them; attach outputs):**
| # | Check | Pass condition |
|---|-------|----------------|
| C1 | Language purity | zero Latin fragments outside URLs/markdown in `response_text` |
| C2 | Statute grounding | expected articles present in `rag_final_selection` chunks OR a `tool_executed:get_article` / `full_code_injected` step |
| C3 | Citation verification | `citation_verification.not_found == []` in final iteration; every response citation resolves to a corpus `article_url` |
| C4 | Link integrity | every matsne URL in the response byte-matches a corpus/store `article_url` (no invented links) |
| C5 | Case attribution | if court_practice chunks in context AND practice-based claims made → ≥1 case number in response, verified against metadata |
| C6 | Deadline coverage | if response advises legal action → contains a ვადა/deadline or explicit "ვადა გადაამოწმეთ" flag |
| C7 | Anchoring | (after plan 2.2) unanchored legal-claim rate < 5% |
| C8 | No pollution | no threshold entries from a mismatched domain in context |

**Manual/model checks (you read the Georgian; document reasoning):**
| # | Check |
|---|-------|
| M1 | Claim-by-claim grounding: every substantive legal statement traceable to a specific chunk/article in the trace (quote both) |
| M2 | Correctness & completeness vs the mission ("does this help a real person win a real case?") — right articles, right amounts, right venue, nothing critical omitted |
| M3 | Simplified-but-faithful: nuance simplifications (e.g. burden-of-proof shifts) don't mislead |

**Spot live-source check**: for ≥3 distinct cited articles across the set, WebFetch the matsne
URL and confirm the article exists and supports the claim (planner did this for G1/G2 —
replicate the method).

**Output**: `.tasks/audits/certification_<date>.md` — per-question scorecard (C1-C8, M1-M3),
trace IDs, session exports attached (`/api/v1/traces/conversation/{id}/export`), and a final
verdict per dimension. **Certification passes** when every automated check passes on every
golden question and manual checks find no misleading or ungrounded advice. Any failure →
root-cause it via the trace (the failing step is visible by construction), fix, re-run that
question, and document the fix in the report. Do not average failures away.

## §5 Regression guarantee going forward

- `eval/golden_retrieval.yaml` + its runner become CI (plan 4.2): C2 at minimum on every run.
- Nightly grounding metrics job (plan 4.1) computes C3/C5/C6 rates from all real traces —
  wire its output into the dashboard so drift is visible without anyone asking.
- Weekly auto-audit (plan 4.3) replays §4 over recent real sessions.
