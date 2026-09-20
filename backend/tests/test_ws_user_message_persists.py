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

    # The question survived the failure — and the failure itself is now
    # part of the conversation too, so a client that comes back later sees
    # that the turn ended rather than question-and-silence.
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "ჩემი კითხვა"),
        ("error", "დაფიქსირდა შეცდომა. გთხოვთ, სცადოთ თავიდან."),
    ]


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


def test_answer_is_stored_even_if_the_client_drops_during_the_guardrail():
    """Leaving BEFORE the first frame must not lose the answer either.

    The previous test leaves after the first status frame. Production showed
    the other timing: the guardrail's provider retries took eighteen seconds,
    the user backgrounded the tab meanwhile, and the very first send after
    the guardrail — a raw `send_json`, not `_safe_send` — raised on the gone
    client BEFORE the shielded turn existed. `ws_disconnected` in the log,
    no answer, no error, no trace. The turn never ran at all.
    """
    import time
    from unittest.mock import MagicMock

    import app.models.database as db_module

    db_module._engine = None
    db_module._session_factory = None

    firebase_uid = f"ws-drop-early-{uuid.uuid4().hex[:8]}"

    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository
    from app.services.conversation_service import ConversationService

    async def db_setup() -> str:
        async with get_session_factory()() as db:
            await UserRepository(db).create_or_update(
                firebase_uid=firebase_uid,
                email="ws-drop-early@fuzzzylaw.ge",
                display_name="WS Drop Early",
            )
            conv = await ConversationService(db).create_conversation(
                user_id=firebase_uid, title="drop early"
            )
            await db.commit()
            return conv["id"]

    conversation_id = asyncio.run(db_setup())
    db_module._engine = None
    db_module._session_factory = None

    result = MagicMock()
    result.response_text = "პასუხი ტაბის დახურვის მიუხედავად"
    result.chunks = []
    result.verified_citations = []
    result.tool_results = []

    allow = GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)

    async def slow_guardrail(*_args, **_kwargs):
        await asyncio.sleep(0.5)
        return allow

    with patch(
        "app.integrations.firebase_client.verify_id_token",
        return_value={"uid": firebase_uid, "email": "ws-drop-early@fuzzzylaw.ge"},
    ), patch(
        "app.services.guardrail_service.GuardrailService.classify",
        side_effect=slow_guardrail,
    ), patch(
        "app.services.agent_pipeline_service.AgentPipelineService.run",
        new_callable=AsyncMock,
        return_value=result,
    ), TestClient(app) as client:
        with client.websocket_connect(
            f"/api/v1/chat/{conversation_id}/ws?token=valid-token"
        ) as ws:
            ws.send_json({"message": "კითხვა", "mode": "chat"})
            # Leave while the guardrail is still classifying: after the
            # message was read (no frame is sent before the guardrail, so a
            # short wait is the only way to be sure), before it answers.
            time.sleep(0.2)
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
        ("assistant", "პასუხი ტაბის დახურვის მიუხედავად"),
    ]


def test_a_failed_turn_after_the_client_left_is_written_into_the_conversation():
    """Production, 07:26 UTC: the user left, the turn ran on and hit the
    provider's quota, the error frame went to a dead socket and the trace —
    and the conversation got nothing. The reloaded page showed the question
    and silence. The failure is a message now, and the model never sees it.
    """
    import time

    import app.models.database as db_module

    db_module._engine = None
    db_module._session_factory = None

    firebase_uid = f"ws-fail-gone-{uuid.uuid4().hex[:8]}"

    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository
    from app.services.conversation_service import ConversationService
    from app.services.turn_registry import turn_in_progress

    async def db_setup() -> str:
        async with get_session_factory()() as db:
            await UserRepository(db).create_or_update(
                firebase_uid=firebase_uid,
                email="ws-fail-gone@fuzzzylaw.ge",
                display_name="WS Fail Gone",
            )
            conv = await ConversationService(db).create_conversation(
                user_id=firebase_uid, title="fail gone"
            )
            await db.commit()
            return conv["id"]

    conversation_id = asyncio.run(db_setup())
    db_module._engine = None
    db_module._session_factory = None

    allow = GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)

    async def slow_quota_failure(*_args, **_kwargs):
        await asyncio.sleep(0.5)
        raise RuntimeError("429 RESOURCE_EXHAUSTED. You exceeded your current quota")

    with patch(
        "app.integrations.firebase_client.verify_id_token",
        return_value={"uid": firebase_uid, "email": "ws-fail-gone@fuzzzylaw.ge"},
    ), patch(
        "app.services.guardrail_service.GuardrailService.classify",
        new_callable=AsyncMock,
        return_value=allow,
    ), patch(
        "app.services.agent_pipeline_service.AgentPipelineService.run",
        side_effect=slow_quota_failure,
    ), TestClient(app) as client:
        with client.websocket_connect(
            f"/api/v1/chat/{conversation_id}/ws?token=valid-token"
        ) as ws:
            ws.send_json({"message": "კითხვა", "mode": "chat"})
            assert ws.receive_json()["type"] in ("status", "stage")
        # Gone. Meanwhile the turn is still running:
        time.sleep(0.1)
        assert turn_in_progress(conversation_id)
        time.sleep(1.5)
        assert not turn_in_progress(conversation_id)

    db_module._engine = None
    db_module._session_factory = None

    async def stored() -> tuple[list[dict], list[dict]]:
        async with get_session_factory()() as db:
            svc = ConversationService(db)
            conv = await svc.get_conversation(conversation_id)
            return conv["messages"], await svc.get_conversation_history(conversation_id)

    messages, history = asyncio.run(stored())
    db_module._engine = None
    db_module._session_factory = None

    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "კითხვა"),
        ("error", "AI სერვისის დღიური ლიმიტი ამოიწურა. სცადეთ მოგვიანებით ან სხვა მოდელით."),
    ]
    assert [m["role"] for m in history] == ["user"], "the model never sees a failure"


