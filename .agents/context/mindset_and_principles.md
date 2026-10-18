# Mindset & Principles

> Read this file before starting any task. This is non-negotiable.

## Mission

**Empower people with easily accessible law.** Make it fit real cases. Really help people.

The law exists to protect everyone — but in practice, it's buried in dense codes, scattered across court rulings, and written in language that shuts ordinary people out. This app exists to change that. We put the full weight of Georgian law — statutes, Supreme Court practice, Grand Chamber decisions — into the hands of the people who need it most, when they need it most.

This is not a legal search engine. This is a legal advocate. Every feature we build must pass one test: **does this help a real person win a real case?** If it doesn't, we don't build it.

---

## Principle 1: Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- **ALWAYS** start tasks ONLY after a full reading of the relevant context files listed in `GEMINI.md`.

## Principle 2: Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
- Is the name understandable for someone who knows nothing about the code? If no, refine it.
- Need to add comments? Then the code is not descriptive enough — refine naming, describe process with methods, talk with code clearly. Remove unnecessary comments.

## Principle 3: Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.
- The test: every changed line should trace directly to the user's request.

## Principle 4: Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Code Quality Standards

### Naming Conventions

| Thing | Pattern | Example |
|-------|---------|---------| 
| Files | `snake_case.py` | `credit_repository.py` |
| Classes | `PascalCase` | `CreditRepository` |
| Functions | `snake_case` | `get_balance` |
| Constants | `SCREAMING_SNAKE` | `FREE_TIER_DAILY_CREDITS` |
| Routes | `/api/v1/resource` | `/api/v1/conversations` |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_URL` |

### Python (Backend)
- Every public function has type hints and a docstring
- Every new feature has at least one test
- Every error path returns a meaningful message
- No hardcoded strings in services — use constants or prompts directory
- Logs use structured format: `logger.info("event_name", key="value")`
- Use `get_logger(__name__)` — follow existing logging patterns exactly

### Flutter (Frontend)
- Repositories NEVER throw exceptions — they return Sealed Classes (Success | Failure)
- Cubits NEVER use try/catch — they use exhaustive switch on sealed response
- State MUST be immutable — use copyWith
- NEVER use `Color()`, `Colors.`, `TextStyle()` directly — use theme extensions
- After creating new `.dart` files, run `./exp.sh` to update barrel files

---

## Remember

> *"The purpose of abstraction is not to be vague, but to create a new semantic level in which one can be absolutely precise."* — Dijkstra

You are not here to write code fast. You are here to write code **right**. Real people's legal outcomes depend on the quality of this code.

**Build it like your freedom depends on it — because for the users, it does.**
