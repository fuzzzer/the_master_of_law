"""
Chat router — POST /chat/{conversation_id}/send (costs 1 credit).

Runs the full pipeline: RAG retrieval -> Legal Analysis -> Citation Verification.
Now persists messages to PostgreSQL and deducts credits after success.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import CreditAction
from app.config.settings import settings
from app.models.database import get_db
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat_schema import (
    ChatSendRequest,
    ChatSendResponse,
    CitationInfo,
    RetrievedChunk,
)
from app.prompts.chat import CASE_INTAKE_SYSTEM, CHAT_SYSTEM
from app.services.agent_pipeline_service import get_agent_pipeline_service
from app.services.conversation_service import ConversationService
from app.services.guardrail_service import get_guardrail_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/{conversation_id}/send", response_model=ChatSendResponse)
async def send_message(
    conversation_id: str,
    body: ChatSendRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and get an AI legal analysis response.

    Pipeline:
    1. Persist user message to DB
    2. RAG retrieval (5-stage) to find relevant law articles
    3. Gemini legal analysis with retrieved context
    4. Citation extraction and verification
    5. Persist assistant response to DB
    6. Deduct credits after successful response
    """
    logger.info(
        "chat_send_start",
        conversation_id=conversation_id,
        message_length=len(body.message),
    )

    conv_svc = ConversationService(db)

    # Verify conversation exists
    conv = await conv_svc.get_conversation(conversation_id)
    if not conv:
        return JSONResponse(
            status_code=404,
            content={"error": "Conversation not found"},
        )

    # Save user message to DB
    await conv_svc.save_user_message(conversation_id, body.message)

    # Auto-generate title from first user message if conversation has no title
    if not conv.get("title"):
        title_preview = body.message[:60].strip()
        if len(body.message) > 60:
            title_preview += '...'
        await conv_svc.update_title(conversation_id, title_preview)

    # Step 0: Guardrail — classify before RAG
    user_info = getattr(request.state, "user", None)
    user_tier = user_info.get("tier", "FREE") if user_info else "FREE"
    guardrail = get_guardrail_service()
    decision = await guardrail.classify(body.message, user_tier=user_tier)

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
        logger.info(
            "chat_guardrail_blocked",
            conversation_id=conversation_id,
            category=decision.category,
        )
        return ChatSendResponse(
            response=response_text,
            citations=[],
            retrieved_chunks=[],
            credits_remaining=None,
        )

    # Get conversation history from DB for multi-turn context
    history = await conv_svc.get_conversation_history(conversation_id)
    msg_count = len(history) if history else 0

    # Select system prompt based on mode
    system_prompt = CASE_INTAKE_SYSTEM if body.mode == "case_intake" else CHAT_SYSTEM

    # Enrich user message with case context if a case is attached
    enriched_message = body.message
    if body.case_context:
        enriched_message = (
            f"[ATTACHED CASE CONTEXT]\n{body.case_context}\n"
            f"[END CASE CONTEXT]\n\n"
            f"USER MESSAGE: {body.message}"
        )

    # Step 1-3: Agent Pipeline (Plan → RAG → Analyze → Verify)
    collections = body.rag_config.to_collection_names() if body.rag_config else None
    pipeline = get_agent_pipeline_service()
    result = await pipeline.run(
        user_message=enriched_message,
        conversation_history=history,
        system_prompt=system_prompt.template if hasattr(system_prompt, 'template') else str(system_prompt),
        rag_collections=collections,
        is_case_chat=body.mode == "case_intake",
        db=db,
    )
    response_text = result.response_text
    chunks = result.chunks
    verified_citations = result.verified_citations

    citation_models = [CitationInfo(**c) for c in verified_citations]

    chunk_models = []
    chunk_ids = []
    for c in chunks[:20]:  # Return top-20 chunks to client
        meta = c.get("metadata", {})
        chunk_id = c.get("chunk_id", "")
        chunk_ids.append(chunk_id)
        chunk_models.append(RetrievedChunk(
            chunk_id=chunk_id,
            content=c.get("content", "")[:500],
            code_name=meta.get("code_name", ""),
            article_number=meta.get("article_number", ""),
            article_title=meta.get("article_title", ""),
            citation_text=meta.get("citation_text", ""),
            article_url=meta.get("article_url", ""),
            distance=c.get("distance", 0.0),
        ))

    # Strip machine-readable tag before saving/returning
    tag_ready = bool(re.search(r'\[CASE_READY\]', response_text))
    if tag_ready:
        response_text = re.sub(r'\s*\[CASE_READY\]\s*', '', response_text).rstrip()

    # Save assistant response to DB (clean, without tag)
    credit_cost = CreditAction.CHAT.cost
    await conv_svc.save_assistant_message(
        conversation_id=conversation_id,
        content=response_text,
        citations=[c.model_dump() for c in citation_models],
        retrieved_chunk_ids=chunk_ids,
        credit_cost=credit_cost,
    )

    # Update conversation phase based on message count
    msg_count = len(history) + 2  # +2 for the new user + assistant messages
    next_phase = await conv_svc.determine_next_phase(conversation_id, msg_count)
    await conv_svc.transition_phase(conversation_id, next_phase)

    # Deduct credits AFTER successful response
    credits_remaining = None
    user_info = getattr(request.state, "user", None)
    if user_info:
        uid = user_info.get("uid", "")
        user_repo = UserRepository(db)
        user = await user_repo.get_by_firebase_uid(uid)
        if user:
            credit_repo = CreditRepository(db)
            credits = await credit_repo.deduct(
                user_id=user.id,
                cost=credit_cost,
                action=CreditAction.CHAT.value,
                description=f"Chat in conversation {conversation_id}",
            )
            credits_remaining = credit_repo.get_remaining_credits(credits)

    # Detect readiness before committing
    intake_history_ready = (
        body.mode == "case_intake"
        and msg_count >= 6
        and not any(q in response_text for q in ["?", "კითხვა", "დამაზუსტებელი"])
    )
    case_analysis_ready = tag_ready or intake_history_ready

    # Suggest questionnaire if we have some context but aren't ready yet
    suggest_questionnaire = (
        body.mode == "case_intake"
        and msg_count >= 2
        and not case_analysis_ready
    )

    # Persist readiness on the conversation so it survives page refresh
    if case_analysis_ready:
        await conv_svc.mark_case_ready(conversation_id)

    await db.commit()

    logger.info(
        "chat_send_done",
        conversation_id=conversation_id,
        response_length=len(response_text),
        citations=len(citation_models),
        chunks=len(chunk_models),
        credits_remaining=credits_remaining,
    )

    return ChatSendResponse(
        response=response_text,
        citations=citation_models,
        retrieved_chunks=chunk_models,
        credits_remaining=credits_remaining,
        case_analysis_ready=case_analysis_ready,
        suggest_questionnaire=suggest_questionnaire,
    )