def test_the_conversation_says_a_turn_is_in_progress_while_it_runs():
    """A page reloaded mid-turn asks the conversation and is told to wait."""
    import time
    from unittest.mock import MagicMock

    import app.models.database as db_module

    db_module._engine = None
    db_module._session_factory = None

    firebase_uid = f"ws-inprog-{uuid.uuid4().hex[:8]}"

    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository
    from app.services.conversation_service import ConversationService

    async def db_setup() -> str:
        async with get_session_factory()() as db:
            await UserRepository(db).create_or_update(
                firebase_uid=firebase_uid,
                email="ws-inprog@fuzzzylaw.ge",
                display_name="WS In Progress",
            )
            conv = await ConversationService(db).create_conversation(
                user_id=firebase_uid, title="in progress"
            )
            await db.commit()
            return conv["id"]

    conversation_id = asyncio.run(db_setup())
    db_module._engine = None
    db_module._session_factory = None

    result = MagicMock()
    result.response_text = "პასუხი"
    result.chunks = []
    result.verified_citations = []
    result.tool_results = []

    async def slow_pipeline(*_args, **_kwargs):
        await asyncio.sleep(0.8)
        return result

    allow = GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)
    auth = {"Authorization": "Bearer valid-token"}

    with patch(
        "app.integrations.firebase_client.verify_id_token",
        return_value={"uid": firebase_uid, "email": "ws-inprog@fuzzzylaw.ge"},
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
        time.sleep(0.1)
        during = client.get(f"/api/v1/conversations/{conversation_id}", headers=auth).json()
        time.sleep(1.5)
        after = client.get(f"/api/v1/conversations/{conversation_id}", headers=auth).json()

    db_module._engine = None
    db_module._session_factory = None

    assert during["turn_in_progress"] is True
    assert [m["role"] for m in during["messages"]] == ["user"]
    assert after["turn_in_progress"] is False
    assert [m["role"] for m in after["messages"]] == ["user", "assistant"]


def test_no_login_mode_never_meters_credits_on_the_socket():
    """Under no-login / bring-your-own-key the user pays Google with their own
    key, so there is no operator spend to meter. The HTTP credit gate already
    stands down in that mode; the socket did not, and QA found production's
    launch mode refusing the sixth message of the day for a balance that
    measured nothing.
    """
    from unittest.mock import MagicMock

    import app.models.database as db_module
    from app.config.settings import settings
    from app.utils.anonymous_identity import ANON_UID_PREFIX

    db_module._engine = None
    db_module._session_factory = None

    device_id = f"qa-device-{uuid.uuid4().hex[:8]}"
    uid = f"{ANON_UID_PREFIX}{device_id}"

    from app.models.database import get_session_factory
    from app.repositories.credit_repository import CreditRepository
    from app.repositories.user_repository import UserRepository
    from app.services.conversation_service import ConversationService

    async def db_setup() -> str:
        async with get_session_factory()() as db:
            user = await UserRepository(db).create_or_update(firebase_uid=uid)
            credits = await CreditRepository(db).get_or_create(user.id)
            credits.daily_credits_used = 999  # nothing left, if it were metered
            conv = await ConversationService(db).create_conversation(
                user_id=uid, title="byok"
            )
            await db.commit()
            return conv["id"]

    conversation_id = asyncio.run(db_setup())
    db_module._engine = None
    db_module._session_factory = None

    result = MagicMock()
    result.response_text = "პასუხი"
    result.chunks = []
    result.verified_citations = []
    result.tool_results = []
    allow = GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)

    with patch.object(settings, "auth_enabled", False), patch(
        "app.services.guardrail_service.GuardrailService.classify",
        new_callable=AsyncMock,
        return_value=allow,
    ), patch(
        "app.services.agent_pipeline_service.AgentPipelineService.run",
        new_callable=AsyncMock,
        return_value=result,
    ), TestClient(app) as client:
        with client.websocket_connect(
            f"/api/v1/chat/{conversation_id}/ws?device_id={device_id}"
        ) as ws:
            for text in ("პირველი", "მეორე"):
                ws.send_json({"message": text, "mode": "chat"})
                frame = _drain_until(ws, ws.receive_json(), stop={"error", "done"})
                assert frame["type"] == "done", frame

    db_module._engine = None
    db_module._session_factory = None

    async def used() -> int:
        async with get_session_factory()() as db:
            user = await UserRepository(db).get_by_firebase_uid(uid)
            return (await CreditRepository(db).get_or_create(user.id)).daily_credits_used

    assert asyncio.run(used()) == 999, "nothing was deducted"
    db_module._engine = None
    db_module._session_factory = None
