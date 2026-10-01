# Flutter Project Bootstrap & Context Extraction Prompt

*User Instructions: Feed this entire file to the AI when onboarding it to a pre-existing Flutter project or when initializing a brand new one. This ensures the AI deeply understands the project and sets up its working memory correctly.*

---
**PROMPT TO AI:**

"We are bootstrapping this Flutter project into our AI Workspace. You must immediately switch to **INIT mode**. Your objective is to perform a deep forensic analysis of the codebase, populate your `.agents/project_guide/` memory banks with production-grade documentation, and identify all technical debt.

Execute the following 5 phases sequentially and meticulously:

### Phase 1: Rule Extraction & Architectural Comparison
1.  **Scan the Codebase:** Recursively read the entire `lib/` and `packages/` directories.
2.  **Compare against General Guides:** For every file you read, cross-reference its patterns against our master guide in `.agents/general_guide/flutter_architecture.md`.
3.  **Document Deviations:** Note any project-specific patterns that override general rules. For example: "This project uses Riverpod for state management, which differs from the standard BLoC/Cubit pattern outlined in the guide."

### Phase 2: Populate `project_context.md`
Overwrite `.agents/project_guide/project_context.md` with a detailed breakdown. **The output of this phase should be a document that another engineer could read to understand the entire project without looking at the code.**
1.  **Core Overview:** Define the Project Name, Target Audience, and Core Value Proposition.
2.  **Technical Stack:** Parse `pubspec.yaml` and create a markdown table of all key dependencies and their versions.
3.  **High-Level Architecture Document:** Generate a **Mermaid.js diagram** that visually maps the system architecture, mirroring the example in the master architecture guide. This diagram must show Entry Points, App Shell, Core Layer, Features, UI Kit, and Code Generators.

### Phase 3: Populate `architecture_state.md` & Log Refactors
Overwrite `.agents/project_guide/architecture_state.md`. **The output of this phase should be an exhaustive, live snapshot of the application's implementation details.**
1.  **Feature Implementation Status:** Create a detailed checklist of all features found in `lib/src/features/` and list their core components (Models, Repositories, Cubits, Pages). Mark them as `[x] Complete` or `[ ] In Progress`.
2.  **API & Routing Maps:**
    -   Scan the GoRouter configuration and generate a complete **GoRouter Map Table** (`Route Name`, `Route Path`, `Payload Class`).
    -   Scan all `*_repository.dart` files and generate a complete **API Endpoints Table** (`Feature`, `Endpoint`, `Method`, `Repository Method`).
3.  **Data Models Dictionary:** Scan all `models/` directories and generate a **Data Models Table** (`Model Name`, `Description`, `File Location`).
4.  **Refactor Logging (CRITICAL):** Create a 'Technical Debt & Violations' section. Scan the entire codebase and create a specific, actionable checklist of every violation of our architectural rules. Each item must include the file path and line number.
    -   `[ ] path/to/repo.dart:55 - VIOLATION: Repository throws an exception instead of returning a Sealed Failure class.`
    -   `[ ] path/to/widget.dart:120 - VIOLATION: UI Widget directly calls sl.get<AuthRepository>() instead of using a Cubit.`
    -   `[ ] path/to/button.dart:32 - VIOLATION: Hardcoded string 'Submit' found. Must be replaced with context.l10n.submit.`

### Phase 4: Populate `file_tree.md`
Overwrite `.agents/project_guide/file_tree.md`. Generate an ASCII-style directory tree of the `lib/` and `packages/ui_kit/` directories. The level of detail should be sufficient to show the canonical feature structure (`models`, `data`, `bloc`, `view`).

### Phase 5: Workflow Alignment
Review the project for custom scripts and tooling.
1.  Verify the presence of `fvm` and update all persona instructions to use `fvm flutter ...`.
2.  Verify the presence of `./exp.sh`, `./loc.sh`, `./gen.sh` and ensure they are documented.

**Completion Gate:**
Once all 5 phases are complete, output a summary report of your findings, highlight the top 3 most critical technical debt items you logged, and explicitly confirm: *'INIT mode complete. Flutter Workspace memory is fully populated and ready for the 4-Persona Lifecycle.'*"
