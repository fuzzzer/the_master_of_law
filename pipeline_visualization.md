## Current Pipeline Analysis

Here is a visualization of how data currently flows (and where it is failing to use your prompts):

### 1. General Chat (`ConsultationPage` & `chat_router.py`)
- Uses `CASE_INTAKE_SYSTEM` for unstructured conversation.
- **Problem:** `QUESTIONNAIRE_GENERATOR` is never called. It just chats freely.
- When enough messages accumulate, a UI button triggers `CaseBuilderService.build_case_file`.
- `CaseBuilderService` runs RAG, then `case_full_analysis` (generates text), then `CASE_BUILDER` (generates JSON). The text from `case_full_analysis` is currently buried in `rendered_text` and not shown to the user in chat.

### 2. AI Case Tab (`CaseWorkspacePage` & `case_agent_router.py`)
- **If the case is empty:** It falls back to the exact same unstructured `CASE_INTAKE_SYSTEM` from the general chat.
- It waits for the `[CASE_READY]` trigger.
- **Problem:** Again, `QUESTIONNAIRE_GENERATOR` is entirely ignored. The `case_full_analysis` only runs in the background when `update_case_file` is triggered, but its output isn't surfaced effectively to the user in the conversation.

---

## The Desired Pipeline (Proper Data Channeling)

To fix the orchestration and properly use the existing prompts, we need to implement a strict state machine for the AI Case Builder when starting an empty case:

1. **Phase 1: Questionnaire Generation (`QUESTIONNAIRE_GENERATOR`)**
   - User sends their first message (e.g., "I was fired illegally").
   - Before replying, the backend extracts the domain and calls `QUESTIONNAIRE_GENERATOR` to generate a structured list of 3-12 questions.
   
2. **Phase 2: Orchestrated Intake (`NARRATIVE_EXTRACTOR`)**
   - The agent asks the user the generated questions one by one.
   - As the user replies in chat, the backend uses `NARRATIVE_EXTRACTOR` to automatically fill out the questionnaire JSON in the background.
   
3. **Phase 3: Full Analysis (`CASE_FULL_ANALYSIS`)**
   - Once all required questions are answered, the agent stops asking questions.
   - The backend runs `CASE_FULL_ANALYSIS` using the structured Q&A and retrieved laws.
   - **Crucial Step:** The agent *sends* this full text analysis back to the user in the chat so they can read it!
   
4. **Phase 4: Case File Generation (`CASE_BUILDER`)**
   - Immediately after sending the analysis, the backend uses `CASE_BUILDER` to convert the analysis into the structured JSON (Facts, Arguments, Strategy, etc.).
   - The Case File is updated, and the UI unlocks all the case tabs (Facts, Laws, Risks, etc.).
