"""
Health check schemas.
"""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Basic liveness response."""
    status: str = "ok"
    service: str = "the-master-of-law"
    version: str = "0.1.0"


class ReadinessDetail(BaseModel):
    """Individual component readiness."""
    name: str
    status: str  # "ok" or "error"
    detail: str = ""


class ReadinessResponse(BaseModel):
    """Full readiness check response."""
    status: str  # "ok" if all components ready, else "degraded"
    components: list[ReadinessDetail]
