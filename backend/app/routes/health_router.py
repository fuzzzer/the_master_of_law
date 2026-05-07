"""
Health check endpoints — liveness and readiness probes.

- ``GET /api/v1/health``       — simple liveness (always 200 if server runs)
- ``GET /api/v1/health/ready`` — deep readiness (checks ChromaDB, Gemini connectivity)
"""

from __future__ import annotations

from fastapi import APIRouter

from app.integrations.chroma_client import get_chroma_client
from app.schemas.health_schema import (
    HealthResponse,
    ReadinessDetail,
    ReadinessResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def liveness():
    """Liveness probe — if the server is running, return 200."""
    return HealthResponse()


@router.get("/ready", response_model=ReadinessResponse)
async def readiness():
    """
    Readiness probe — checks all backend dependencies.

    Returns 200 with status "ok" if all components are healthy,
    or 200 with status "degraded" if some components are down.
    """
    components: list[ReadinessDetail] = []

    # ── ChromaDB ─────────────────────────────────────────
    try:
        chroma = get_chroma_client()
        count = chroma.count()
        n_collections = len(chroma.available_collections)
        components.append(ReadinessDetail(
            name="chromadb",
            status="ok",
            detail=f"{count} documents across {n_collections} collection(s)",
        ))
    except Exception as e:
        logger.error("readiness_chroma_failed", error=str(e))
        components.append(ReadinessDetail(
            name="chromadb",
            status="error",
            detail=str(e),
        ))

    # ── Vertex AI Embedding ──────────────────────────────
    # We don't call the API on every health check to avoid quota usage.
    # Just verify the client can be instantiated.
    try:
        from app.integrations.vertex_embedding_client import get_embedding_client
        client = get_embedding_client()
        # Verify the client object exists (doesn't call API)
        _ = client._get_client()
        components.append(ReadinessDetail(
            name="vertex_embedding",
            status="ok",
            detail="Client initialized",
        ))
    except Exception as e:
        logger.error("readiness_embedding_failed", error=str(e))
        components.append(ReadinessDetail(
            name="vertex_embedding",
            status="error",
            detail=str(e),
        ))

    # ── Overall status ───────────────────────────────────
    all_ok = all(c.status == "ok" for c in components)
    return ReadinessResponse(
        status="ok" if all_ok else "degraded",
        components=components,
    )
