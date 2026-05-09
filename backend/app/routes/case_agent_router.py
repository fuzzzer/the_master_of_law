"""
Case agent router — AI-powered case modification via function calling.

POST /chat/{conversation_id}/agent   — send message in case_agent mode
POST /chat/{conversation_id}/confirm-tool — confirm/reject a destructive action
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import CreditAction
from app.config.settings import settings
from app.models.database import get_db
from app.prompts.chat import CASE_AGENT_SYSTEM
from app.repositories.case_file_repository import CaseFileRepository
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat_schema import (
    ChatSendRequest,
    ChatSendResponse,
    CitationInfo,
    RetrievedChunk,
    ToolConfirmRequest,
    ToolConfirmResponse,
    ToolResultInfo,
)
from app.services.case_tool_executor import CaseToolExecutor, MAX_TOOL_CALLS_PER_MESSAGE
from app.services.citation_service import get_citation_service
from app.services.conversation_service import ConversationService
from app.services.legal_analysis_service import LawContextFormatter
from app.services.rag_retrieval_service import get_rag_service
from app.integrations.vertex_ai_client import get_vertex_ai_client
from app.tools.case_tools import CASE_TOOLS
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["case-agent"])


@router.post("/{conversation_id}/agent", response_model=ChatSendResponse)
async def send_agent_message(
    conversation_id: str,
    body: ChatSendRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message in case_agent mode.

    The AI can call tools to modify case data. Destructive actions
    are deferred for user confirmation.
    """
    if not body.case_file_id:
        return JSONResponse(
            status_code=400,
            content={"error": "case_file_id is required for case_agent mode"},
        )

    conv_svc = ConversationService(db)

    conv = await conv_svc.get_conversation(conversation_id)
    if not conv:
        return JSONResponse(status_code=404, content={"error": "Conversation not found"})

    case_repo = CaseFileRepository(db)
    import uuid as _uuid
    try:
        cf_uuid = _uuid.UUID(body.case_file_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid case_file_id"})

    case_file = await case_repo.get_by_id(cf_uuid)
    if not case_file:
        return JSONResponse(status_code=404, content={"error": "Case file not found"})

    await conv_svc.save_user_message(conversation_id, body.message)

    user_info = getattr(request.state, "user", None)
    uid = user_info.get("uid", "") if user_info else ""

    case_context = _build_case_context(case_file)

    # RAG retrieval — agent has full access to the law corpus
    rag = get_rag_service()
    collections = None
    if body.rag_config:
        from app.schemas.rag_schema import RAGCollectionConfig
        try:
            rag_cfg = RAGCollectionConfig(**body.rag_config.model_dump())
            collections = rag_cfg.to_collection_names()
        except Exception:
            pass

    chunks = await rag.retrieve(body.message, collections=collections)
    law_context = LawContextFormatter.format(chunks)

    full_context = f"{case_context}\n\n{law_context}"
    system_prompt = CASE_AGENT_SYSTEM.render(case_context=full_context)

    history = await conv_svc.get_conversation_history(conversation_id)

    contents = _build_gemini_contents(history, body.message)

    gemini = get_vertex_ai_client()
    tool_executor = CaseToolExecutor(db)
    tool_results: list[ToolResultInfo] = []
    response_text = ""
    tool_call_count = 0

    response = await gemini.generate_with_tools(
        contents=contents,
        tools=CASE_TOOLS,
        system_instruction=system_prompt,
        temperature=CASE_AGENT_SYSTEM.temperature,
        max_output_tokens=CASE_AGENT_SYSTEM.max_output_tokens,
        model_name=settings.gemini_chat_model,
    )

    while tool_call_count < MAX_TOOL_CALLS_PER_MESSAGE:
        function_calls = _extract_function_calls(response)
        text_parts = _extract_text(response)

        if text_parts:
            response_text += text_parts

        if not function_calls:
            break

        tool_call_count += len(function_calls)
        if tool_call_count > MAX_TOOL_CALLS_PER_MESSAGE:
            response_text += "\n\n⚠️ Maximum tool calls per message reached."
            break

        function_response_parts = []
        for fc in function_calls:
            tool_name = fc.name
            tool_args = dict(fc.args) if fc.args else {}

            result = await tool_executor.execute(
                tool_name=tool_name,
                args=tool_args,
                case_file_id=body.case_file_id,
                user_id=uid,
            )
            tool_results.append(ToolResultInfo(**result.to_dict()))

            function_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response=result.to_dict(),
                )
            )

        contents.append(response.candidates[0].content)
        contents.append(types.Content(
            role="user",
            parts=function_response_parts,
        ))

        response = await gemini.generate_with_tools(
            contents=contents,
            tools=CASE_TOOLS,
            system_instruction=system_prompt,
            temperature=CASE_AGENT_SYSTEM.temperature,
            max_output_tokens=CASE_AGENT_SYSTEM.max_output_tokens,
            model_name=settings.gemini_chat_model,
        )

    final_text = _extract_text(response)
    if final_text:
        response_text += final_text

    if not response_text.strip():
        response_text = "Tool operations completed."

    # Citation verification
    citation_svc = get_citation_service()
    raw_citations = citation_svc.extract_citations(response_text)
    verified_citations = citation_svc.verify_citations(raw_citations, chunks)

    chunk_ids = [c.get("chunk_id", "") for c in chunks[:20] if "chunk_id" in c]

    await conv_svc.save_assistant_message(
        conversation_id=conversation_id,
        content=response_text,
        citations=verified_citations,
        retrieved_chunk_ids=chunk_ids,
        credit_cost=CreditAction.CHAT.cost,
    )

    credits_remaining = None
    if user_info:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_firebase_uid(uid)
        if user:
            credit_repo = CreditRepository(db)
            credits = await credit_repo.deduct(
                user_id=user.id,
                cost=CreditAction.CHAT.cost,
                action=CreditAction.CHAT.value,
                description=f"Case agent in conversation {conversation_id}",
            )
            credits_remaining = credit_repo.get_remaining_credits(credits)

    await db.commit()

    logger.info(
        "case_agent_done",
        conversation_id=conversation_id,
        tool_calls=tool_call_count,
        tool_results=len(tool_results),
    )

    return ChatSendResponse(
        response=response_text,
        citations=[
            CitationInfo(
                article_number=c.get("article_number", ""),
                code_name=c.get("code_name", ""),
                raw_text=c.get("raw_text", ""),
                verified=c.get("verified", False),
                article_url=c.get("article_url", ""),
                citation_text=c.get("citation_text", ""),
            )
            for c in verified_citations
        ],
        retrieved_chunks=[
            RetrievedChunk(
                chunk_id=c.get("chunk_id", ""),
                content=c.get("content", "")[:500],
                code_name=c.get("metadata", {}).get("code_name", ""),
                article_number=c.get("metadata", {}).get("article_number", ""),
                article_title=c.get("metadata", {}).get("article_title", ""),
                article_url=c.get("metadata", {}).get("article_url", ""),
            )
            for c in chunks[:10]
        ],
        credits_remaining=credits_remaining,
        tool_results=tool_results,
    )


