# QA Test Case: AI Chat & Legal Consultation

**Feature:** The main conversational interface where users interact with the legal AI.
**Goal:** Verify streaming rendering, citation linking, state preservation, and chat UX.

## TC-01: Basic Query & Streaming Response
**Pre-conditions:** Logged in, on the "Chat" tab.
1. Type a query: "My landlord hasn't fixed the heater in 2 months. What are my rights?"
2. Tap "Send".
   - **Expected:** The message appears immediately in a user-styled chat bubble on the right. An elegant "typing" indicator appears on the left.
3. Observe the AI response.
   - **Expected:** The text streams in smoothly. The scroll view automatically follows the bottom of the content as it grows.
   - **Visuals:** Markdown elements (bold text, lists) render flawlessly as they stream.

## TC-02: Citation Interaction
**Pre-conditions:** The AI has provided a response containing legal citations.
1. Locate a citation chip (e.g., "Article 170") in the AI's response.
2. Tap the chip.
   - **Expected:** A modal or bottom sheet smoothly slides up, displaying the full text of Article 170 from the Georgian Civil Code.
   - **Performance:** Modal opening should be instantaneous (no heavy network delays if cached, or a quick skeleton loader if fetching).

## TC-03: Chat State Preservation
**Pre-conditions:** Active chat with multiple messages.
1. Navigate away from the Chat tab to the "Profile" tab.
2. Navigate back to the Chat tab.
   - **Expected:** The chat history is preserved exactly as left. The scroll position is maintained.
3. Hard reload the application (refresh browser or restart app).
   - **Expected:** The chat history loads seamlessly from local storage (Hive). No messages are lost.

## TC-04: Network Degradation
**Pre-conditions:** Active chat.
1. Send a message.
2. Immediately toggle Airplane Mode / Disable Network.
   - **Expected:** The message fails to send. A clear visual indicator (e.g., a red exclamation mark or "Retry" button) appears next to the failed message.
3. Re-enable Network and tap Retry.
   - **Expected:** The message sends successfully and the AI responds.

## TC-05: RAG Feature Flag Toggles (If exposed in Dev Panel)
**Pre-conditions:** Chat interface loaded.
1. Open Dev Panel and disable "Supreme Court RAG Collection".
2. Ask a question regarding court practice.
   - **Expected:** The AI should answer based only on Statutes (Georgian Laws), stating that it cannot access court practice.
