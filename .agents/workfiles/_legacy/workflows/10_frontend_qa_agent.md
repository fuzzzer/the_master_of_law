# 🕵️ Antigravity QA Testing Workflow

> **Purpose:** Automate manual QA testing by deploying an Antigravity browser subagent to interact with the Flutter Web build, finding visual bugs, and documenting them.

## Step 1: Start the Local Environments
Before testing, ensure both the backend and frontend are running.

1. Start the FastAPI backend (if not mocked):
   ```bash
   cd backend && ./dev_runner.sh
   ```
2. Start the Flutter Web server on a fixed port:
   ```bash
   cd frontend && flutter run -d chrome-web-server --web-port=8080
   ```

## Step 2: Spawn the QA Browser Subagent

Use the `browser_subagent` tool with the following prompt configuration. 

**TaskName:** `Frontend QA and Bug Hunter`
**RecordingName:** `flutter_web_qa_session`
**TaskSummary:** `Test core user flows in the Flutter web app and report UI/UX bugs.`

**Task Prompt:**
```text
Navigate to http://localhost:8080. You are acting as a strict Human QA Tester evaluating the "Fuzzzy Law" application. Your job is to test complex interaction flows and hunt for bugs.

Perform the following flows sequentially:
1. **Navigation Check**: Click through all the main bottom navigation tabs (Chat, Cases, Laws, Notes, Profile). Ensure the transitions are smooth and the correct pages load.
2. **Case Builder Flow**: 
   - Navigate to the "Cases" section.
   - Interact with a case dashboard.
   - Attempt to interact with Facts, Arguments, and Action Items.
3. **Chat Interaction**:
   - Navigate to the "Chat" section.
   - Click the input field and type a long query.
   - Submit it and observe the loading state and the rendering of the response.

During your entire session, actively search for and take note of:
- **Layout Issues**: Text overflowing containers, overlapping widgets, or poorly scaled fonts.
- **Responsiveness**: Elements that don't scale properly.
- **Interactivity**: Buttons or links that do not respond, or missing hover indicators.
- **Visual Glitches**: Colors that clash, hard-to-read text, or broken icons.

When you have completed the flows, STOP and RETURN a highly detailed Bug Report. List every anomaly, exactly what screen it occurred on, and describe the visual state in detail. If the app is "smooth as butter" with no bugs, state that clearly.
```

## Step 3: Document Findings

Once the subagent completes its task and returns the bug report, the main Antigravity agent must save the output:

- Create or append to a file at `frontend/docs/qa_reports/latest_run.md`.
- Ensure the subagent's video recording is referenced for developers to review.
