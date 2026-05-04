"""
Law browser router — free endpoints for browsing and searching laws.

All endpoints in this router cost 0 credits.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.law_schema import (
    LawChunkResponse,
    LawCodeSummary,
    LawCodesResponse,
    LawSearchResponse,
)
from app.services.law_browser_service import get_law_browser_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/laws", tags=["laws"])


@router.get("/search", response_model=LawSearchResponse)
async def search_laws(
    q: str = Query(..., min_length=1, description="Search query"),
    domain: str | None = Query(None, description="Filter by legal code name"),
    top_k: int = Query(20, ge=1, le=100, description="Number of results"),
):
    """Search laws by query text (free, no credits)."""
    svc = get_law_browser_service()
    results = svc.search(query=q, domain=domain, top_k=top_k)

    return LawSearchResponse(
        results=[LawChunkResponse(
            chunk_id=r["chunk_id"],
            content=r.get("content", ""),
            metadata=r.get("metadata", {}),
        ) for r in results],
        query=q,
        total=len(results),
    )


@router.get("/codes", response_model=LawCodesResponse)
async def list_codes():
    """List all available legal codes (free)."""
    svc = get_law_browser_service()
    codes = svc.list_codes()
    return LawCodesResponse(
        codes=[LawCodeSummary(**c) for c in codes],
        total=len(codes),
    )


@router.get("/codes/{code_id}")
async def get_code(code_id: str):
    """Get a specific legal code structure (free)."""
    svc = get_law_browser_service()
    code = svc.get_code(code_id)
    if code is None:
        return {"error": "Code not found", "code_id": code_id}
    return code


@router.get("/articles/{article_id}")
async def get_article(article_id: str):
    """Get all chunks for a specific article (free)."""
    svc = get_law_browser_service()
    chunks = svc.get_article(article_id)
    return {
        "article_id": article_id,
        "chunks": [LawChunkResponse(
            chunk_id=c["chunk_id"],
            content=c.get("content", ""),
            metadata=c.get("metadata", {}),
        ) for c in chunks],
        "total": len(chunks),
    }
