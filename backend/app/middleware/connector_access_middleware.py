"""
Law connector access middleware — admission, rate limits and quotas.

Pure ASGI, like the BYOK middleware, so the MCP endpoint's streamed responses
pass through untouched. It guards only the connector's own paths; the app's
other middleware leave those paths alone (see their allowlists), because the
connector has its own callers — outside AI agents — and its own access modes.
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config.settings import settings
from app.middleware.rate_limit_middleware import check_redis_rate_limit
from app.services.connector_access_service import (
    DAY,
    MINUTE,
    ConnectorAccessDenied,
    get_connector_access_service,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

CONNECTOR_PREFIXES = ("/mcp", "/api/v1/connector")
# Discovery documents a client must read before it can sign in.
CONNECTOR_OPEN_PATHS = {"/api/v1/connector/openapi.json"}

rate_limiter = check_redis_rate_limit


def is_connector_path(path: str) -> bool:
    return path.startswith(CONNECTOR_PREFIXES)


def _header(scope: Scope, name: bytes) -> str:
    for raw_name, raw_value in scope.get("headers") or []:
        if raw_name.lower() == name:
            return raw_value.decode("latin-1").strip()
    return ""


async def _reply(send: Send, status: int, body: dict, headers: list[tuple[bytes, bytes]]) -> None:
    payload = json.dumps(body, ensure_ascii=False).encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(payload)).encode()),
            *headers,
        ],
    })
    await send({"type": "http.response.body", "body": payload})


def _www_authenticate() -> list[tuple[bytes, bytes]]:
    value = "Bearer"
    if settings.connector_access_mode == "oauth":
        base = settings.connector_public_base_url.rstrip("/")
        value += f' resource_metadata="{base}/.well-known/oauth-protected-resource"'
    return [(b"www-authenticate", value.encode())]


class ConnectorAccessMiddleware:
    """Admit, rate-limit and meter calls to the law connector."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if (
            scope["type"] != "http"
            or not is_connector_path(path)
            or path in CONNECTOR_OPEN_PATHS
            or scope.get("method") == "OPTIONS"
        ):
            return await self.app(scope, receive, send)

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        try:
            caller = get_connector_access_service().resolve(
                client_ip, _header(scope, b"authorization")
            )
        except ConnectorAccessDenied as denied:
            logger.info("connector_access_denied", code=denied.code, path=path)
            return await _reply(
                send, 401, {"error": denied.code, "message": denied.message}, _www_authenticate()
            )

        allowed, retry_after = await rate_limiter(
            f"connector:minute:{caller.caller_id}", caller.per_minute, MINUTE
        )
        if allowed and caller.daily_quota is not None:
            allowed, retry_after = await rate_limiter(
                f"connector:day:{caller.caller_id}", caller.daily_quota, DAY
            )
        if not allowed:
            logger.warning("connector_rate_limited", caller=caller.caller_id)
            return await _reply(
                send,
                429,
                {
                    "error": "rate_limited",
                    "message": "Too many requests to the law connector; try again later.",
                    "retry_after_seconds": retry_after,
                },
                [(b"retry-after", str(retry_after).encode())],
            )
        return await self.app(scope, receive, send)
