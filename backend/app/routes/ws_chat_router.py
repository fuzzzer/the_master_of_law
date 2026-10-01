"""
WebSocket chat router — unified advocate with streaming + function calling.

WS /api/v1/chat/{conversation_id}/ws

Merges the old chat-only and case-agent flows into one WebSocket.
When case_file_id is present, AI has access to case tools.
When absent, it's a standard legal Q&A chat.
"""

from __future__ import annotations

import json
import re
import uuid as _uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from google.genai import types

from app.config.settings import settings
from app.config.constants import CreditAction, UserTier
from app.middleware.rate_limit_middleware import check_redis_rate_limit
from app.repositories.credit_repository import CreditRepository
from app.prompts.advocate import compose_advocate_prompt
from app.prompts.chat import CHAT_SYSTEM, CASE_INTAKE_SYSTEM
from app.services.agent_pipeline_service import get_agent_pipeline_service
from app.services.case_tool_executor import CaseToolExecutor
from app.services.conversation_service import ConversationService
from app.services.turn_registry import turn_finished, turn_started
from app.services.trace_service import record_step, save_current_trace, start_trace
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-ws"])


async def _fail_turn(websocket: WebSocket, conversation_id: str, exc: Exception) -> None:
    """Record a failed turn everywhere it has to be recorded.

    The message is rendered VERBATIM as a chat bubble in a Georgian-only
    app, so it is Georgian, and it says which of the three things went
    wrong rather than "an error". It goes into the conversation as a
    message of role ``error`` — on its own session, because the turn's may
    be poisoned by the very failure — into the trace, and to the socket if
    anyone is still there.
    """
    from app.models.database import get_session_factory
    from app.utils.provider_errors import classify

    provider = classify(exc)
    if provider.is_provider_fault:
        logger.warning(
            "ws_provider_error",
            kind=provider.kind.value,
            retry_after_s=provider.retry_after_s,
            error=str(exc)[:300],
        )
    else:
        logger.error("ws_processing_error", error=str(exc), exc_info=True)
    await save_current_trace(status="failed", error=str(exc))
    try:
        async with get_session_factory()() as edb:
            await ConversationService(edb).save_error_message(
                conversation_id=conversation_id, content=provider.message_ka,
            )
            await edb.commit()
    except Exception as save_exc:
        logger.error("ws_error_message_not_saved", error=str(save_exc))
    await _safe_send(websocket, {
        "type": "error",
        "code": provider.error_code,
        "message": provider.message_ka,
        **({"retry_after_s": provider.retry_after_s}
           if provider.retry_after_s else {}),
    })


async def _safe_send(websocket: WebSocket, data: dict) -> bool:
    """Send JSON to WebSocket, returning False if the connection is closed.

    Broad on purpose. Which exception a send to a gone client raises depends
    on the server (`RuntimeError` under uvicorn, `anyio.ClosedResourceError`
    under the test client, `WebSocketDisconnect` in between), and the turn
    that calls this must finish and persist whichever one it is.
    """
    try:
        await websocket.send_json(data)
        return True
    except Exception:
        return False


