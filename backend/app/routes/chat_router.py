"""
Chat router — POST /chat/{conversation_id}/send (costs 1 credit).

Runs the full pipeline: RAG retrieval -> Legal Analysis -> Citation Verification.
Now persists messages to PostgreSQL and deducts credits after success.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import CreditAction
from app.models.database import get_db
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat_schema import (
    ChatSendRequest,
    ChatSendResponse,
    CitationInfo,
    RetrievedChunk,
)
from app.services.citation_service import get_citation_service
from app.services.conversation_service import ConversationService
from app.services.legal_analysis_service import get_legal_analysis_service
from app.services.rag_retrieval_service import get_rag_service
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

    # Get conversation history from DB for multi-turn context
    history = await conv_svc.get_conversation_history(conversation_id)

    # Step 1: RAG Retrieval
    rag = get_rag_service()
    collections = body.rag_config.to_collection_names() if body.rag_config else None
    chunks = await rag.retrieve(body.message, collections=collections)

    # Step 2: Legal Analysis
    analysis = get_legal_analysis_service()
    response_text = await analysis.analyze(
        user_message=body.message,
        retrieved_chunks=chunks,
        conversation_history=history if history else None,
    )

    # Step 3: Citation Verification
    citation_svc = get_citation_service()
    raw_citations = citation_svc.extract_citations(response_text)
    verified_citations = citation_svc.verify_citations(raw_citations, chunks)

    # Build response models
    citation_models = [CitationInfo(**c) for c in verified_citations]

    chunk_models = []
    chunk_ids = []
    for c in chunks[:20]:  # Return top-20 chunks to client
        meta = c.get("metadata", {})
        chunk_id = c.get("chunk_id", "")
        chunk_ids.append(chunk_id)
        chunk_models.append(RetrievedChunk(
            chunk_id=chunk_id,
            content=c.get("content", "")[:500],  # Truncate for response size
            code_name=meta.get("code_name", ""),
            article_number=meta.get("article_number", ""),
            article_title=meta.get("article_title", ""),
            citation_text=meta.get("citation_text", ""),
            article_url=meta.get("article_url", ""),
            distance=c.get("distance", 0.0),
        ))

    # Save assistant response to DB
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
    )
