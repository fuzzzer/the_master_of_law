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
from google.genai import types

from app.config.settings import settings
from app.prompts.advocate import compose_advocate_prompt
from app.prompts.chat import CHAT_SYSTEM, CASE_INTAKE_SYSTEM
from app.services.agent_pipeline_service import get_agent_pipeline_service
from app.services.case_tool_executor import CaseToolExecutor
from app.services.conversation_service import ConversationService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-ws"])


async def _safe_send(websocket: WebSocket, data: dict) -> bool:
    """Send JSON to WebSocket, returning False if the connection is closed."""
    try:
        await websocket.send_json(data)
        return True
    except (RuntimeError, WebSocketDisconnect):
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

    uid = await _authenticate(websocket, token)
    if uid is None:
        return

    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            if payload.get("type") == "confirm":
                await _handle_confirmation(websocket, payload, uid)
                continue

            user_message = payload.get("message", "")
            if not user_message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            case_file_id = payload.get("case_file_id")
            rag_config_data = payload.get("rag_config")
            # Legacy support: accept 'mode' for backward compat but ignore it
            is_case_chat = payload.get("mode") == "case_intake" or case_file_id is not None

            collections = _parse_rag_config(rag_config_data)

            from app.models.database import get_session_factory
            async with get_session_factory()() as db:
                conv_svc = ConversationService(db)

                conv = await conv_svc.get_conversation(conversation_id)
                if not conv:
                    await websocket.send_json({"type": "error", "message": "Conversation not found"})
                    continue
                if conv.get("user_id") != uid and settings.app_env != "development":
                    await websocket.send_json({"type": "error", "message": "Unauthorized access to conversation"})
                    continue

                history = await conv_svc.get_conversation_history(conversation_id)
                await conv_svc.save_user_message(conversation_id, user_message)

                await websocket.send_json({"type": "status", "message": "Checking query..."})

                try:
                    from app.services.guardrail_service import get_guardrail_service
                    guardrail = get_guardrail_service()
                    decision = await guardrail.classify(user_message)

                    if not decision.should_proceed:
                        response_text = decision.response_text or ""
                        await conv_svc.save_assistant_message(
                            conversation_id=conversation_id,
                            content=response_text,
                            citations=[],
                            retrieved_chunk_ids=[],
                            credit_cost=0,
                        )
                        await db.commit()
                        await websocket.send_json({
                            "type": "done",
                            "full_response": response_text,
                            "citations": [],
                            "chunk_count": 0,
                            "guardrail_category": decision.category,
                        })
                        continue

                    await websocket.send_json({"type": "status", "message": "მოთხოვნის ანალიზი..."})

                    # Determine system prompt based on case state
                    case_file = None
                    if case_file_id:
                        from app.repositories.case_file_repository import CaseFileRepository
                        case_repo = CaseFileRepository(db)
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
                        db=db,
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

                    # Handle [CASE_READY] — tag already stripped above
                    if tag_ready:
                        await conv_svc.mark_case_ready(conversation_id)

                        from app.services.case_builder_service import get_case_builder_service
                        case_builder = get_case_builder_service()
                        try:
                            await _safe_send(websocket, {"type": "status", "message": "საქმის სრული ანალიზი მიმდინარეობს..."})
                            if case_file_id:
                                build_result = await case_builder.update_case_file(
                                    db=db,
                                    case_file_id=_uuid.UUID(case_file_id),
                                    conversation_id=conversation_id,
                                    retrieved_chunks=chunks,
                                )
                            else:
                                build_result = await case_builder.build_case_file(
                                    db=db,
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

                    # Save assistant response
                    chunk_ids = [c.get("chunk_id", "") for c in chunks[:20] if "chunk_id" in c]
                    await conv_svc.save_assistant_message(
                        conversation_id=conversation_id,
                        content=response_text,
                        citations=verified_citations,
                        retrieved_chunk_ids=chunk_ids,
                        credit_cost=1,
                    )

                    # Update conversation phase
                    msg_count = len(history) + 2
                    next_phase = await conv_svc.determine_next_phase(conversation_id, msg_count)
                    await conv_svc.transition_phase(conversation_id, next_phase)

                    await db.commit()

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

                except Exception as e:
                    logger.error("ws_processing_error", error=str(e), exc_info=True)
                    await _safe_send(websocket, {
                        "type": "error",
                        "message": "An error occurred during analysis. Please try again.",
                    })

    except WebSocketDisconnect:
        logger.info("ws_disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("ws_error", error=str(e), exc_info=True)

# ── Removed: _handle_advocate_with_tools and _handle_standard_chat ──
# Both replaced by AgentPipelineService.run() in the main WS handler.


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


async def _authenticate(websocket: WebSocket, token: str | None) -> str | None:
    """Authenticate WebSocket connection. Returns uid or None if failed."""
    api_key = websocket.query_params.get("api_key")
    if api_key:
        if api_key == settings.admin_api_key:
            return "admin-api-key"
        from app.utils.api_keys import is_valid_api_key
        if is_valid_api_key(api_key):
            return f"api-user-{api_key[:8]}"
        await websocket.send_json({"type": "error", "message": "Invalid API key"})
        await websocket.close(code=1008)
        return None
    elif token:
        try:
            from app.integrations.firebase_client import verify_id_token
            decoded = verify_id_token(token)
            return decoded.get("uid", "anonymous")
        except Exception as e:
            await websocket.send_json({"type": "error", "message": f"Invalid token: {str(e)}"})
            await websocket.close(code=1008)
            return None
    elif settings.app_env == "development":
        return "dev-user-001"
    else:
        await websocket.send_json({"type": "error", "message": "Authentication required"})
        await websocket.close(code=1008)
        return None


async def _handle_confirmation(websocket: WebSocket, payload: dict, uid: str) -> None:
    """Handle tool confirmation messages from the client."""
    confirmation_id = payload.get("confirmation_id", "")
    confirmed = payload.get("confirmed", False)

    if not confirmation_id:
        await websocket.send_json({"type": "error", "message": "Missing confirmation_id"})
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
