# 🔧 Workflow: Refactor

> **Use when:** Code works but has structural problems, tech debt, or pattern violations.
> **Philosophy:** Refactoring changes structure without changing behavior. Tests prove it.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for quality standards.
Read `.agents/code_architect/context.md` for target patterns.

## Refactor Request

**Target:** [FILE(S) TO REFACTOR]

**Smell:** [WHAT'S WRONG — e.g., "God service", "leaky abstraction", "duplicated logic"]

**Constraint:** Behavior must NOT change. All existing tests must pass.

## Execute This Workflow:

### Phase 1 — Assess (STOP — show me)
1. Read all target files completely
2. Run existing tests to get baseline: `pytest tests/ -q`
3. Identify all code smells with specific line numbers
4. Categorize: architecture violation / duplication / complexity / naming
5. Propose the refactoring plan (what moves where)
6. List every file that will change

### Phase 2 — Safety Net
7. If tests are insufficient for the refactored code, write them FIRST
8. Verify they pass on the CURRENT (pre-refactor) code
9. These tests are your safety net — they must catch if behavior changes

### Phase 3 — Refactor (one step at a time)
10. Apply ONE structural change
11. Run tests
12. If passing, apply next change
13. Repeat until complete

### Phase 4 — Verify
14. Run ALL tests: `pytest tests/ -q`
15. Compare route count before/after (should be identical)
16. Manual smoke test the affected endpoints
17. git diff — review every change for unintended behavior changes
```
