"""
Document generation reports a provider failure the way every route does.

Production, 2026-10-01: `POST /case-files/{id}/generate-document` answered
`500 {"error": "429 RESOURCE_EXHAUSTED. {'error': …"}` — Google's raw English
text, because the route caught every exception itself and returned `str(e)`
instead of letting the shared error handler classify it.

Needs the migrated test database (`scripts/test-db.sh up`).
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import app.models.database as db_module
from app.middleware.error_handler_middleware import ErrorHandlerMiddleware
from app.repositories.case_file_repository import CaseFileRepository
from app.repositories.user_repository import UserRepository
from app.routes.case_file_router import router

QUOTA_429 = (
    "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded "
    "your current quota.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': "
    "'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '41s'}]}}"
)


def _reset_engine():
    db_module._engine = None
    db_module._session_factory = None


async def _case_file_owned_by(login_id: str) -> str:
    async with db_module.get_session_factory()() as db:
        user = await UserRepository(db).create_or_update(firebase_uid=login_id)
        cf = await CaseFileRepository(db).create(user_id=user.id, title="t", status="draft")
        await db.commit()
        case_file_id = str(cf.id)
    await db_module._engine.dispose()
    return case_file_id


def test_a_spent_quota_while_drafting_is_a_georgian_503_not_googles_text():
    login_id = f"anon:test-{uuid.uuid4().hex[:8]}"
    _reset_engine()
    case_file_id = asyncio.run(_case_file_owned_by(login_id))
    _reset_engine()

    app = FastAPI()
    app.add_middleware(ErrorHandlerMiddleware)

    @app.middleware("http")
    async def as_caller(request: Request, call_next):
        request.state.user = {"uid": login_id, "tier": "ADMIN"}
        return await call_next(request)

    app.include_router(router)
    generator = MagicMock()
    generator.generate_document = AsyncMock(side_effect=RuntimeError(QUOTA_429))

    with patch("app.routes.case_file_router.get_document_generator_service", return_value=generator), \
            TestClient(app, raise_server_exceptions=False) as client:
        r = client.post(f"/api/v1/case-files/{case_file_id}/generate-document", json={})
    _reset_engine()

    assert r.status_code == 503, r.text
    body = r.json()
    assert body["error"] == "ai_quota_exhausted"
    assert "RESOURCE_EXHAUSTED" not in r.text
    assert any("Ⴀ" <= ch <= "ჿ" for ch in body["message"])


def test_no_route_answers_a_catch_all_with_the_exceptions_own_text():
    """`except Exception as e: return …str(e)…` hides the failure from the
    shared error handler and hands the user raw provider text."""
    import ast
    from pathlib import Path

    offenders = []
    for path in Path("app/routes").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not (isinstance(node, ast.ExceptHandler) and node.name
                    and isinstance(node.type, ast.Name) and node.type.id == "Exception"):
                continue
            for ret in (n for stmt in node.body for n in ast.walk(stmt) if isinstance(n, ast.Return)):
                if any(isinstance(c, ast.Call) and getattr(c.func, "id", None) == "str"
                       and any(getattr(a, "id", None) == node.name for a in c.args)
                       for c in ast.walk(ret)):
                    offenders.append(f"{path}:{ret.lineno}")
    assert not offenders, offenders
