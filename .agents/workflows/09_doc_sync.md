# 📋 Workflow: Documentation Sync

> **When to use:** After ANY task that changes codebase structure.
> This workflow ensures context files stay accurate.

---

## When This Workflow Triggers

Run this workflow after you:
- Add/remove/rename endpoints, services, repositories, models, or schemas
- Add/remove Flutter feature modules
- Change architecture patterns (new middleware, new integrations)
- Add/remove test files
- Change production deployment configuration
- Modify the RAG pipeline stages

---

## Step 1: Scan Current State

Run these commands to get accurate numbers:

```bash
# Backend stats
echo "=== Endpoints ===" && grep -r "@router\." backend/app/routes/ --include="*.py" | wc -l
echo "=== Router files ===" && find backend/app/routes -name "*.py" ! -name "__init__.py" | wc -l
echo "=== Services ===" && find backend/app/services -name "*.py" ! -name "__init__.py" | wc -l
echo "=== Repositories ===" && find backend/app/repositories -name "*.py" ! -name "__init__.py" | wc -l
echo "=== Models ===" && find backend/app/models -name "*.py" ! -name "__init__.py" | wc -l
echo "=== Schemas ===" && find backend/app/schemas -name "*.py" ! -name "__init__.py" | wc -l
echo "=== Test files ===" && find backend/tests -name "test_*.py" -o -name "*_test.py" | wc -l
echo "=== Test functions ===" && find backend/tests -name "test_*.py" -o -name "*_test.py" | xargs grep -c "def test_" | awk -F: '{sum+=$2} END {print sum}'
echo "=== Python files ===" && find backend/app -name "*.py" | wc -l
echo "=== Lines of code ===" && find backend/app -name "*.py" | xargs wc -l | tail -1

# Frontend stats
echo "=== Flutter features ===" && find frontend/lib/src/features -maxdepth 1 -type d | tail -n +2
```

## Step 2: Compare With Documented State

Check these files for stale numbers:
1. `GEMINI.md` — Architecture section
2. `CLAUDE.md` — Architecture section
3. `.agents/context/project_status.md` — Completed sections
4. `.agents/context/backend.md` — Codebase Stats table + endpoint table

## Step 3: Update Stale Files

For each file where numbers don't match:
1. Update the count/stat to match reality
2. Update the "Last verified" date to today
3. If endpoints were added/removed, update the endpoint table in `backend.md`
4. If new services/features were added, add them to the relevant list

## Step 4: Verify Consistency

After updates, verify that these values are consistent across ALL context files:
- Endpoint count
- Service count
- Test count
- ChromaDB chunk count
- Flutter feature list

---

## Quick Reference: Which File Documents What

| Data | Documented in |
|------|--------------|
| Endpoint count + table | `backend.md` + `GEMINI.md` (count only) |
| Service list | `backend.md` |
| Test count | `backend.md` + `project_status.md` |
| ChromaDB stats | `project_status.md` + `law_corpus.md` |
| Flutter features | `project_status.md` + `GEMINI.md` |
| Production state | `production.md` + `project_status.md` |
| Architecture diagram | `GEMINI.md` |
| Current step/phase | `GEMINI.md` + `project_status.md` |