@router.websocket("/{conversation_id}/ws")
async def chat_websocket(websocket: WebSocket, conversation_id: str, token: str | None = None):
    """
    Unified WebSocket endpoint for streaming chat responses.

    Protocol:
    1. Client sends: {"message": "...", "case_file_id": "optional", "rag_config": {...}}
    2. Server streams: {"type": "chunk", "content": "partial text"}
    3. Tool executions: {"type": "tool_executed", "tool": "add_fact", "result": {...}}
    4. Confirmations: {"type": "confirmation_required", "confirmation_id": "...", ...}
    5. Server ends with: {"type": "done", "citations": [...], "chunk_count": N}
    6. On error: {"type": "error", "message": "error description"}

    Client can also send: {"type": "confirm", "confirmation_id": "...", "confirmed": true}
    """
    await websocket.accept()
    logger.info("ws_connected", conversation_id=conversation_id)

    auth_info = await _authenticate(websocket, token)
    if auth_info is None:
        return

    uid = auth_info["uid"]
    user_tier = auth_info["tier"]
    user_db_id = auth_info["user_id"]

    try:
        while True:
            # A turn that finished after its client left has already seen the
            # disconnect (inside `_safe_send`), and Starlette then raises a
            # bare RuntimeError from `receive_text()` rather than
            # WebSocketDisconnect — which used to land in the log as ws_error
            # with a traceback, for the most ordinary thing a phone does.
            # Both flags: a disconnect the client announced sets
            # `client_state`; a send that failed on a vanished client sets
            # `application_state`, and `receive_text` checks that one.
            if WebSocketState.DISCONNECTED in (
                websocket.client_state, websocket.application_state,
            ):
                raise WebSocketDisconnect()
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "code": "bad_request", "message": "მოთხოვნის ფორმატი არასწორია."})
                continue

            if payload.get("type") == "confirm":
                await _handle_confirmation(websocket, payload, uid)
                continue

            user_message = payload.get("message", "")
            if not user_message:
                await websocket.send_json({"type": "error", "code": "empty_message", "message": "შეტყობინება ცარიელია."})
                continue

            case_file_id = payload.get("case_file_id")
            rag_config_data = payload.get("rag_config")
            is_case_chat = payload.get("mode") == "case_intake" or case_file_id is not None

            collections = _parse_rag_config(rag_config_data)

            # Rate Limit check
            from app.config.constants import TIER_RATE_LIMITS, UserTier
            rate_limit_key = f"rate_limit:ws:{uid}"
            try:
                tier_val = UserTier(user_tier if user_tier != "SUPERADMIN" else "ADMIN")
            except ValueError:
                tier_val = UserTier.FREE

            limit = TIER_RATE_LIMITS.get(tier_val, 5)
            allowed, retry_after = await check_redis_rate_limit(rate_limit_key, limit)
            from app.models.database import get_session_factory

            if not allowed:
                message_ka = f"მოთხოვნების ლიმიტი ამოიწურა. გთხოვთ დაელოდოთ {retry_after} წამი."
                # The refusal is part of the conversation like any other
                # outcome: live, the user sees their message and the reason;
                # a reopen used to show neither. Ownership is checked here as
                # it is on the normal path below, since this runs before it.
                async with get_session_factory()() as rdb:
                    refused = ConversationService(rdb)
                    owned = await refused.get_conversation(conversation_id)
                    if owned and (owned.get("user_id") == uid or settings.app_env == "development"):
                        await refused.save_user_message(conversation_id, user_message)
                        await refused.save_error_message(conversation_id, message_ka)
                        await rdb.commit()
                await websocket.send_json({
                    "type": "error",
                    "message": message_ka,
                    "code": "rate_limited"
                })
                continue

            async with get_session_factory()() as db:
                conv_svc = ConversationService(db)

                conv = await conv_svc.get_conversation(conversation_id)
                if not conv:
                    await websocket.send_json({"type": "error", "code": "not_found", "message": "საუბარი ვერ მოიძებნა."})
                    continue
                if conv.get("user_id") != uid and settings.app_env != "development":
                    await websocket.send_json({"type": "error", "code": "forbidden", "message": "ამ საუბარზე წვდომა არ გაქვთ."})
                    continue

                # Credits meter the OPERATOR's spend on the user's behalf.
                # Under no-login / bring-your-own-key there is none: the user
                # pays Google with their own key, and the ceiling is their own
                # quota. The HTTP credit gate already stands down in that mode
                # (credit_gate_middleware.py); this socket must too, or the
                # sixth message of the day is refused for a balance that
                # measures nothing. Admins are never metered either way.
                is_admin = user_tier in ("ADMIN", "SUPERADMIN")
                credits_metered = settings.auth_enabled and not is_admin
                cost = CreditAction.CHAT.cost
                credit_repo = CreditRepository(db)

                if credits_metered:
                    credits_bal = await credit_repo.get_balance(user_db_id)
                    if not credit_repo.has_sufficient_credits(credits_bal, cost):
                        await websocket.send_json({
                            "type": "error",
                            "message": "საკმარისი კრედიტები არ გაქვთ. გთხოვთ ხვალ სცადოთ.",
                            "code": "insufficient_credits"
                        })
                        continue

                history = await conv_svc.get_conversation_history(conversation_id)
                await conv_svc.save_user_message(conversation_id, user_message)
                if not history:
                    await conv_svc.name_after_first_message(
                        conversation_id, conv.get("title"), user_message,
                    )
                # The user's message is a fact the moment it arrives. It used
                # to ride the same transaction as the answer, committed only
                # at the end of the turn: a reload mid-turn showed the
                # conversation without it, and a pipeline failure rolled it
                # back — the message the user typed simply vanished.
                await db.commit()

                # Stage reporting starts BEFORE the guardrail — that call is a
                # model round-trip too, and leaving it unreported meant stage
                # 1 of 10 never fired and the bar began at 2.
                import asyncio as _asyncio

                from app.services.progress_service import (
                    clear_progress_sink,
                    set_progress_sink,
                )

                stage_queue: _asyncio.Queue = _asyncio.Queue()
                set_progress_sink(stage_queue.put_nowait)

                async def pump_stages():
                    while True:
                        frame = await stage_queue.get()
                        if not await _safe_send(websocket, frame):
                            return

                stage_task = _asyncio.create_task(pump_stages())

                start_trace(
                    entry_point="ws_chat",
                    user_message=user_message,
                    user_id=uid,
                    conversation_id=conversation_id,
                )
                record_step(
                    "request_received",
                    message=user_message,
                    case_file_id=case_file_id,
                    case_context_attached=bool(payload.get("case_context")),
                    rag_config=rag_config_data,
                    user_tier=user_tier,
                )

                try:
                    # The turn — guardrail, pipeline, persistence, credits,
                    # trace — is ONE task, shielded from the socket's fate. It
                    # used to be inline, beside a watcher that awaited
                    # `receive_text()` to notice a disconnect and then cancelled
                    # the pipeline: a user who closed the tab, pressed back, or
                    # lost signal for a second lost the answer they had paid
                    # their own key for — and a second message sent mid-turn
                    # was swallowed by the watcher as if it were a disconnect.
                    # The guardrail is inside too: it is a model call that can
                    # take many seconds of provider retries, and while it ran
                    # outside, a client that left in the meantime made the very
                    # first send after it raise — before this task existed, so
                    # the turn never ran at all. The task owns its own session
                    # because the handler's session closes with the handler;
                    # every send inside it goes through `_safe_send`, a no-op
                    # once the client is gone, and the client picks the answer
                    # up from the conversation on its next load.
                    import asyncio

                    async def complete_turn():
                        turn_started(conversation_id)
                        try:
                            await run_turn()
                        except Exception as e:
                            # Handled HERE, in the task, not in the handler
                            # below: when the client is gone the handler may
                            # be gone with it, and the failure still has to be
                            # written into the conversation or the user comes
                            # back to their question and silence.
                            await _fail_turn(websocket, conversation_id, e)
                        finally:
                            turn_finished(conversation_id)

                    async def run_turn():
                        async with get_session_factory()() as tdb:
                            turn_conv = ConversationService(tdb)
                            turn_credits = CreditRepository(tdb)

                            from app.services.guardrail_service import get_guardrail_service
                            guardrail = get_guardrail_service()
                            decision = await guardrail.classify(
                                user_message,
                                in_conversation=bool(history) or is_case_chat,
                            )
                            record_step(
                                "guardrail_decision",
                                category=decision.category,
                                confidence=decision.confidence,
                                should_proceed=decision.should_proceed,
                                canned_response=decision.response_text,
                            )

                            if not decision.should_proceed:
                                response_text = decision.response_text or ""
                                await turn_conv.save_assistant_message(
                                    conversation_id=conversation_id,
                                    content=response_text,
                                    citations=[],
                                    retrieved_chunk_ids=[],
                                    credit_cost=0,
                                )
                                await tdb.commit()
                                await save_current_trace(status="blocked", response_text=response_text)
                                await _safe_send(websocket, {
                                    "type": "done",
                                    "full_response": response_text,
                                    "citations": [],
                                    "chunk_count": 0,
                                    "guardrail_category": decision.category,
                                })
                                return

                            await _safe_send(websocket, {"type": "status", "message": "მოთხოვნის ანალიზი..."})

                            # Determine system prompt based on case state
                            case_file = None
                            if case_file_id:
                                from app.repositories.case_file_repository import CaseFileRepository
                                case_repo = CaseFileRepository(tdb)
                                try:
                                    case_file = await case_repo.get_by_id(_uuid.UUID(case_file_id))
                                except (ValueError, Exception):
                                    pass

                            if case_file:
                                system_prompt_text = compose_advocate_prompt(
                                    case_file=case_file, is_case_chat=is_case_chat
                                )
                            elif is_case_chat:
                                system_prompt_text = CASE_INTAKE_SYSTEM.template
                            else:
                                system_prompt_text = CHAT_SYSTEM.template

                            enriched_message = user_message
                            case_context = payload.get("case_context")
                            if case_context:
                                enriched_message = (
                                    f"[ATTACHED CASE CONTEXT]\n{case_context}\n"
                                    f"[END CASE CONTEXT]\n\n"
                                    f"USER MESSAGE: {user_message}"
                                )

                            pipeline = get_agent_pipeline_service()

                            result = await pipeline.run(
                                user_message=enriched_message,
                                conversation_history=history,
                                system_prompt=system_prompt_text,
                                rag_collections=collections,
                                case_file_id=case_file_id,
                                user_id=uid,
                                conversation_id=conversation_id,
                                db=tdb,
                                is_case_chat=is_case_chat,
                            )

                            response_text = result.response_text
                            chunks = result.chunks
                            verified_citations = result.verified_citations

                            # Detect and strip [CASE_READY] BEFORE sending chunk to client
                            tag_ready = bool(re.search(r'\[CASE_READY\]', response_text))
                            if tag_ready:
                                response_text = re.sub(r'\s*\[CASE_READY\]\s*', '', response_text).rstrip()

                            # Stream the response to client
                            if response_text:
                                await _safe_send(websocket, {"type": "chunk", "content": response_text})

                            # Send tool results to client
                            for tr in result.tool_results:
                                if tr.requires_confirmation:
                                    await _safe_send(websocket, {
                                        "type": "confirmation_required",
                                        "confirmation_id": tr.confirmation_id,
                                        "tool_name": tr.tool_name,
                                        "description": tr.description,
                                     })
                                else:
                                    await _safe_send(websocket, {
                                        "type": "tool_executed",
                                        "tool": tr.tool_name,
                                        "status": tr.status,
                                        "result": tr.result,
                                    })

                            # Handle [CASE_READY]
                            if tag_ready:
                                await turn_conv.mark_case_ready(conversation_id)

                                from app.services.case_builder_service import get_case_builder_service
                                case_builder = get_case_builder_service()
                                try:
                                    await _safe_send(websocket, {"type": "status", "message": "საქმის სრული ანალიზი მიმდინარეობს..."})
                                    if case_file_id:
                                        build_result = await case_builder.update_case_file(
                                            db=tdb,
                                            case_file_id=_uuid.UUID(case_file_id),
                                            conversation_id=conversation_id,
                                            retrieved_chunks=chunks,
                                        )
                                    else:
                                        build_result = await case_builder.build_case_file(
                                            db=tdb,
                                            user_id=uid,
                                            conversation_id=conversation_id,
                                            retrieved_chunks=chunks,
                                        )
                                    if "full_analysis_text" in build_result:
                                        extra = "\n\n" + build_result["full_analysis_text"]
                                        response_text += extra
                                        await _safe_send(websocket, {"type": "chunk", "content": extra})
                                except Exception as e:
                                    logger.error("case_agent_auto_build_failed", error=str(e))
                                    # A failed build must not take the answer
                                    # down with it: a flush error leaves the
                                    # session unusable until it is rolled
                                    # back, and the save below would fail too.
                                    await tdb.rollback()
                                    await turn_conv.mark_case_ready(conversation_id)

                            # Save assistant response
                            chunk_ids = [c.get("chunk_id", "") for c in chunks[:20] if "chunk_id" in c]
                            await turn_conv.save_assistant_message(
                                conversation_id=conversation_id,
                                content=response_text,
                                citations=verified_citations,
                                retrieved_chunk_ids=chunk_ids,
                                credit_cost=cost,
                            )

                            # Update conversation phase
                            msg_count = len(history) + 2
                            next_phase = await turn_conv.determine_next_phase(conversation_id, msg_count)
                            await turn_conv.transition_phase(conversation_id, next_phase)

                            # Deduct credits
                            if credits_metered:
                                await turn_credits.deduct(
                                    user_id=user_db_id,
                                    cost=cost,
                                    action=CreditAction.CHAT.value,
                                    description=f"WS Chat in conversation {conversation_id}"
                                )

                            await tdb.commit()

                            await save_current_trace(status="completed", response_text=response_text)

                            await _safe_send(websocket, {
                                "type": "done",
                                "full_response": response_text,
                                "citations": verified_citations,
                                "chunk_count": len(chunks),
                                "case_analysis_ready": tag_ready,
                                "tool_results": [{
                                    "tool_name": t.tool_name,
                                    "status": t.status,
                                    "result": t.result,
                                } for t in result.tool_results],
                            })

                    try:
                        await asyncio.shield(asyncio.create_task(complete_turn()))
                    finally:
                        # Flush whatever the pump has not drained yet; the
                        # pump itself is retired by the per-message finally.
                        while not stage_queue.empty():
                            await _safe_send(websocket, stage_queue.get_nowait())

                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    # Anything that failed OUTSIDE the turn task (the task
                    # reports its own failures).
                    await _fail_turn(websocket, conversation_id, e)
                finally:
                    # This handler is a LOOP serving many messages. Every exit
                    # path from one message — answered, blocked by the
                    # guardrail, or failed — must retire that message's pump,
                    # or the next one pushes stages into a queue nobody drains.
                    stage_task.cancel()
                    clear_progress_sink()

    except WebSocketDisconnect:
        logger.info("ws_disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("ws_error", error=str(e), exc_info=True)


def _build_gemini_contents(
    history: list[dict[str, str]],
    current_message: str,
) -> list[Any]:
    """Build Gemini-compatible contents from conversation history."""
    raw_messages = []
    for msg in history[-20:]:
        role = "user" if msg["role"] == "user" else "model"
        raw_messages.append({"role": role, "content": msg["content"]})

    raw_messages.append({"role": "user", "content": current_message})

    merged = []
    for msg in raw_messages:
        if not merged:
            merged.append(msg)
        else:
            if merged[-1]["role"] == msg["role"]:
                merged[-1]["content"] += "\n\n" + msg["content"]
            else:
                merged.append(msg)

    if merged and merged[0]["role"] == "model":
        merged.pop(0)

    contents = []
    for msg in merged:
        contents.append(types.Content(
            role=msg["role"],
            parts=[types.Part.from_text(text=msg["content"])],
        ))
    return contents


async def _authenticate(websocket: WebSocket, token: str | None) -> dict[str, Any] | None:
    """Authenticate WebSocket connection. Returns dict with user details or None if failed."""
    api_key = websocket.query_params.get("api_key")
    uid = None
    tier = "FREE"

    # ── No-login mode ─────────────────────────────────────────
    # Checked before the api_key branch below: in this mode the api_key query
    # parameter carries the caller's GOOGLE key (ByokMiddleware has already
    # validated and bound it), not an invite code, so running it through
    # is_valid_api_key would reject every legitimate connection.
    if not settings.auth_enabled:
        from app.utils.anonymous_identity import anonymous_uid

        uid = anonymous_uid(
            websocket.query_params.get("device_id"),
            websocket.client.host if websocket.client else None,
        )
    elif api_key:
        if settings.app_env == "development" and api_key == settings.admin_api_key:
            uid = "admin-api-key"
            tier = "SUPERADMIN"
        else:
            from app.utils.api_keys import is_valid_api_key
            if is_valid_api_key(api_key):
                uid = f"api-user-{api_key[:8]}"
                tier = "FREE"
            else:
                await websocket.send_json({"type": "error", "code": "unauthorized", "message": "წვდომის გასაღები არასწორია."})
                await websocket.close(code=1008)
                return None
    elif token:
        try:
            from app.integrations.firebase_client import verify_id_token
            decoded = verify_id_token(token)
            uid = decoded.get("uid", "anonymous")
        except Exception as e:
            await websocket.send_json({"type": "error", "message": f"Invalid token: {str(e)}"})
            await websocket.close(code=1008)
            return None
    elif settings.app_env == "development":
        uid = "dev-user-001"
        tier = "ADMIN"
    else:
        await websocket.send_json({"type": "error", "code": "unauthorized", "message": "საჭიროა ავტორიზაცია."})
        await websocket.close(code=1008)
        return None

    # Fetch DB user and resolve tier
    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository

    db_factory = get_session_factory()
    async with db_factory() as db:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_firebase_uid(uid)

        if not user:
            if settings.app_env == "development" or not settings.auth_enabled:
                user = await user_repo.create_or_update(
                    firebase_uid=uid,
                    email=None if not settings.auth_enabled else "mock@fuzzzylaw.ge",
                    display_name=None if not settings.auth_enabled else "Mock User",
                )
                await db.commit()
            else:
                await websocket.send_json({"type": "error", "code": "account_uninitialized", "message": "ანგარიში არ არის ინიციალიზებული. გთხოვთ, გაიაროთ ავტორიზაცია თავიდან."})
                await websocket.close(code=1008)
                return None

        if user:
            tier = user.tier

    return {"uid": uid, "tier": tier, "user_id": user.id if user else None}


async def _handle_confirmation(websocket: WebSocket, payload: dict, uid: str) -> None:
    """Handle tool confirmation messages from the client."""
    confirmation_id = payload.get("confirmation_id", "")
    confirmed = payload.get("confirmed", False)

    if not confirmation_id:
        await websocket.send_json({"type": "error", "code": "bad_request", "message": "დადასტურების იდენტიფიკატორი აკლია."})
        return

    from app.models.database import get_session_factory
    async with get_session_factory()() as db:
        executor = CaseToolExecutor(db)
        result = await executor.confirm_pending(
            confirmation_id=confirmation_id,
            user_id=uid,
            confirmed=confirmed,
        )
        await db.commit()

    await websocket.send_json({
        "type": "tool_confirmed",
        "tool_name": result.tool_name,
        "status": result.status,
        "result": result.result,
    })


def _parse_rag_config(rag_config_data: dict | None) -> list[str] | None:
    """Parse optional rag_config from WS message."""
    if not rag_config_data or not isinstance(rag_config_data, dict):
        return None
    from app.schemas.rag_schema import RAGCollectionConfig
    try:
        rag_cfg = RAGCollectionConfig(**rag_config_data)
        return rag_cfg.to_collection_names()
    except Exception:
        return None
