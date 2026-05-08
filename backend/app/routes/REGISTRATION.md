# Route Registration Guide (Conflict-Avoidance)

This file documents the one-line changes needed in `app/main.py` to register
new routers WITHOUT causing merge conflicts with parallel agents.

## Questionnaire Router

File: `backend/app/routes/questionnaire_router.py`

### Step 1 — Add import

In `backend/app/main.py`, add this line to the existing imports block:

```python
from app.routes import questionnaire_router
```

Place it alphabetically after `rag_router`:
```python
from app.routes import (
    account_router,
    auth_router,
    case_file_router,
    chat_router,
    conversation_router,
    health_router,
    law_browser_router,
    questionnaire_router,   # <-- ADD THIS
    rag_router,
    ws_chat_router,
)
```

### Step 2 — Register router

In `backend/app/main.py`, add this line in the routes section:

```python
    app.include_router(questionnaire_router.router)
```

Place it after `law_browser_router` and before `rag_router`:
```python
    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(account_router.router)
    app.include_router(conversation_router.router)
    app.include_router(chat_router.router)
    app.include_router(law_browser_router.router)
    app.include_router(questionnaire_router.router)  # <-- ADD THIS
    app.include_router(case_file_router.router)
    app.include_router(rag_router.router)
    app.include_router(ws_chat_router.router)
```

That's it — two one-line additions. No other files in `main.py` need changes.
