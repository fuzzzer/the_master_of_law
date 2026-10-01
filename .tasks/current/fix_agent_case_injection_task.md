# Fix Agent Case Injection (Arguments & TC)

## Objective
Fix the issue where the AI agent is failing to correctly generate or inject "arguments" and "tc" (timeline/circumstances/test cases) into the case file.

## Context
- Issue reported: "agent generating or injecting arguments and tc in the case DOES NOT WORK".
- This is part of the case builder / case generation workflow where the AI structures user-provided context into a legal case entity.
- The fields for `arguments` and `tc` might be missing from the prompt, failing to parse from the LLM output, or failing to save to the database.

## Tasks
- [ ] Identify the exact meaning/location of "tc" and "arguments" in the schema (e.g. `Argument` model, timeline events, etc.).
- [ ] Review the `CaseBuilderService` (or relevant case generation service) to trace the prompt generation and response parsing for these fields.
- [ ] Ensure the Gemini model output correctly maps to the expected schema for these lists.
- [ ] Fix any parsing or database injection errors preventing them from being saved to the case.
- [ ] Add unit/integration tests to verify that arguments and TC are successfully populated during auto-case generation.
