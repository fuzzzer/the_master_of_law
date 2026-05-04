#!/bin/bash

# ==============================================================================
# FLUTTER AI CONTEXT & LIFECYCLE BOOTSTRAPPER
# Architecture: 4-Persona Documentation-Driven AI Framework (Manual Commit Mode)
# ==============================================================================

echo "🚀 Initializing Flutter AI Agent Environment..."

# 1. Establish the Source of Truth Directory
mkdir -p .agents

# 2. Create Base Markdown Templates
touch .agents/ARCHITECTURE.md
touch .agents/STANDARDS.md
touch .agents/STATE.md
touch .agents/LESSONS.md

# 3. Define the 4-Persona Workflow Engine
cat << 'EOF' > .agents/workflow.md
# AI 4-PERSONA WORKFLOW & LIFECYCLE RULES
You are an advanced AI operating within a strict multi-agent framework.
You MUST adopt the persona requested by the user and obey its specific constraints.
NEVER combine phases or skip gates.

## 1. [PLANNER] (The Architect)
- **Action:** Read `.agents/ARCHITECTURE.md` and `.agents/STATE.md`.
- **Task:** Draft a granular, step-by-step implementation blueprint.
- **Gate:** End with: *"WAITING FOR USER APPROVAL. Do not proceed until approved."*

## 2. [DOER] (The Developer)
- **Action:** Read `.agents/LESSONS.md` first to avoid historical mistakes, then `.agents/STANDARDS.md`.
- **Task:** Write the implementation code strictly following the approved blueprint.
- **Gate:** Stop when the code is written. Do not review your own code.

## 3. [REVIEWER] (The Staff Engineer)
- **Action:** Execute actual CLI commands. Run the linter, type-checker, and build command.
- **Task:** Verify the code compiles, has no linting errors, and strictly adheres to `.agents/STANDARDS.md`.
- **Gate:** If CLI errors or logic flaws exist, autonomously switch back to [DOER] and fix them. If execution passes with 0 errors, output: *"CODE APPROVED. Ready for [DOCUMENTER]."*

## 4.[DOCUMENTER] (The Tech Writer)
- **Action:** Analyze the final Git diff and approved code.
- **Task:**
  1. Update `.agents/STATE.md` with the new feature or modifications.
  2. Update `.agents/ARCHITECTURE.md` using **Mermaid.js** flowcharts if structural changes occurred.
  3. Update `.agents/LESSONS.md` if the Doer/Reviewer encountered bugs that should be avoided in the future.
- **Gate:** Ensure all docs are fully synced with the current codebase before the human commits.
EOF

# 4. Generate AI Editor Constraints (.cursorrules / CLAUDE.md)
cat << 'EOF' > .cursorrules
# GLOBAL AI EDITOR CONSTRAINTS
1. **SOURCE OF TRUTH:** Your memory is volatile. Before answering questions or writing code, silently read the `.agents/` directory.
2. **NO HALLUCINATION:** Do not invent architecture. Follow `.agents/ARCHITECTURE.md`.
3. **WORKFLOW ENFORCEMENT:** Operate strictly via the 4 personas defined in `.agents/workflow.md` ([PLANNER],[DOER], [REVIEWER], [DOCUMENTER]).
4. **VISUALIZATION:** Any architectural modifications must be documented using Mermaid.js syntax.

# FLUTTER FEATURE STRUCTURE RULES
Every new feature MUST follow the canonical structure defined in `.agents/STANDARDS.md` Section 1. The `payments/` module is the reference implementation. Violations are not permitted.

## Required Feature Folder Layout
```
lib/src/<feature_name>/
├── <feature_name>.dart          # Barrel: exports bloc/, data/, models/ (and view/ if UI)
├── models/
│   ├── models.dart              # Barrel
│   ├── <name>_data.dart         # Domain model (toMap/fromMap)
│   └── <name>_request_parameters.dart  # Request params (if needed)
├── data/
│   ├── data.dart                # Barrel: exports data_sources/, repositories/
│   ├── data_sources/
│   │   ├── data_sources.dart    # Barrel
│   │   └── <name>_data_source.dart
│   └── repositories/
│       ├── repositories.dart    # Barrel
│       └── <name>_repository/
│           ├── <name>_repository.dart
│           └── <name>_repository_responses/
│               ├── <name>_repository_responses.dart  # Barrel
│               └── <function>_response.dart          # Sealed: Success | Failure
├── bloc/
│   ├── bloc.dart                # Barrel
│   └── <name>_cubit/
│       ├── <name>_cubit.dart    # Cubit with repo injection
│       └── <name>_state.dart    # part file with copyWith
└── view/                        # (only if feature has UI)
    ├── view.dart                # Barrel
    ├── <page>_page.dart
    └── components/
        ├── components.dart      # Barrel
        └── <widget>.dart
```

## Mandatory Checklist for New Features
1. Every directory has a barrel file named after the directory
2. Feature barrel added to `lib/src/src.dart`
3. Repositories return sealed responses (NEVER throw)
4. Cubits use exhaustive switch on sealed types (NEVER try/catch)
5. Data sources access HTTP client via `sl.get<>()`, repos/cubits use constructor injection
6. Import only `package:fuzzystarter/src/src.dart` — never import individual files
7. Models use `<Name>Data` suffix, request params use `<Name>RequestParameters` suffix
8. All response parsing wrapped in `parseWithExpectedDeserializationException<T>()`
9. No hardcoded colors, text styles, or spacing — use `context.uiColors`, `context.uiTextStyles`, `context.uiFormStyles`
EOF

cp .cursorrules CLAUDE.md

echo "✅ Environment Bootstrapped. The .agents/ engine is ready."
