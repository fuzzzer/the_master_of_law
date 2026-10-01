# Task: Better Generation UX

> **Covers:** Streaming responses, UI/UX updates during generation, Intermediate state indicators
> **Dependencies:** `01_law_chat_and_retrieval`

---

## Purpose

The user experience during AI response generation needs to be improved. Currently, users have to wait for the entire response to be fully generated before seeing any output. 

To make the platform feel more responsive and transparent, we need to implement streamed generation. Furthermore, before the actual stream of text begins, the UI should indicate the current background processes (e.g., "Querying law...", "Thinking..."), so the user understands what the system is doing. Once the content is ready, it should write through the stream.

---

## Multi-Step Guide

### Milestone 1: Backend Streaming & State Emission
1. Update `VertexAIClient` and the RAG pipeline to support streaming generation.
2. Modify the generation endpoint to use Server-Sent Events (SSE) or WebSockets.
3. Emit intermediate status events (e.g., `status: querying_law`, `status: thinking`) during the retrieval and expansion phases before the Gemini model starts generating.
4. **Verify:** You can connect to the endpoint via a cURL/client and see status events followed by streamed text chunks.

### Milestone 2: Frontend State Indicators
1. Update the Flutter app's chat UI to handle intermediate status events.
2. Display appropriate UI elements (like a loading indicator with text "Querying law..." or "Thinking...") when these events are received.
3. **Verify:** The user sees clear, descriptive text of what the system is doing before the text starts streaming.

### Milestone 3: Frontend Stream Rendering
1. Update the frontend chat bubble to accept streamed text chunks.
2. Append the text chunks to the message in real-time as they arrive.
3. Ensure the UI scrolls smoothly or updates without jank as new text is added.
4. **Verify:** The user can see the generated answer being written out word-by-word or chunk-by-chunk.

### Milestone 4: Testing & Verification
1. Test the full flow from query submission to complete streamed response.
2. Ensure there are no race conditions between state updates and the start of the text stream.
3. **Verify:** The end-to-end UX feels snappy, informative, and responsive.
