# Flutter Project Bootstrap & Context Extraction Prompt

*User Instructions: Feed this entire file to the AI when onboarding it to a pre-existing Flutter project or when initializing a brand new one.*

---
**PROMPT TO AI:**

"We are bootstrapping this Flutter project into our AI Workspace. You must immediately switch to **INIT mode**. Your objective is to comprehensively map the project, extract its specific domain rules, identify technical debt, and populate your `.agents/project_guide/` memory banks.

Execute the following 5 phases sequentially and meticulously:

### Phase 1: Rule Extraction & Architectural Comparison
1.  **Scan the Codebase:** Recursively read the `lib/` and `packages/` directories.
2.  **Compare against General Guides:** Cross-reference the project's structure, state management, and data layer patterns against our established standards in `.agents/general_guide/`.
3.  **Identify Deviations:** Note any project-specific patterns that override general rules (e.g., using Riverpod instead of BLoC, a custom routing solution, Freezed for models). These are not necessarily "wrong," but must be documented as the project's specific "dialect."

### Phase 2: Populate `project_context.md`
Overwrite `.agents/project_guide/project_context.md` with a highly detailed breakdown:
1.  **Core Overview:** Define the Project Name, Target Audience, and Core Value Proposition. (If this is a new empty project, ask me for these details first).
2.  **Technical Stack:** Parse `pubspec.yaml` and create a table of key dependencies and their versions (`flutter`, `bloc`, `go_router`, `get_it`, `hive`, `dio`, etc.).
3.  **Third-Party Integrations:** List all external services you can identify from imports or configuration files (e.g., Firebase, Sentry, Stripe).
4.  **Core Business Domains:** Based on the folder names in `lib/src/features/`, list the app's primary features (e.g., 'Authentication', 'Book Reading', 'Character Creation').

### Phase 3: Populate `architecture_state.md` & Log Refactors
Overwrite `.agents/project_guide/architecture_state.md` with the current implementation status:
1.  **Feature Completion Status:** Create a markdown checklist of all identified major features and estimate their completeness.
2.  **API & Routing Maps:**
    -   Scan the GoRouter configuration and create a GoRouter map table (`Route Name`, `Route Path`, `Payload Class`).
    -   Scan repository implementations and create an API Endpoints table (`Feature`, `Endpoint`, `Method`, `Repository Method`).
3.  **Data Models Dictionary:** Create a table of core domain entities (`Model Name`, `Description`, `File Location`).
4.  **Refactor Logging (CRITICAL):** Create a 'Technical Debt & Violations' section. Create a checklist of files and line numbers that violate our core architecture:
    -   `[ ] path/to/repo.dart:55 - Repository throws an exception instead of returning a Sealed Failure class.`
    -   `[ ] path/to/widget.dart:120 - UI Widget directly calls sl.get<AuthRepository>() instead of using a Cubit.`
    -   `[ ] path/to/button.dart:32 - Hardcoded string 'Submit' found. Should use context.l10n.submit.`
    -   `[ ] path/to/header.dart:15 - Hardcoded color Colors.blue found. Should use context.uiColors.primary.`

### Phase 4: Populate `file_tree.md`
Overwrite `.agents/project_guide/file_tree.md` with a structural map of the project, focusing on the `lib/src/features/` and `packages/ui_kit/` directories to illustrate the architectural boundaries.

### Phase 5: Workflow Alignment
Review `.agents/workflows/` and `.agents/self_heal/`.
1.  Confirm that the project uses FVM by checking for an `.fvm/` directory. Update test commands to use `fvm flutter test`.
2.  Check for custom scripts (`./exp.sh`, `./loc.sh`) and ensure they are documented in `workflows/automation_scripts.md`.

**Completion Gate:**
Once all 5 phases are complete, output a summary report of your findings, list the major technical debt items you logged, and explicitly confirm: *'INIT mode complete. Flutter Workspace memory is fully populated and ready for the 4-Persona Lifecycle.'*"
