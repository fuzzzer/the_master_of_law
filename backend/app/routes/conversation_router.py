"""
Conversation router — CRUD for conversations.

Starting a conversation costs 0 credits.
Now wired to PostgreSQL via ConversationService.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.conversation_schema import (
    ConversationCreate,
    ConversationDetail,
    ConversationListResponse,
    ConversationSummary,
)
from app.services.conversation_service import ConversationService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.post("", response_model=ConversationSummary, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Start a new conversation (costs 0 credits)."""
    user = getattr(request.state, "user", {})
    uid = user.get("uid", "anonymous")

    svc = ConversationService(db)
    conv = await svc.create_conversation(user_id=uid, title=body.title)
    await db.commit()

    logger.info("conversation_created", id=conv["id"], user_id=uid)
    return ConversationSummary(
        id=conv["id"],
        title=conv["title"],
        phase=conv["phase"],
        legal_domain=conv.get("legal_domain", ""),
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List user's conversations."""
    user = getattr(request.state, "user", {})
    uid = user.get("uid", "anonymous")

    svc = ConversationService(db)
    convs, total = await svc.list_conversations(user_id=uid)

    return ConversationListResponse(
        conversations=[
            ConversationSummary(
                id=c["id"],
                title=c["title"],
                phase=c["phase"],
                legal_domain=c.get("legal_domain", ""),
                created_at=c.get("created_at", ""),
                updated_at=c.get("updated_at", ""),
            )
            for c in convs
        ],
        total=total,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get conversation with messages."""
    svc = ConversationService(db)
    conv = await svc.get_conversation(conversation_id)

    if not conv:
        return JSONResponse(status_code=404, content={"error": "Conversation not found"})

    return ConversationDetail(
        id=conv["id"],
        title=conv["title"],
        phase=conv["phase"],
        legal_domain=conv.get("legal_domain", ""),
        case_ready=conv.get("case_ready", False),
        messages=conv.get("messages", []),
        created_at=conv.get("created_at", ""),
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and its messages."""
    svc = ConversationService(db)
    deleted = await svc.delete_conversation(conversation_id)
    await db.commit()

    if deleted:
        logger.info("conversation_deleted", id=conversation_id)
    return None
