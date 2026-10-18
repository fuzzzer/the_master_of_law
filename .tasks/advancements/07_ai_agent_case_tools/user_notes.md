# User Notes: AI Agent Case Tools

> Drop manual reviews, edge cases, design feedback, or priority changes here.
> Agents will read this file before starting work.

---

## Design Feedback

_No feedback yet._

## Priority Adjustments

- Case attachment in standalone chat is a prerequisite — must work before agent mode
- Start with read-only tools (`get_case_summary`) to validate infrastructure
- Add write tools incrementally: create → update → delete

## Edge Cases to Watch

- What if user has multiple cases and switches mid-conversation?
- What if tool execution fails halfway (e.g., DB error after partial writes)?
- What if Gemini calls a tool with invalid arguments?
- Rate limit: prevent AI from spamming tool calls in a loop

## Review Notes

_No reviews yet._
