# 📝 User Notes

> Personal notes, decisions, observations, and context that AI agents should reference. 
> This is **your voice** — the human-in-the-loop memory.

---

## Structure

```
.user_notes/
├── README.md              ← You are here
├── decisions.md           ← Architecture/product decisions with rationale
├── observations.md        ← Things you noticed during testing/usage
├── priorities.md          ← Current priorities and what matters most
└── session_log.md         ← Quick notes from each working session
```

---

## How to Use

1. **Before starting a session** — jot down what you want to achieve in `session_log.md`
2. **When you make a decision** — record it in `decisions.md` with the "why"
3. **When you notice something** — drop it in `observations.md`
4. **When priorities shift** — update `priorities.md`

AI agents should read `.user_notes/` at the start of each session to align with your current thinking.

---

## Why This Exists

AI agents are powerful but stateless. They don't know:
- What you tried yesterday that didn't work
- Why you chose approach A over approach B
- What your current gut feeling is about the product
- Which features you care about most right now

This directory bridges that gap. It's the "human context" that makes AI collaboration 10x more effective.
