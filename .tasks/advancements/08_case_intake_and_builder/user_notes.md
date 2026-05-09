# User Notes: Case Intake & AI Case Builder

> Agents read this file FIRST before starting work.

---

## Design Feedback

- No ducktape pattern matching on user messages (removed `user_demand_signals`)
- Readiness should come from the AI prompt or clean message-count heuristic, not from scanning user words
- If AI isn't producing the readiness signal, tune the prompt — don't workaround in the router

## Priority

1. Make readiness detection reliable (prompt tuning)
2. Validate Build Case → sections populate end-to-end
3. Validate case attachment context injection
4. Conversation titles are cosmetic but nice-to-have for now

## Edge Cases

- User says "I don't know" to AI questions → AI should still proceed with available info
- Very short initial messages (1-2 words) → AI should ask more
- Very long initial messages with everything → AI should skip questions and signal ready immediately

## Review Notes

- 2026-05-09: All milestones code-complete, awaiting device validation
- 2026-05-09: Removed `user_demand_signals` ducktape per user feedback
