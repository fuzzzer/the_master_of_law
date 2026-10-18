# 🧠 Context Engineer — Skill Context

> **When to load:** When you want to maximize AI output quality, design better prompts, or optimize the human-AI collaboration loop.
> This is the **meta-skill** — it makes every other skill more effective.

---

## Philosophy: Context Engineering > Prompt Engineering

> *"The art of AI development is not crafting the perfect prompt. It is engineering the perfect context window."* — Anthropic, 2025

The difference between mediocre AI output and exceptional AI output is rarely the instruction — it's the **context**. A well-curated context window with 2,000 tokens of the RIGHT information beats 100,000 tokens of everything.

---

## The Context Pyramid

```
┌─────────────────────────┐
│      INSTRUCTION         │  ← What to do (smallest layer)
│    (5% of context)       │
├─────────────────────────┤
│      CONSTRAINTS         │  ← What NOT to do
│    (10% of context)      │
├─────────────────────────┤
│      EXAMPLES            │  ← Show, don't tell
│    (15% of context)      │
├─────────────────────────┤
│      DOMAIN KNOWLEDGE    │  ← Project-specific context
│    (30% of context)      │
├─────────────────────────┤
│      CODEBASE CONTEXT    │  ← Relevant files, patterns
│    (40% of context)      │
└─────────────────────────┘
```

**Rule:** The more specific the codebase context, the less instruction you need.

---

## Effective Patterns

### 1. Declarative > Imperative

```
❌ IMPERATIVE: "First read the file, then find the function, then add error 
handling, then add a try/except, then log the error..."

✅ DECLARATIVE: "Add error handling to `process_query()` in 
rag_retrieval_service.py. It should catch ChromaDB connection errors 
and return a graceful fallback. Follow the existing error patterns 
in legal_analysis_service.py."
```

### 2. Show the Shape of Success

```
❌ VAGUE: "Write a good test"

✅ SHAPED: "Write a test for citation_service.extract_citations(). 
It should look similar to test_citation_extraction in tests/test_citation.py. 
Test with Georgian text input containing 'მუხლი 177' and verify 
it returns a list of Citation objects with article_number=177."
```

### 3. Constrain the Blast Radius

```
❌ OPEN: "Improve the RAG pipeline"

✅ CONSTRAINED: "Improve ONLY Stage 4 (reranking) in rag_retrieval_service.py.
Do not modify stages 0-3. The change must pass all existing tests. 
Target: reduce rerank candidates from 272 to ~50 by adding a 
cosine distance threshold of 0.4."
```

### 4. The Checkpoint Pattern (for complex tasks)

```
Phase 1: Analyze — read files, list what you'll change. STOP.
Phase 2: Plan — show me the exact changes. STOP.
Phase 3: Execute — make the changes.
Phase 4: Verify — run tests, provide evidence it works.

I will approve each phase before you proceed.
```

---

## Anti-Patterns That Kill Quality

### 1. The "Just Do It" Pattern
```
❌ "Add a case file export endpoint"
```
Missing: format, auth, credits, response schema, error handling. The AI will fill in all blanks with guesses.

### 2. The "Everything at Once" Pattern
```
❌ "Refactor the backend to use a better architecture, add caching, 
improve error handling, and add 50 new tests"
```
Too many concerns. Quality drops exponentially with scope.

### 3. The "No Context" Pattern
```
❌ "Fix the bug"
```
Missing: error message, reproduction steps, what was tried. Forces AI to guess.

### 4. The "Override Expertise" Pattern
```
❌ "Use this exact code: [paste 200 lines of untested code]"
```
Better: describe intent and constraints, let the AI apply project patterns.

---

## Session Management

### Starting a Session
```
1. State your goal (1 sentence)
2. Point to relevant context files
3. Set explicit scope boundaries ("do X, do NOT touch Y")
4. Define "done" criteria
```

### Mid-Session Course Correction
```
When the AI is going in the wrong direction:

❌ "No, that's wrong, try again"
✅ "The approach is off because [specific reason]. 
Instead, follow the pattern in [specific file]. 
The key constraint you missed is [specific constraint]."
```

### Ending a Session
```
1. Ask the AI to summarize what was done
2. Ask for any remaining concerns or tech debt introduced
3. Update .user_notes/session_log.md
4. Commit changes
```

---

## Prompt Templates for Common Situations

### "I Need to Understand This Code"
```
Read [FILE]. Explain:
1. What is the single responsibility of this module?
2. What are its inputs and outputs?
3. What external dependencies does it have?
4. What are the failure modes?
5. How does it fit into the architecture in AI_GUIDE.md?
Don't explain obvious things. Focus on non-obvious design decisions.
```

### "I Need to Make a Decision"
```
I'm deciding between [OPTION A] and [OPTION B] for [CONTEXT].

For each option, analyze:
1. Pros (max 3)
2. Cons (max 3)
3. Effort (hours)
4. Risk (what could go wrong)
5. Reversibility (easy to undo?)

Then give your recommendation with reasoning.
Consider our constraints: [TECH STACK, TIMELINE, SCALE].
```

### "Teach Me This Concept"
```
Explain [CONCEPT] as it applies to THIS project (Fuzzzy Law).
Use a concrete example from our codebase.
Skip the theory — I want to understand the practical implication.
What would break if we got this wrong?
```

---

## The Golden Rule of AI Collaboration

> **AI amplifies your direction, not your intent.**

If you give it a vague direction, it will amplify vagueness into confident-sounding nonsense. If you give it a precise direction with rich context, it will amplify that precision into exceptional output.

Your job is not to "prompt" the AI. Your job is to **engineer the context** that makes the right answer obvious.
