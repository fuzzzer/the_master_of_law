from app.routes.ws_chat_router import _build_gemini_contents
from google.genai import types

def test_alternating():
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "again"},
    ]
    contents = _build_gemini_contents(history, "current")
    for c in contents:
        print(c.role)

test_alternating()
