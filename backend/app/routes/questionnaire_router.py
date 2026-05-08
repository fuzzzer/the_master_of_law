"""
Questionnaire router — dynamic intake question API.

Endpoints:
  POST /api/v1/questionnaire/{conversation_id}/generate
  GET  /api/v1/questionnaire/{conversation_id}
  POST /api/v1/questionnaire/{conversation_id}/answer
  POST /api/v1/questionnaire/{conversation_id}/skip

This router is NOT registered in main.py automatically to avoid merge
conflicts with parallel agents.  See REGISTRATION.md for the one-line
diff needed in app/main.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.schemas.questionnaire_schema import (
    QuestionnaireAnswerRequest,
    QuestionnaireAnswerResponse,
    QuestionnaireGenerateResponse,
    QuestionnaireGetResponse,
    QuestionnaireSkipResponse,
)
from app.services.questionnaire_service import get_questionnaire_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/questionnaire", tags=["questionnaire"])


@router.post("/{conversation_id}/generate", response_model=QuestionnaireGenerateResponse)
async def generate_questionnaire(
    conversation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a domain-specific questionnaire for a conversation.

    Triggers Gemini to create tailored questions based on the detected
    legal domain and user's initial description.  Overwrites any
    previously generated questions for this conversation.
    """
    svc = get_questionnaire_service(db)

    # Extract context from request body if provided, otherwise empty
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    context = body.get("context", "") if isinstance(body, dict) else ""
    domain = body.get("domain", "civil") if isinstance(body, dict) else "civil"

    try:
        questions = await svc.generate_questionnaire(
            conversation_id=conversation_id,
            domain=domain,
            context=context,
        )
        await db.commit()
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error("generate_questionnaire_error", error=str(e), conversation_id=conversation_id)
        return JSONResponse(status_code=500, content={"error": "Failed to generate questionnaire"})

    required_count = sum(1 for q in questions if q.get("required", True))
    return QuestionnaireGenerateResponse(
        questions=questions,
        total=len(questions),
        required_count=required_count,
    )


@router.get("/{conversation_id}", response_model=QuestionnaireGetResponse)
async def get_questionnaire(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current questionnaire state for a conversation.

    Returns all questions, existing answers, and progress counters.
    """
    svc = get_questionnaire_service(db)

    try:
        state = await svc.get_questionnaire_state(conversation_id)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return QuestionnaireGetResponse(
        questions=state["questions"],
        answers=state["answers"],
        progress=state["progress"],
    )


@router.post("/{conversation_id}/answer", response_model=QuestionnaireAnswerResponse)
async def answer_question(
    conversation_id: str,
    body: QuestionnaireAnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an answer to a questionnaire question.

    Returns the next unanswered question (if any) and any follow-up
    questions generated based on the answer.
    """
    svc = get_questionnaire_service(db)

    try:
        result = await svc.process_answer(
            conversation_id=conversation_id,
            question_id=body.question_id,
            answer=body.answer,
        )
        await db.commit()
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error("answer_question_error", error=str(e), conversation_id=conversation_id)
        return JSONResponse(status_code=500, content={"error": "Failed to process answer"})

    return QuestionnaireAnswerResponse(
        accepted=result["accepted"],
        next_question=result.get("next_question"),
        follow_ups=result.get("follow_ups", []),
        progress=result["progress"],
    )


@router.post("/{conversation_id}/skip", response_model=QuestionnaireSkipResponse)
async def skip_question(
    conversation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Skip a non-required questionnaire question.

    Body: {"question_id": "..."}
    """
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    question_id = body.get("question_id", "") if isinstance(body, dict) else ""

    if not question_id:
        return JSONResponse(status_code=400, content={"error": "question_id is required"})

    svc = get_questionnaire_service(db)

    try:
        result = await svc.skip_question(
            conversation_id=conversation_id,
            question_id=question_id,
        )
        await db.commit()
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error("skip_question_error", error=str(e), conversation_id=conversation_id)
        return JSONResponse(status_code=500, content={"error": "Failed to skip question"})

    return QuestionnaireSkipResponse(
        skipped_count=result["skipped_count"],
        ready_for_analysis=result["ready_for_analysis"],
    )