@router.post("/{conversation_id}/confirm-tool", response_model=ToolConfirmResponse)
async def confirm_tool_action(
    conversation_id: str,
    body: ToolConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Confirm or reject a pending destructive tool action."""
    user_info = getattr(request.state, "user", None)
    uid = user_info.get("uid", "") if user_info else ""

    executor = CaseToolExecutor(db)
    result = await executor.confirm_pending(
        confirmation_id=body.confirmation_id,
        user_id=uid,
        confirmed=body.confirmed,
    )

    await db.commit()

    return ToolConfirmResponse(
        status=result.status,
        tool_name=result.tool_name,
        result=result.result,
    )


def _build_case_context(case_file) -> str:
    """Serialize case file data into a text context block for the system prompt."""
    parts = [f"CASE: {case_file.title} (Status: {case_file.status})"]

    if case_file.facts:
        parts.append(f"\nFACTS: {json.dumps(case_file.facts, ensure_ascii=False, default=str)[:2000]}")
    if case_file.applicable_laws:
        parts.append(f"\nLAWS: {json.dumps(case_file.applicable_laws, ensure_ascii=False, default=str)[:2000]}")
    if case_file.defense_strategies:
        parts.append(f"\nSTRATEGIES: {json.dumps(case_file.defense_strategies, ensure_ascii=False, default=str)[:1000]}")
    if case_file.prosecution_args:
        parts.append(f"\nARGUMENTS: {json.dumps(case_file.prosecution_args, ensure_ascii=False, default=str)[:1000]}")
    if case_file.action_checklist:
        parts.append(f"\nACTION ITEMS: {json.dumps(case_file.action_checklist, ensure_ascii=False, default=str)[:1000]}")
    if case_file.unclear_items:
        parts.append(f"\nRISKS/UNCLEAR: {json.dumps(case_file.unclear_items, ensure_ascii=False, default=str)[:1000]}")

    return "\n".join(parts)


def _build_gemini_contents(
    history: list[dict[str, str]],
    current_message: str,
) -> list[Any]:
    """Build Gemini-compatible contents from conversation history."""
    contents = []
    for msg in history[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg["content"])],
        ))
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=current_message)],
    ))
    return contents


def _extract_function_calls(response) -> list:
    """Extract FunctionCall parts from Gemini response."""
    calls = []
    if not response.candidates:
        return calls
    for part in response.candidates[0].content.parts:
        if part.function_call:
            calls.append(part.function_call)
    return calls


def _extract_text(response) -> str:
    """Extract text parts from Gemini response."""
    if not response.candidates:
        return ""
    texts = []
    for part in response.candidates[0].content.parts:
        if part.text:
            texts.append(part.text)
    return "".join(texts)
