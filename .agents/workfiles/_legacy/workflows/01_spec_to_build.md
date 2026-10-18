# 📋 Workflow: Spec → Build

> **Use when:** Building a new feature from scratch.
> **Philosophy:** Define what "done" looks like BEFORE writing a single line of code.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for context and quality standards.
Read `AI_GUIDE.md` for backend architecture.
Read `.user_notes/priorities.md` for current focus.

## Feature Spec

**Feature:** [DESCRIBE THE FEATURE IN 1-2 SENTENCES]

**User Story:** As a [USER TYPE], I want to [ACTION] so that [BENEFIT].

**Success Criteria:**
1. [SPECIFIC, TESTABLE CRITERION]
2. [SPECIFIC, TESTABLE CRITERION]
3. [SPECIFIC, TESTABLE CRITERION]

**Constraints:**
- Must follow existing patterns in AI_GUIDE.md
- Must have type hints and docstrings on all public functions
- Must include at least one test per new function
- Error messages in Georgian AND English

## Execute This Workflow:

### Phase 1 — Analyze (STOP after this, show me the plan)
1. List EVERY file that will be created or modified
2. Identify which layer each change belongs to (Route / Service / Repository / Model / Schema)
3. List any new dependencies or environment variables needed
4. Identify potential risks or edge cases
5. Estimate credit cost if applicable

### Phase 2 — Build (only after I approve the plan)
6. Create/modify files in dependency order: Model → Schema → Repository → Service → Route
7. Follow the singleton pattern for services
8. Follow the DI pattern for repositories (inject `db: AsyncSession`)
9. Register any new router in `main.py`

### Phase 3 — Verify
10. Run existing tests: `cd backend && .venv/bin/python -m pytest tests/ -q`
11. Write new tests for the feature
12. Provide a curl command to manually test
13. Update AI_GUIDE.md endpoint table if new endpoint added

### Phase 4 — Document
14. Update `.user_notes/session_log.md` with what was done
```

---

## Why This Works

The key insight from **Spec-Driven Development**: AI agents perform 3-5x better when given concrete success criteria vs. vague descriptions. The "STOP after Phase 1" pattern prevents the agent from building the wrong thing at full speed.
