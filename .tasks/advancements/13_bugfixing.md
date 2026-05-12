# Bugfixing Task Tracker

## Bugs

1. [x] **Facts are not populated by AI analysis**
   - **Details:** Case "1778581658186" shows facts appended as text in the description but not saved in the facts list.
   - **Status:** Fixed. Modified `CaseFileRepository.update` in the backend to use `flag_modified` so SQLAlchemy recognizes the JSONB mutations.

2. [x] **Double Empty Message Box during Generation**
   - **Details:** Flutter incorrectly shows a second empty message box weirdly when "AI ფიქრობს" is active.
   - **Status:** Fixed. Refactored `ConsultationCubit` to inject the empty message bubble only after receiving the first response chunk, hiding the initial spinner simultaneously.

3. [x] **Missing Links to Georgian Laws**
   - **Details:** Ensure openable links to matsne.gov.ge or similar for all Georgian laws, both in AI responses and the "კანონები" (Laws) tab in a case.
   - **Status:** Fixed. Added `url` mapping to `CitationData` and connected `article_url` in both UI chat citations (`url_launcher`) and the `CaseDetailCubit` linked laws tab.

4. [x] **Agent Cannot Prompt Dangerous Action Verification by User**
   - **Details:** Agent is unable to prompt dangerous action verification (UI/Backend issue).
   - **Status:** Fixed. Added `_PendingConfirmationCard` component into `CaseChatSection.dart` which intercepts `pendingConfirmations` and displays them above the chat input allowing user explicitly Accept/Reject.
