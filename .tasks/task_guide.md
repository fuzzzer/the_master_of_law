# Task Structure Guide

> How advancement tasks are organized in `.tasks/advancements/`.

---

## Directory Structure

Each task lives in its own numbered directory:

```
.tasks/
├── advancements/
│   ├── 01_law_chat_and_retrieval/
│   ├── 02_dynamic_questionnaire/
│   ├── ...
│   └── 07_ai_agent_case_tools/
│       ├── current_progress.md    ← Track what's done
│       ├── description.md         ← What & why & how
│       ├── specs.md               ← Technical constraints & specs
│       └── user_notes.md          ← Manual feedback & overrides
└── task_guide.md                  ← This file
```

---

## File Purposes

### `current_progress.md`
**What's done, what's next.**

- Organized by milestones with checkboxes
- Each milestone ends with a "Milestone complete ✅" gate
- Last updated timestamp at the top
- Blockers section at the bottom
- Agents update this as they work

### `description.md`
**What this task is and step-by-step guide to implement it.**

- Purpose: why this task exists (1-2 paragraphs)
- Dependencies: which prior tasks must be done
- Multi-step guide: numbered milestones with concrete steps
- Each step ends with a "Verify" instruction

### `specs.md`
**Technical constraints, schemas, configs, and acceptance criteria.**

- Behavioral specs: tables of what/how
- Technical constraints: code snippets, API schemas, config examples
- Go/no-go criteria: checklists that must pass before task is "done"
- Environment/infrastructure details

### `user_notes.md`
**Human feedback that overrides everything else.**

- Design feedback from user
- Priority adjustments
- Edge cases discovered during review
- Agents read this FIRST before starting work

---

## Naming Convention

```
{NN}_{snake_case_short_name}/
```

- `NN` = sequential number (01, 02, ... 07)
- Name = 2-4 words describing the feature
- Examples: `01_law_chat_and_retrieval`, `07_ai_agent_case_tools`

---

## Rules

1. **Agents read `user_notes.md` first** — it contains overrides
2. **Check `current_progress.md` before starting** — don't redo completed work
3. **Update progress as you go** — check boxes, add timestamps
4. **One milestone at a time** — verify before moving to next
5. **Blockers go in progress file** — not in chat, not in code comments
