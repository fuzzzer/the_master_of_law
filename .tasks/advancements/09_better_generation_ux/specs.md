# Specs: Better Generation UX

## Behavioral Specs

| Scenario | System State | User Interface Should Show |
| :--- | :--- | :--- |
| User submits query | Expanding Query & Vector Search | "Querying law..." indicator |
| RAG pipeline retrieves documents | Synthesizing Context | "Thinking..." indicator |
| Gemini starts generating | First token received | Indicator disappears, first text chunk appears |
| Gemini generating | Streaming tokens | Text typing out in the chat bubble |
| Gemini finishes | Stream complete | Final markdown rendered response |

## Technical Constraints

- **Streaming Protocol:** Use Server-Sent Events (SSE) or WebSockets (since WebSockets might already be used, see Architecture). SSE is often simpler for unidirectional text streaming.
- **Payload Structure (Example SSE):**
  - `event: status`, `data: querying_law`
  - `event: status`, `data: thinking`
  - `event: chunk`, `data: "According "`
  - `event: chunk`, `data: "to the law..."`
  - `event: done`, `data: {}`
- **Flutter Frontend:** Use `StreamBuilder` or a similar reactive pattern to handle incoming stream chunks efficiently without rebuilding the entire screen unnecessarily.

## Go/No-Go Criteria

- [ ] The user must see exactly what the system is doing before text generation starts.
- [ ] Text must stream in a typewriter-like effect, not arrive in one giant block.
- [ ] Stream chunk processing on the frontend must not block the main UI thread (no jank).
