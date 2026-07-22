"""
Case file router — build, view, update, and delete defense case files.

Building costs 3 credits. Updating costs 1 credit.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import CreditAction
from app.models.database import get_db
from app.repositories.case_file_repository import CaseFileRepository
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.case_file_schema import (
    CaseFileBuildRequest,
    CaseFileDetail,
    CaseFileListResponse,
    CaseFileSummary,
    CaseFileUpdateRequest,
    DocumentGenerationRequest,
    DocumentGenerationResponse,
)
from app.services.case_builder_service import get_case_builder_service
from app.services.document_generator_service import get_document_generator_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/case-files", tags=["case-files"])


@router.post("/build", response_model=CaseFileDetail, status_code=201)
async def build_case_file(
    body: CaseFileBuildRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Build a defense case file from a conversation (costs 3 credits)."""
    user_info = getattr(request.state, "user", None)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    uid = user_info.get("uid", "")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_firebase_uid(uid)

    if not user:

        user = await user_repo.create_or_update(
            firebase_uid=uid,
            email=user_info.get("email"),
            display_name=user_info.get("name"),
            photo_url=user_info.get("picture"),
        )
        await db.commit()

    cost = CreditAction.CASE_FILE.cost
    is_admin = user_info.get("tier") in ("ADMIN", "SUPERADMIN")

    if user and not is_admin:
        credit_repo = CreditRepository(db)
        credits = await credit_repo.get_balance(user.id)
        if not credit_repo.has_sufficient_credits(credits, cost):
            return JSONResponse(
                status_code=402,
                content={
                    "error": "insufficient_credits",
                    "message": "Not enough credits to build a case file (requires 3 credits)",
                    "credits_remaining": credit_repo.get_remaining_credits(credits),
                },
            )

    # Build the case file
    try:
        svc = get_case_builder_service()
        result = await svc.build_case_file(
            db=db,
            user_id=uid,
            conversation_id=body.conversation_id,
        )
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    # Deduct credits after success
    if user and not is_admin:
        credit_repo = CreditRepository(db)
        await credit_repo.deduct(
            user_id=user.id,
            cost=cost,
            action=CreditAction.CASE_FILE.value,
            description=f"Built case file from conversation {body.conversation_id}",
        )

    await db.commit()
    logger.info("case_file_built", case_id=result["id"], user=uid)

    return CaseFileDetail(**result)


