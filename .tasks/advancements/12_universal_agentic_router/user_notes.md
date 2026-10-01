# User Notes

- **The Ultimate Goal**: We are building a "clever advocate agent that helps in everything". It should not feel like a standard chatbot. It should feel like a relentless legal assistant that has its hands on the keyboard of the app.
- **Maintainability Over Hacks**: Do not use massive regex strings to parse LLM outputs. Use strict Pydantic schemas and structured generation. This makes the code reviewable and bulletproof.
- **Data Flow Clarity**: Every engineer should be able to look at the `Orchestrator` and immediately understand what happens after what. No hidden side-effects.
- **Safety First**: The agent has unrestricted access to read, analyze, and build arguments. But for actions like deleting cases or spending money, the Dangerous Action Protocol (DAP) must be an impenetrable wall requiring human authorization.
- **UI Extensibility**: Design the payload structure so that if we want the AI to generate a custom Flutter form in the future, the backend is already ready to send that command.
