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
from app.services.case_tool_executor import CaseToolExecutor, MAX_TOOL_CALLS_PER_MESSAGE
from app.services.citation_service import get_citation_service
from app.services.conversation_service import ConversationService
from app.services.legal_analysis_service import (
    LawContextFormatter,
    get_legal_analysis_service,
)
from app.services.rag_retrieval_service import get_rag_service
from app.integrations.vertex_ai_client import get_vertex_ai_client
from app.tools.case_tools import CASE_TOOLS
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-ws"])


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

                    await websocket.send_json({"type": "status", "message": "Searching laws..."})

                    rag = get_rag_service()
                    chunks = await rag.retrieve(user_message, collections=collections)

                    await websocket.send_json({
                        "type": "status",
                        "message": f"Found {len(chunks)} relevant articles. Analyzing..."
                    })

                    case_file = None
                    if case_file_id:
                        from app.repositories.case_file_repository import CaseFileRepository
                        case_repo = CaseFileRepository(db)
                        try:
                            case_file = await case_repo.get_by_id(_uuid.UUID(case_file_id))
                        except (ValueError, Exception):
                            pass

                    is_case_empty = False
                    if case_file:
                        is_case_empty = not case_file.facts and not case_file.applicable_laws and not case_file.defense_strategies

                    if case_file and not is_case_empty:
                        response_text, tool_results = await _handle_advocate_with_tools(
                            websocket=websocket,
                            user_message=user_message,
                            history=history,
                            chunks=chunks,
                            case_file=case_file,
                            case_file_id=case_file_id,
                            uid=uid,
                            db=db,
                            is_case_chat=is_case_chat,
                        )
                    else:
                        response_text = await _handle_standard_chat(
                            websocket=websocket,
                            user_message=user_message,
                            history=history,
                            chunks=chunks,
                            conv=conv,
                            uid=uid,
                            is_case_chat=is_case_chat,
                            case_context=payload.get("case_context"),
                        )
                        tool_results = []

                    tag_ready = bool(re.search(r'\[CASE_READY\]', response_text))
                    if tag_ready:
                        response_text = re.sub(r'\s*\[CASE_READY\]\s*', '', response_text).rstrip()
                        await conv_svc.mark_case_ready(conversation_id)
                        
                        from app.services.case_builder_service import get_case_builder_service
                        case_builder = get_case_builder_service()
                        try:
                            await websocket.send_json({"type": "status", "message": "საქმის სრული ანალიზი მიმდინარეობს..."})
                            
                            if case_file_id:
                                result = await case_builder.update_case_file(
                                    db=db,
                                    case_file_id=_uuid.UUID(case_file_id),
                                    conversation_id=conversation_id,
                                    retrieved_chunks=chunks,
                                )
                            else:
                                result = await case_builder.build_case_file(
                                    db=db,
                                    user_id=uid,
                                    conversation_id=conversation_id,
                                    retrieved_chunks=chunks,
                                )
                                
                            if "full_analysis_text" in result:
                                extra = "\n\n" + result["full_analysis_text"]
                                response_text += extra
                                await websocket.send_json({"type": "chunk", "content": extra})
                        except Exception as e:
                            logger.error("case_agent_auto_build_failed", error=str(e))

                    # Citation verification
                    citation_svc = get_citation_service()
                    raw_citations = citation_svc.extract_citations(response_text)
                    verified_citations = citation_svc.verify_citations(raw_citations, chunks)

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

                    await websocket.send_json({
                        "type": "done",
                        "full_response": response_text,
                        "citations": verified_citations,
                        "chunk_count": len(chunks),
                        "case_analysis_ready": tag_ready,
                        "tool_results": [t.to_dict() for t in tool_results] if tool_results else [],
                    })

                except Exception as e:
                    logger.error("ws_processing_error", error=str(e), exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": "An error occurred during analysis. Please try again.",
                    })

    except WebSocketDisconnect:
        logger.info("ws_disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("ws_error", error=str(e), exc_info=True)


async def _handle_advocate_with_tools(
    websocket: WebSocket,
    user_message: str,
    history: list[dict[str, str]],
    chunks: list[dict[str, Any]],
    case_file: Any,
    case_file_id: str,
    uid: str,
    db: Any,
    is_case_chat: bool,
) -> tuple[str, list]:
    """Handle chat with case tools — unified advocate flow.

    Streams text to the client while also executing function calls.
    Returns (response_text, tool_results).
    """
    from app.services.case_tool_executor import ToolResult as ToolResultObj

    system_prompt = compose_advocate_prompt(case_file=case_file, is_case_chat=is_case_chat)

    # Append source-specific RAG instructions
    analysis_svc = get_legal_analysis_service()
    system_prompt = analysis_svc._build_system_prompt(chunks, type('P', (), {'template': system_prompt})())

    law_context = LawContextFormatter.format(chunks)

    if law_context and law_context != "No relevant legal context was found.":
        system_prompt = system_prompt + f"\n\nRETRIEVED LAW ARTICLES:\n{law_context}"

    contents = _build_gemini_contents(history, user_message)

    gemini = get_vertex_ai_client()
    tool_executor = CaseToolExecutor(db)
    tool_results = []
    response_text = ""
    tool_call_count = 0

    # First pass: stream text + collect function calls
    async for event in gemini.generate_stream_with_tools(
        contents=contents,
        tools=CASE_TOOLS,
        system_instruction=system_prompt,
        temperature=0.5,
        max_output_tokens=10000,
        model_name=settings.gemini_chat_model,
    ):
        if "text" in event:
            response_text += event["text"]
            await websocket.send_json({"type": "chunk", "content": event["text"]})
        elif "function_call" in event:
            fc = event["function_call"]
            tool_name = fc.name
            tool_args = dict(fc.args) if fc.args else {}
            tool_call_count += 1

            if tool_call_count > MAX_TOOL_CALLS_PER_MESSAGE:
                break

            result = await tool_executor.execute(
                tool_name=tool_name,
                args=tool_args,
                case_file_id=case_file_id,
                user_id=uid,
            )
            tool_results.append(result)

            if result.requires_confirmation:
                await websocket.send_json({
                    "type": "confirmation_required",
                    "confirmation_id": result.confirmation_id,
                    "tool_name": result.tool_name,
                    "description": result.description,
                })
            else:
                await websocket.send_json({
                    "type": "tool_executed",
                    "tool": tool_name,
                    "status": result.status,
                    "result": result.result,
                })

    if tool_results and any(not r.requires_confirmation for r in tool_results):
        executed_summaries = []
        for r in tool_results:
            if not r.requires_confirmation:
                executed_summaries.append(f"{r.tool_name}: {r.status} — {json.dumps(r.result, ensure_ascii=False, default=str)[:200]}")

        if executed_summaries:
            tool_note = "\n\n📌 " + " | ".join(
                _tool_summary_ka(r.tool_name, r.result)
                for r in tool_results
                if not r.requires_confirmation and r.status == "executed"
            )
            if tool_note.strip() != "📌":
                response_text += tool_note
                await websocket.send_json({"type": "chunk", "content": tool_note})

    from app.config.constants import LEGAL_DISCLAIMER_KA
    disclaimer = f"\n\n---\n⚠️ {LEGAL_DISCLAIMER_KA}"
    response_text += disclaimer
    await websocket.send_json({"type": "chunk", "content": disclaimer})

    return response_text, tool_results


async def _handle_standard_chat(
    websocket: WebSocket,
    user_message: str,
    history: list[dict[str, str]],
    chunks: list[dict[str, Any]],
    conv: dict[str, Any],
    uid: str,
    is_case_chat: bool,
    case_context: str | None,
) -> str:
    """Handle standard chat with the search_law tool available."""
    from app.tools.case_tools import SEARCH_LAW_TOOL
    from google.genai import types as gtypes

    system_prompt = CASE_INTAKE_SYSTEM if is_case_chat else CHAT_SYSTEM

    analysis_svc = get_legal_analysis_service()
    system_prompt_text = analysis_svc._build_system_prompt(chunks, system_prompt)
    law_context = LawContextFormatter.format(chunks)

    if law_context and law_context != "No relevant legal context was found.":
        system_prompt_text += f"\n\nRETRIEVED LAW ARTICLES:\n{law_context}"

    if case_context:
        system_prompt_text += f"\n\nCURRENT CASE CONTEXT:\n{case_context}"

    contents = _build_gemini_contents(history, user_message)

    gemini = get_vertex_ai_client()
    rag_svc = get_rag_service()
    response_text = ""
    search_call_count = 0
    MAX_SEARCH_CALLS = 2  

    while True:
        async for event in gemini.generate_stream_with_tools(
            contents=contents,
            tools=[SEARCH_LAW_TOOL],
            system_instruction=system_prompt_text,
            temperature=system_prompt.temperature,
            max_output_tokens=system_prompt.max_output_tokens,
            model_name=settings.gemini_chat_model,
        ):
            if "text" in event:
                response_text += event["text"]
                await websocket.send_json({"type": "chunk", "content": event["text"]})
            elif "function_call" in event and search_call_count < MAX_SEARCH_CALLS:
                fc = event["function_call"]
                if fc.name == "search_law":
                    search_call_count += 1
                    args = dict(fc.args) if fc.args else {}
                    query = args.get("query", user_message)
                    article_number = args.get("article_number")
                    code_name = args.get("code_name")

                    await websocket.send_json({
                        "type": "status",
                        "message": f"🔍 კანონის ბაზის შემოწმება: {article_number or query[:40]}...",
                    })

                    found_chunks = await rag_svc.search_law(
                        query=query,
                        article_number=article_number,
                        code_name=code_name,
                    )

                    if found_chunks:
                        result_text = LawContextFormatter.format(found_chunks)
                    else:
                        result_text = "No matching law articles found in database."

                    contents.append(gtypes.Content(
                        role="model",
                        parts=[gtypes.Part(function_call=fc)],
                    ))
                    contents.append(gtypes.Content(
                        role="user",
                        parts=[gtypes.Part(
                            function_response=gtypes.FunctionResponse(
                                name="search_law",
                                response={"result": result_text},
                            )
                        )],
                    ))
                    break
        else:
            break

    return response_text



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


def _tool_summary_ka(tool_name: str, result: dict) -> str:
    summaries = {
        "add_fact": lambda r: f"ფაქტი დამატებულია: {r.get('text', '')[:50]}",
        "edit_fact": lambda r: f"ფაქტი განახლდა: {r.get('fact_id', '')}",
        "add_argument": lambda r: f"არგუმენტი დამატებულია: {r.get('title', '')[:50]}",
        "link_article": lambda r: f"მუხლი მიბმულია: {r.get('code_name', '')} {r.get('article_number', '')}",
        "set_strategy": lambda r: f"სტრატეგია დაყენებულია: {r.get('strategy', '')[:50]}",
        "add_action_item": lambda r: f"დავალება დამატებულია: {r.get('task', '')[:50]}",
        "complete_action_item": lambda r: f"დავალება შესრულდა",
        "add_risk": lambda r: f"რისკი დამატებულია: {r.get('description', '')[:50]}",
        "get_case_summary": lambda r: "საქმის მიმოხილვა",
    }
    builder = summaries.get(tool_name)
    return builder(result) if builder else f"{tool_name} შესრულდა"


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
