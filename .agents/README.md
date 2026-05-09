# 🤖 Agent Skills Directory

> **Thematic context packages** that give AI agents domain-specific superpowers.
> Each folder is a "skill module" — a focused context package that transforms a general AI into a specialist.

---

## Philosophy

Inspired by Andrej Karpathy's approach to software (Software 3.0):

> *"The verb is no longer 'coding' — it's 'manifesting'. Describe intent, let agents execute."*

But intent without precision produces garbage. These skill files are **executable context** — when an AI reads them, it doesn't just gain knowledge, it gains **judgment**. The difference between a junior dev and a 10x engineer isn't what they know, it's **what they choose NOT to do** and **how they think about tradeoffs**.

### Core Insights from Research

1. **Context Engineering > Prompt Engineering** — The quality of AI output is 80% determined by the context, not the instruction
2. **Spec-Driven Development** — Define "done" before writing code. AI performs 3-5x better with concrete success criteria
3. **Verification-First** — Tests and linters are infrastructure, not polish. They make speed possible
4. **Checkpoint Pattern** — Analyze → Plan (STOP) → Execute (STOP) → Verify. Never let AI auto-pilot through all phases
5. **Jagged Intelligence** — AI is brilliant at complex tasks but fails at simple ones. Build verification around known weaknesses

---

## Directory Structure

```
.agents/
├── README.md                          ← You are here
├── init_prompt.md                     ← 🔥 THE MASTER PROMPT — initializes all skills
│
├── context/                           ← 📍 PROJECT CONTEXT (load by task)
│   ├── project_status.md             ← ★ Always read first — current state
│   ├── backend.md                     ← Backend architecture, endpoints, patterns
│   ├── law_corpus.md                  ← Law data: 9,450 chunks, ChromaDB schema
│   └── production.md                  ← VPS deployment guide (Caddy, Docker, backups)
│
├── code_architect/                    ← System design + code quality superpowers
│   └── context.md                     ← Deep patterns, anti-patterns, templates
│
├── debug_surgeon/                     ← Surgical debugging + root cause analysis
│   └── context.md                     ← Hypothesis-driven investigation protocol
│
├── rag_specialist/                    ← RAG pipeline optimization expertise
│   └── context.md                     ← Retrieval, reranking, embedding craft
│
├── security_hardener/                 ← Security-first thinking for production
│   └── context.md                     ← Threat models, hardening, compliance
│
├── georgian_legal/                    ← Domain expertise: Georgian law system
│   └── context.md                     ← Legal structure, citations, terminology
│
├── context_engineer/                  ← 🧠 META-SKILL: maximize AI effectiveness
│   └── context.md                     ← Context pyramid, patterns, anti-patterns
│
└── workflows/                         ← 📋 Copy-paste workflow prompts
    ├── README.md                      ← Index of all workflows
    ├── 01_spec_to_build.md            ← Feature: spec → plan → build → verify
    ├── 02_bug_to_fix.md               ← Bug: reproduce → isolate → fix → prevent
    ├── 03_code_review.md              ← Review: architecture → quality → security
    ├── 04_test_generation.md          ← Test: analyze → write → verify
    ├── 05_optimize.md                 ← Perf: profile → bottleneck → optimize
    ├── 06_refactor.md                 ← Refactor: assess → safety net → restructure
    ├── 07_endpoint_builder.md         ← Endpoint: schema → repo → service → route
    └── 08_deploy_checklist.md         ← Deploy: verify → backup → push → smoke test
```

---

## How to Use

### Quick Start (paste into any AI conversation)

```
Read `.agents/init_prompt.md` — this is your skill initialization file.
Then read the relevant skill context from `.agents/<skill>/context.md`.
```

### Skill Selection Guide

| Task | Load These Skills |
|------|------------------|
| **Starting any task** | `context/project_status.md` (always first) |
| Working on the backend | `context/backend.md` + `code_architect` |
| Working on Flutter app | `frontend/.agents/orchestrator.md` |
| Working on design system | `packages/open-design/design-systems/kanonis-ostati/DESIGN.md` |
| Debugging a production issue | `debug_surgeon` + `context/backend.md` |
| Improving search/retrieval quality | `rag_specialist` + `context/law_corpus.md` |
| Deploying / hardening for production | `security_hardener` + `context/production.md` |
| Working with Georgian law content | `georgian_legal` + `context/law_corpus.md` |
| Feature planning | `master_plan/04_feature_roadmap.md` |
| Improving your AI collaboration | `context_engineer` |
| **Any specific task** | Use a workflow from `workflows/` |
| **Full context (new agent onboarding)** | `init_prompt.md` (loads all) |

### Using Workflows

Workflows are **copy-paste prompt recipes** for common tasks. They encode the Spec-Driven Development pattern:

```
Define Success → Plan (STOP for approval) → Execute → Verify → Document
```

See `.agents/workflows/README.md` for the full index.

---

## Principles

1. **Skills are composable** — load only what you need for the task
2. **Context is precious** — every token of context should earn its place
3. **Judgment > Knowledge** — teach the AI *how to think*, not just what to know
4. **Project-specific** — these skills are calibrated for THIS codebase, not generic advice
5. **Living documents** — update skills as the project evolves
6. **Verification-first** — every workflow ends with "verify it works"
7. **Checkpoint control** — human approves the plan before AI executes
