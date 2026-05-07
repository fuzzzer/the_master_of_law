"""
RAG router — collection management and status endpoints.

GET /api/v1/rag/collections — list available RAG collections with their status.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.integrations.chroma_client import get_chroma_client
from app.schemas.rag_schema import CollectionInfo, CollectionListResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.get("/collections", response_model=CollectionListResponse)
async def list_collections():
    """
    List available RAG collections and their status.

    Returns information about each knowledge source:
    - georgian_laws: Legal codes from Matsne (15 codes)
    - court_practice: Supreme Court case rulings (2022-2026)
    - grand_chamber: Grand Chamber binding decisions

    Each collection includes availability status and document count.
    """
    try:
        chroma = get_chroma_client()
        info = chroma.get_collection_info()
    except Exception as e:
        logger.error("rag_collections_error", error=str(e))
        # Return all collections as unavailable
        from app.integrations.chroma_client import ChromaClient
        info = [
            {
                "id": name,
                "name_ka": meta["name_ka"],
                "description": meta["description"],
                "available": False,
                "chunk_count": 0,
            }
            for name, meta in ChromaClient.COLLECTIONS.items()
        ]

    return CollectionListResponse(
        collections=[CollectionInfo(**c) for c in info]
    )
