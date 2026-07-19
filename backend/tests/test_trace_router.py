"""
Tests for the trace transparency router — route registration and admin guard.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.main import create_app
from app.routes.trace_router import require_admin


def _route_paths(app) -> set[str]:
    paths = set()
    for r in app.routes:
        if hasattr(r, "path"):
            paths.add(r.path)
        elif hasattr(r, "original_router"):
            for sub_r in r.original_router.routes:
                if hasattr(sub_r, "path"):
                    paths.add(sub_r.path)
    return paths


def test_trace_routes_registered():
    app = create_app()
    paths = _route_paths(app)

    assert "/api/v1/traces" in paths
    assert "/api/v1/traces/sessions" in paths
    assert "/api/v1/traces/dashboard" in paths
    assert "/api/v1/traces/{trace_id}" in paths
    assert "/api/v1/traces/{trace_id}/export" in paths
    assert "/api/v1/traces/conversation/{conversation_id}/export" in paths


def _request_with_tier(tier: str | None):
    request = MagicMock()
    request.state.user = {"uid": "u", "tier": tier} if tier else None
    return request


def test_require_admin_allows_admin_tiers():
    require_admin(_request_with_tier("ADMIN"))
    require_admin(_request_with_tier("SUPERADMIN"))


def test_require_admin_rejects_free_tier():
    with pytest.raises(HTTPException) as exc:
        require_admin(_request_with_tier("FREE"))
    assert exc.value.status_code == 403


def test_require_admin_rejects_missing_user():
    with pytest.raises(HTTPException) as exc:
        require_admin(_request_with_tier(None))
    assert exc.value.status_code == 403
