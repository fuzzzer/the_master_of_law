"""The message a user typed survives whatever happens to the answer.

Before this test, the WebSocket turn saved the user's message and the
assistant's answer in ONE transaction, committed at the end of the turn. Two
things followed: a reload mid-turn (the history sheet does one) showed the
conversation without the message just sent, and a pipeline failure rolled
the message back entirely — the chat bubble the user watched disappear.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.guardrail_service import GuardrailDecision
from tests.test_agy_verification import _drain_until


def test_user_message_is_committed_before_the_pipeline_runs():
    import app.models.database as db_module

    db_module._engine = None
    db_module._session_factory = None

    # Unique per run: the test database keeps users between runs, and a
    # reused user runs out of daily credits after five of them.
    firebase_uid = f"ws-persist-{uuid.uuid4().hex[:8]}"

    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository
    from app.services.conversation_service import ConversationService

    async def db_setup() -> str:
        async with get_session_factory()() as db:
            await UserRepository(db).create_or_update(
                firebase_uid=firebase_uid,
                email="ws-persist@fuzzzylaw.ge",
                display_name="WS Persist",
            )
            conv = await ConversationService(db).create_conversation(
                user_id=firebase_uid, title="persist"
            )
            await db.commit()
            return conv["id"]

    conversation_id = asyncio.run(db_setup())
    db_module._engine = None
    db_module._session_factory = None

    allow = GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)
    client = TestClient(app)

    with patch(
        "app.integrations.firebase_client.verify_id_token",
        return_value={"uid": firebase_uid, "email": "ws-persist@fuzzzylaw.ge"},
    ), patch(
        "app.services.guardrail_service.GuardrailService.classify",
        new_callable=AsyncMock,
        return_value=allow,
    ), patch(
        "app.services.agent_pipeline_service.AgentPipelineService.run",
        new_callable=AsyncMock,
        side_effect=RuntimeError("model exploded"),
    ):
        with client.websocket_connect(
            f"/api/v1/chat/{conversation_id}/ws?token=valid-token"
        ) as ws:
            ws.send_json({"message": "ჩემი კითხვა", "mode": "chat"})
            frame = _drain_until(ws, ws.receive_json(), stop={"error", "done"})
            assert frame["type"] == "error", frame

    db_module._engine = None
    db_module._session_factory = None

    async def stored_messages() -> list[dict]:
        async with get_session_factory()() as db:
            conv = await ConversationService(db).get_conversation(conversation_id)
            return conv["messages"]

    messages = asyncio.run(stored_messages())
    db_module._engine = None
    db_module._session_factory = None

    assert [(m["role"], m["content"]) for m in messages] == [("user", "ჩემი კითხვა")]


def test_answer_is_stored_even_if_the_client_drops_mid_turn():
    """Closing the tab, pressing back, losing signal: none of it loses the answer.

    The socket handler used to cancel the pipeline the moment the client went
    away. The user had paid for that answer with their own key and got nothing
    for it; on returning to the conversation they found their question and
    silence.
    """
    import time
    from unittest.mock import MagicMock

    import app.models.database as db_module

    db_module._engine = None
    db_module._session_factory = None

    firebase_uid = f"ws-drop-{uuid.uuid4().hex[:8]}"

    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository
    from app.services.conversation_service import ConversationService

    async def db_setup() -> str:
        async with get_session_factory()() as db:
            await UserRepository(db).create_or_update(
                firebase_uid=firebase_uid,
                email="ws-drop@fuzzzylaw.ge",
                display_name="WS Drop",
            )
            conv = await ConversationService(db).create_conversation(
                user_id=firebase_uid, title="drop"
            )
            await db.commit()
            return conv["id"]

    conversation_id = asyncio.run(db_setup())
    db_module._engine = None
    db_module._session_factory = None

    result = MagicMock()
    result.response_text = "პასუხი, რომელიც არ უნდა დაიკარგოს"
    result.chunks = []
    result.verified_citations = []
    result.tool_results = []

    async def slow_pipeline(*_args, **_kwargs):
        await asyncio.sleep(0.5)
        return result

    allow = GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)

    with patch(
        "app.integrations.firebase_client.verify_id_token",
        return_value={"uid": firebase_uid, "email": "ws-drop@fuzzzylaw.ge"},
    ), patch(
        "app.services.guardrail_service.GuardrailService.classify",
        new_callable=AsyncMock,
        return_value=allow,
    ), patch(
        "app.services.agent_pipeline_service.AgentPipelineService.run",
        side_effect=slow_pipeline,
    ), TestClient(app) as client:
        with client.websocket_connect(
            f"/api/v1/chat/{conversation_id}/ws?token=valid-token"
        ) as ws:
            ws.send_json({"message": "კითხვა", "mode": "chat"})
            assert ws.receive_json()["type"] in ("status", "stage")
            # Leave without waiting for the answer: the `with` closes the socket.
        time.sleep(1.5)

    db_module._engine = None
    db_module._session_factory = None

    async def stored_messages() -> list[dict]:
        async with get_session_factory()() as db:
            conv = await ConversationService(db).get_conversation(conversation_id)
            return conv["messages"]

    messages = asyncio.run(stored_messages())
    db_module._engine = None
    db_module._session_factory = None

    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "კითხვა"),
        ("assistant", "პასუხი, რომელიც არ უნდა დაიკარგოს"),
    ]