@router.get("", response_model=CaseFileListResponse)
async def list_case_files(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List user's case files."""
    user_info = getattr(request.state, "user", {})
    uid = user_info.get("uid", "")

    repo = CaseFileRepository(db)
    case_files = await repo.list_for_user(uid)
    total = await repo.count_for_user(uid)

    return CaseFileListResponse(
        case_files=[
            CaseFileSummary(
                id=str(cf.id),
                title=cf.title,
                status=cf.status,
                conversation_id=str(cf.conversation_id) if cf.conversation_id else None,
                created_at=cf.created_at.isoformat() if cf.created_at else "",
                updated_at=cf.updated_at.isoformat() if cf.updated_at else "",
            )
            for cf in case_files
        ],
        total=total,
    )


@router.get("/{case_file_id}", response_model=CaseFileDetail)
async def get_case_file(
    case_file_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific case file with all sections."""
    import uuid as _uuid
    user_info = getattr(request.state, "user", {})
    uid = user_info.get("uid", "anonymous")

    try:
        cf_uuid = _uuid.UUID(case_file_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid case file ID"})

    repo = CaseFileRepository(db)
    cf = await repo.get_by_id(cf_uuid)
    if not cf:
        return JSONResponse(status_code=404, content={"error": "Case file not found"})

    from app.config.settings import settings
    if cf.user_id != uid and settings.app_env != "development":
        return JSONResponse(status_code=403, content={"error": "Unauthorized access to case file"})

    return CaseFileDetail(
        id=str(cf.id),
        title=cf.title,
        conversation_id=str(cf.conversation_id) if cf.conversation_id else None,
        facts=cf.facts,
        evidence=cf.evidence,
        applicable_laws=cf.applicable_laws,
        defense_strategies=cf.defense_strategies,
        prosecution_args=cf.prosecution_args,
        action_checklist=cf.action_checklist,
        unclear_items=cf.unclear_items,
        lawyer_brief=cf.lawyer_brief,
        citations=cf.citations,
        retrieved_chunks=cf.retrieved_chunks,
        rendered_text=cf.rendered_text or "",
        status=cf.status,
        user_notes=cf.user_notes or "",
        created_at=cf.created_at.isoformat() if cf.created_at else "",
        updated_at=cf.updated_at.isoformat() if cf.updated_at else "",
    )


@router.patch("/{case_file_id}", response_model=CaseFileDetail)
async def update_case_file(
    case_file_id: str,
    body: CaseFileUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update case file notes or status."""
    import uuid as _uuid
    user_info = getattr(request.state, "user", {})
    uid = user_info.get("uid", "anonymous")

    try:
        cf_uuid = _uuid.UUID(case_file_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid case file ID"})

    repo = CaseFileRepository(db)
    cf = await repo.get_by_id(cf_uuid)
    if not cf:
        return JSONResponse(status_code=404, content={"error": "Case file not found"})

    from app.config.settings import settings
    if cf.user_id != uid and settings.app_env != "development":
        return JSONResponse(status_code=403, content={"error": "Unauthorized access to case file"})

    kwargs = {}
    if body.user_notes is not None:
        kwargs["user_notes"] = body.user_notes
    if body.status is not None:
        kwargs["status"] = body.status

    cf = await repo.update(cf_uuid, **kwargs)
    if not cf:
        return JSONResponse(status_code=404, content={"error": "Case file not found"})

    await db.commit()

    return CaseFileDetail(
        id=str(cf.id),
        title=cf.title,
        conversation_id=str(cf.conversation_id) if cf.conversation_id else None,
        facts=cf.facts,
        evidence=cf.evidence,
        applicable_laws=cf.applicable_laws,
        defense_strategies=cf.defense_strategies,
        prosecution_args=cf.prosecution_args,
        action_checklist=cf.action_checklist,
        unclear_items=cf.unclear_items,
        lawyer_brief=cf.lawyer_brief,
        citations=cf.citations,
        retrieved_chunks=cf.retrieved_chunks,
        rendered_text=cf.rendered_text or "",
        status=cf.status,
        user_notes=cf.user_notes or "",
        created_at=cf.created_at.isoformat() if cf.created_at else "",
        updated_at=cf.updated_at.isoformat() if cf.updated_at else "",
    )


@router.delete("/{case_file_id}", status_code=204)
async def delete_case_file(
    case_file_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete a case file."""
    import uuid as _uuid
    user_info = getattr(request.state, "user", {})
    uid = user_info.get("uid", "anonymous")

    try:
        cf_uuid = _uuid.UUID(case_file_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid case file ID"})

    repo = CaseFileRepository(db)
    cf = await repo.get_by_id(cf_uuid)
    if not cf:
        return JSONResponse(status_code=404, content={"error": "Case file not found"})

    from app.config.settings import settings
    if cf.user_id != uid and settings.app_env != "development":
        return JSONResponse(status_code=403, content={"error": "Unauthorized access to case file"})

    await repo.delete(cf_uuid)
    await db.commit()
    return None


@router.post("/{case_file_id}/generate-document", response_model=DocumentGenerationResponse, status_code=201)
async def generate_document(
    case_file_id: str,
    body: DocumentGenerationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Generate a legal DOCX document and dispatch info (costs 5 credits)."""
    import base64
    import uuid as _uuid

    user_info = getattr(request.state, "user", None)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    uid = user_info.get("uid", "")

    try:
        cf_uuid = _uuid.UUID(case_file_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid case file ID"})

    # Check ownership
    repo = CaseFileRepository(db)
    cf = await repo.get_by_id(cf_uuid)
    if not cf:
        return JSONResponse(status_code=404, content={"error": "Case file not found"})

    from app.config.settings import settings
    if cf.user_id != uid and settings.app_env != "development":
        return JSONResponse(status_code=403, content={"error": "Unauthorized access to case file"})

    # Credit check
    cost = CreditAction.DOCUMENT_GENERATION.cost
    user_repo = UserRepository(db)
    user = await user_repo.get_by_firebase_uid(uid)

    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "User account not initialized."},
        )

    is_admin = user_info.get("tier") in ("ADMIN", "SUPERADMIN")

    credit_repo = CreditRepository(db)
    if not is_admin:
        credits = await credit_repo.get_balance(user.id)
        if not credit_repo.has_sufficient_credits(credits, cost):
            return JSONResponse(
                status_code=402,
                content={
                    "error": "insufficient_credits",
                    "message": f"Not enough credits to generate document (requires {cost} credits)",
                    "credits_remaining": credit_repo.get_remaining_credits(credits),
                },
            )

    try:
        svc = get_document_generator_service()
        result = await svc.generate_document(
            db=db,
            case_file_id=cf_uuid,
            document_type=body.document_type or "ოფიციალური დოკუმენტი / სარჩელი / საჩივარი",
            notes_for_drafting=body.notes_for_drafting,
        )
    except Exception as e:
        logger.error("document_generation_failed", error=str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Deduct credits
    if not is_admin:
        await credit_repo.deduct(
            user_id=user.id,
            cost=cost,
            action=CreditAction.DOCUMENT_GENERATION.value,
            description=f"Generated document for case file {case_file_id}",
        )
    await db.commit()

    docx_base64 = base64.b64encode(result["docx_bytes"]).decode("utf-8")

    return DocumentGenerationResponse(
        docx_base64=docx_base64,
        markdown_text=result["markdown_text"],
        dispatch_info=result["dispatch_info"],
    )

