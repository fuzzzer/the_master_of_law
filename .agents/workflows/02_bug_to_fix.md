# 🐛 Workflow: Bug → Fix

> **Use when:** Something is broken, unexpected behavior, or tests are failing.
> **Philosophy:** Hypothesize, don't guess. Isolate, don't shotgun.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for context.
Read `.agents/debug_surgeon/context.md` for debugging protocol.

## Bug Report

**Symptom:** [WHAT HAPPENS — be exact]

**Expected:** [WHAT SHOULD HAPPEN]

**Error / Stack Trace:**
[PASTE FULL ERROR — never summarize]

**Steps to Reproduce:**
1. [EXACT COMMAND OR ACTION]
2. [EXACT COMMAND OR ACTION]

**What I Already Tried:**
- [ATTEMPT 1 AND ITS RESULT]
- [ATTEMPT 2 AND ITS RESULT]

## Execute This Workflow:

### Phase 1 — Reproduce & Isolate
1. Confirm you can reproduce the exact error from my description
2. Narrow down which layer the bug is in:
   Request → Middleware → Route → Service → Repository → Integration → Config
3. State your top 3 hypotheses, ranked by likelihood

### Phase 2 — Root Cause (STOP — show me before fixing)
4. For hypothesis #1, describe the exact mechanism of failure
5. Show me the specific line(s) of code responsible
6. Explain WHY this bug exists (not just what)

### Phase 3 — Fix (only after I approve the diagnosis)
7. Write a failing test that reproduces the bug
8. Apply the minimal fix (change as few lines as possible)
9. Verify the test now passes
10. Run full test suite to check for regressions

### Phase 4 — Prevent
11. Could this class of bug happen elsewhere? Check.
12. Should we add a guard/assertion to prevent recurrence?
13. Document the fix in `.user_notes/observations.md`
```

---

## The Five Whys Example

```
Problem: Chat endpoint returns 500
  Why? → LegalAnalysisService raised an exception
  Why? → Gemini API returned a 403
  Why? → SA key was not mounted in Docker
  Why? → GCP_SA_KEY_PATH was empty in .env
  Why? → We added ADC auth but forgot to set the new env var

Root cause: Missing environment variable after auth migration
Fix: Add GCP_SA_KEY_PATH to .env + validation in settings.py
Prevention: Add startup check that verifies all required env vars
```
