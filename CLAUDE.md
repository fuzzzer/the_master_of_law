# კანონის ოსტატი — The Master of Law

> AI-powered legal advocate for Georgian citizens. Case-centric architecture.

## Mindset

**Empower people with easily accessible law.** Make it fit real cases. Really help people.

The law exists to protect everyone — but in practice, it's buried in dense codes, scattered across court rulings, and written in language that shuts ordinary people out. This app exists to change that. We put the full weight of Georgian law — statutes, Supreme Court practice, Grand Chamber decisions — into the hands of the people who need it most, when they need it most.

This is not a legal search engine. This is a legal advocate. Every feature we build must pass one test: **does this help a real person win a real case?** If it doesn't, we don't build it.

## Principles

### 1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First
Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
- Is name understandable for someone who knows noting about the code? If no, refine it, make it more descriptive.
- Need to add comments? Then it means code is not descriptive enough, refine naming, describe process with methods, talk with code clearly.

### 3. Surgical Changes
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

### 4. Goal-Driven Execution
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

## Status: Step 3 — Design System & Flutter App 🔄

| Component | Status | Key File |
|-----------|--------|----------|
| Law Corpus (9,450 chunks) | ✅ Done | `law_corpus/data/chroma/` |
| Backend (25 endpoints) | ✅ Done | `.agents/context/backend.md` |
| Design System | 🔄 In Progress | `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` |
| Flutter App | 🔄 In Progress | `frontend/` (package: `master_of_law`) |

## Context Loading — Read by Task

### Always read first:
- `.agents/context/project_status.md` — Current state, what's done, what's next

### By task:
| Task | Load These |
|------|-----------|
| **Backend work** | `.agents/context/backend.md` |
| **Flutter / UI** | `frontend/.agents/orchestrator.md` → `frontend/.agents/general_guide/flutter_architecture.md` |
| **Design system** | `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` |
| **Feature planning** | `master_plan/04_feature_roadmap.md` |
| **Production deploy** | `.agents/context/production.md` |
| **Law corpus** | `.agents/context/law_corpus.md` |
| **Original specs** | `master_plan/01_...`, `02_...`, `03_...` |

## Architecture (compact)

```
Flutter App (master_of_law, ge.fuzzycore.masteroflaw)
  │ 5 tabs: Chat │ Cases ⭐ │ Laws │ Notes │ Profile
  │ HTTPS / WebSocket
  ▼
FastAPI Backend (25 endpoints, 10 services)
  │ Firebase Auth → Credit Gate → Rate Limit
  │ 5-stage RAG: Expand → Vector → FullText → Merge → Rerank
  │ Gemini 3.1 Pro legal analysis
  ▼
Data: PostgreSQL + ChromaDB (9,450 law chunks) + Redis
```

## Core Decision: Cases = Projects

Every feature serves one purpose: building the strongest legal case.
Users dump raw info → AI organizes it.
Everything links to everything (facts ↔ arguments ↔ laws ↔ evidence ↔ conversations).
