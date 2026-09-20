"""
Questionnaire router — 4 endpoints for the dynamic pre-analysis questionnaire.

All endpoints cost 0 credits (questionnaire is part of intake, not paid analysis).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.questionnaire_schema import (
    AnswerRequest,
    AnswerResponse,
    ExtractRequest,
    ExtractResponse,
    GenerateRequest,
    GenerateResponse,
    QuestionnaireStateResponse,
    SkipResponse,
)
from app.services.questionnaire_service import QuestionnaireService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/questionnaire", tags=["questionnaire"])


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None


@router.post("/{conversation_id}/generate", response_model=GenerateResponse)
async def generate_questionnaire(
    conversation_id: str,
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a dynamic questionnaire based on legal domain and user description."""
    conv_uuid = _parse_uuid(conversation_id)
    if not conv_uuid:
        return JSONResponse(status_code=400, content={"error": "Invalid conversation ID"})

    svc = QuestionnaireService(db)
    try:
        result = await svc.generate_questionnaire(
            conversation_id=conv_uuid,
            domain=body.domain,
            user_description=body.user_description,
        )
    except Exception as e:
        logger.error("questionnaire_generate_failed", error=str(e))
        return JSONResponse(status_code=500, content={"error": "Failed to generate questionnaire"})

    await db.commit()
    return GenerateResponse(**result)


@router.get("/{conversation_id}", response_model=QuestionnaireStateResponse)
async def get_questionnaire(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the current questionnaire state — questions, answers, and progress."""
    conv_uuid = _parse_uuid(conversation_id)
    if not conv_uuid:
        return JSONResponse(status_code=400, content={"error": "Invalid conversation ID"})

    svc = QuestionnaireService(db)
    result = await svc.get_questionnaire(conv_uuid)
    return QuestionnaireStateResponse(**result)


@router.post("/{conversation_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    conversation_id: str,
    body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit an answer to a questionnaire question."""
    conv_uuid = _parse_uuid(conversation_id)
    if not conv_uuid:
        return JSONResponse(status_code=400, content={"error": "Invalid conversation ID"})

    svc = QuestionnaireService(db)
    result = await svc.process_answer(
        conversation_id=conv_uuid,
        question_id=body.question_id,
        answer_value=body.answer,
    )

    if not result.get("accepted"):
        return JSONResponse(status_code=404, content={"error": result.get("error", "Question not found")})

    await db.commit()
    return AnswerResponse(**result)


@router.post("/{conversation_id}/skip", response_model=SkipResponse)
async def skip_remaining(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Skip all remaining optional questions and mark questionnaire as ready."""
    conv_uuid = _parse_uuid(conversation_id)
    if not conv_uuid:
        return JSONResponse(status_code=400, content={"error": "Invalid conversation ID"})

    svc = QuestionnaireService(db)
    result = await svc.skip_remaining(conv_uuid)

    await db.commit()
    return SkipResponse(**result)


@router.post("/{conversation_id}/extract", response_model=ExtractResponse)
async def extract_from_narrative(
    conversation_id: str,
    body: ExtractRequest,
    db: AsyncSession = Depends(get_db),
):
    """Extract structured answers from a free-text narrative using AI."""
    conv_uuid = _parse_uuid(conversation_id)
    if not conv_uuid:
        return JSONResponse(status_code=400, content={"error": "Invalid conversation ID"})

    svc = QuestionnaireService(db)
    try:
        result = await svc.extract_from_narrative(
            conversation_id=conv_uuid,
            domain=body.domain,
            narrative=body.narrative,
        )
    except Exception as e:
        logger.error("narrative_extract_failed", error=str(e))
        return JSONResponse(status_code=500, content={"error": "Failed to extract from narrative"})

    await db.commit()
    return ExtractResponse(**result)
