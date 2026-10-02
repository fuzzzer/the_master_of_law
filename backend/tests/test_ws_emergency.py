"""
On the socket, a person in danger is told about 112 first — and keeps it.

Production, 2026-10-01: "ქმარი მცემს, ახლა სახლშია და მემუქრება. რა ვქნა?"
— the saved conversation held only two quota errors.

Needs the migrated test database (`scripts/test-db.sh up`).
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

import app.models.database as db_module
from app.main import app
from app.services.guardrail_service import GuardrailDecision
from tests.test_agy_verification import _drain_until

DANGER = "ქმარი მცემს, ახლა სახლშია და მემუქრება. რა ვქნა?"
QUOTA_429 = "429 RESOURCE_EXHAUSTED. You exceeded your current quota. 'retryDelay': '41s'"


def _reset_engine():
    db_module._engine = None
    db_module._session_factory = None


def _conversation(login_id: str) -> str:
    from app.repositories.user_repository import UserRepository
    from app.services.conversation_service import ConversationService

    async def setup() -> str:
        async with db_module.get_session_factory()() as db:
            await UserRepository(db).create_or_update(firebase_uid=login_id)
            conv = await ConversationService(db).create_conversation(user_id=login_id, title="t")
            await db.commit()
            return conv["id"]

    _reset_engine()
    conversation_id = asyncio.run(setup())
    _reset_engine()
    return conversation_id


def _stored(conversation_id: str) -> list[tuple[str, str]]:
    from app.services.conversation_service import ConversationService

    async def read():
        async with db_module.get_session_factory()() as db:
            return (await ConversationService(db).get_conversation(conversation_id))["messages"]

    _reset_engine()
    messages = asyncio.run(read())
    _reset_engine()
    return [(m["role"], m["content"]) for m in messages]


def _turn(conversation_id, login_id, guardrail, pipeline):
    frames = []
    with patch("app.integrations.firebase_client.verify_id_token", return_value={"uid": login_id}), \
            patch("app.services.guardrail_service.GuardrailService.classify", guardrail), \
            patch("app.services.agent_pipeline_service.AgentPipelineService.run", pipeline):
        with TestClient(app).websocket_connect(f"/api/v1/chat/{conversation_id}/ws?token=t") as ws:
            ws.send_json({"message": DANGER, "mode": "chat"})
            first = ws.receive_json()
            frames.append(first)
            last = _drain_until(ws, first, stop={"error", "done"})
            frames.append(last)
    return frames


def test_the_emergency_reply_arrives_and_stays_even_when_every_model_call_fails():
    login_id = f"ws-danger-{uuid.uuid4().hex[:8]}"
    conversation_id = _conversation(login_id)
    guardrail = AsyncMock(side_effect=RuntimeError(QUOTA_429))
    pipeline = AsyncMock(side_effect=RuntimeError(QUOTA_429))

    first, last = _turn(conversation_id, login_id, guardrail, pipeline)

    assert first["type"] == "chunk" and "112" in first["content"], first
    assert "116 006" in first["content"]
    assert last["type"] == "error", "the failure is still reported honestly"
    stored = _stored(conversation_id)
    assert stored[0] == ("user", DANGER)
    assert stored[1][0] == "assistant" and "112" in stored[1][1]
    assert stored[2][0] == "error"


def test_the_legal_answer_follows_the_emergency_reply_in_one_message():
    login_id = f"ws-danger-{uuid.uuid4().hex[:8]}"
    conversation_id = _conversation(login_id)
    guardrail = AsyncMock(return_value=GuardrailDecision(category="legal", confidence=1.0, should_proceed=True))
    result = MagicMock(response_text="შემაკავებელი ორდერი…", chunks=[], verified_citations=[], tool_results=[])
    pipeline = AsyncMock(return_value=result)

    first, last = _turn(conversation_id, login_id, guardrail, pipeline)

    assert first["type"] == "chunk" and "112" in first["content"]
    assert last["type"] == "done"
    assert last["full_response"].startswith(first["content"])
    assert last["full_response"].endswith("შემაკავებელი ორდერი…")
    assert _stored(conversation_id)[1] == ("assistant", last["full_response"])


def test_the_rest_chat_route_answers_with_112_when_the_model_fails():
    from fastapi import FastAPI, Request

    from app.middleware.error_handler_middleware import ErrorHandlerMiddleware
    from app.routes.chat_router import router

    login_id = f"rest-danger-{uuid.uuid4().hex[:8]}"
    conversation_id = _conversation(login_id)
    rest = FastAPI()
    rest.add_middleware(ErrorHandlerMiddleware)

    @rest.middleware("http")
    async def as_caller(request: Request, call_next):
        request.state.user = {"uid": login_id, "tier": "ADMIN"}
        return await call_next(request)

    rest.include_router(router)
    with patch("app.services.guardrail_service.GuardrailService.classify",
               AsyncMock(side_effect=RuntimeError(QUOTA_429))), \
            TestClient(rest) as client:
        r = client.post(f"/api/v1/chat/{conversation_id}/send", json={"message": DANGER})
    _reset_engine()

    assert r.status_code == 200, r.text
    assert "112" in r.json()["response"] and "ლიმიტი" in r.json()["response"]
    stored = _stored(conversation_id)
    assert stored[0] == ("user", DANGER)
    assert stored[1][0] == "assistant" and "112" in stored[1][1]
    assert stored[2][0] == "error"


def test_a_turn_slower_than_the_apps_silence_window_keeps_the_socket_alive():
    """Production, 2026-10-01: one drafting call took 73 s with no frame
    sent; the app gives up after 60 s of silence, so the user saw an error
    while the server kept spending their quota. Here the window is shrunk:
    a pipeline 6× slower than the heartbeat interval."""
    login_id = f"ws-slow-{uuid.uuid4().hex[:8]}"
    conversation_id = _conversation(login_id)
    allow = AsyncMock(return_value=GuardrailDecision(category="legal", confidence=1.0, should_proceed=True))
    result = MagicMock(response_text="პასუხი", chunks=[], verified_citations=[], tool_results=[])

    async def slow_model_call(*_args, **_kwargs):
        await asyncio.sleep(0.3)
        return result

    frames = []
    with patch("app.routes.ws_chat_router.WS_HEARTBEAT_INTERVAL_S", 0.05), \
            patch("app.integrations.firebase_client.verify_id_token", return_value={"uid": login_id}), \
            patch("app.services.guardrail_service.GuardrailService.classify", allow), \
            patch("app.services.agent_pipeline_service.AgentPipelineService.run", slow_model_call):
        with TestClient(app).websocket_connect(f"/api/v1/chat/{conversation_id}/ws?token=t") as ws:
            ws.send_json({"message": "კითხვა", "mode": "chat"})
            while True:
                frames.append(ws.receive_json())
                if frames[-1]["type"] in ("done", "error") or len(frames) > 200:
                    break

    kinds = [f["type"] for f in frames]
    assert kinds[-1] == "done", kinds
    assert kinds.count("heartbeat") >= 3, kinds
