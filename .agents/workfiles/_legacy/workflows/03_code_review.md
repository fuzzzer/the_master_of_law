# 🔍 Workflow: Code Review

> **Use when:** Auditing code quality before merge, after a big feature, or periodic health check.
> **Philosophy:** Review like a Staff Engineer who cares about the codebase 2 years from now.

---

## Copy-Paste Prompt

```
Read `.agents/init_prompt.md` for quality standards.
Read `.agents/code_architect/context.md` for architecture patterns.
Read `AI_GUIDE.md` for the project architecture.

## Code Review Request

**Files to review:** [LIST FILES, OR "all files changed since last commit"]

**Focus areas:** [OPTIONAL — e.g., "security", "performance", "architecture"]

## Execute This Workflow:

Review each file against these criteria, in this order:

### 1. Architecture Compliance
- [ ] Does it follow Route → Service → Repository → Model layering?
- [ ] Are there any layer violations (e.g., SQLAlchemy in a route)?
- [ ] Is the dependency direction correct (inward only)?
- [ ] Does it use existing patterns (singleton services, DI repos)?

### 2. Code Quality
- [ ] Type hints on all public functions?
- [ ] Docstrings on all public functions?
- [ ] Named constants instead of magic numbers?
- [ ] Error handling for every failure path?
- [ ] Structured logging (`logger.info("event", key="val")`)?
- [ ] No dead code or commented-out blocks?

### 3. Security
- [ ] No hardcoded credentials or API keys?
- [ ] Input validation on all user-supplied data?
- [ ] Auth middleware applied to protected routes?
- [ ] SQL injection safe (parameterized queries via ORM)?
- [ ] CORS configured correctly?

### 4. Performance
- [ ] No N+1 query patterns?
- [ ] Appropriate use of async/await?
- [ ] Reasonable timeout on external calls (Gemini, ChromaDB)?
- [ ] Caching where appropriate?

### 5. Maintainability
- [ ] Would a new developer understand this code in 10 minutes?
- [ ] Are variable names self-documenting?
- [ ] Is there unnecessary abstraction?
- [ ] Are tests adequate for the complexity?

## Output Format

For each finding:
**[SEVERITY: Critical/High/Medium/Low]** — File: `path/to/file.py`, Line: N
**Issue:** What's wrong
**Why it matters:** Impact if not fixed
**Fix:** Concrete suggestion (with code if applicable)
```
