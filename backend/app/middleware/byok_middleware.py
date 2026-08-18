"""
Bring-your-own-key middleware — binds the caller's Google key to the request.

WHY THIS IS PURE ASGI AND NOT BaseHTTPMiddleware:
two reasons, both load-bearing.

1. BaseHTTPMiddleware runs the downstream app in a task spawned from its own
   task group. Context set before ``call_next`` does propagate today, but it
   is an implementation detail of Starlette's plumbing rather than a promise —
   and the failure mode if it ever changes is silent: the key vanishes, the
   client factory falls back to the SERVER's credential, and every user's
   traffic quietly lands on the operator's bill while still returning correct
   answers. A plain ASGI callable runs the whole request in this very task, so
   the ContextVar is simply in scope.

2. BaseHTTPMiddleware does not see WebSocket connections at all, and the chat
   stream — the single biggest consumer of model calls in the app — is a
   WebSocket. Here the key is bound for the whole connection lifetime.

The header defaults to the one the Flutter app ALREADY sends for its access
key (X-API-Key), so switching a deployment to BYOK needs no client change:
the same field the user already fills in now holds their Google key instead
of an invite code. WebSocket callers pass it as ?api_key= because browsers
cannot set headers on a WebSocket handshake.
"""

from __future__ import annotations

from urllib.parse import parse_qs

from starlette.types import ASGIApp, Receive, Scope, Send

from app.config.request_context import (
    ModelChoice,
    reset_byok_key,
    reset_model_choice,
    set_byok_key,
    set_model_choice,
)
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Paths that never make a model call, and so never need a key. Everything not
# listed here requires one when byok_required is on. The list is an ALLOWLIST
# on purpose: an AI route added next month is protected by default, whereas a
# blocklist of "AI paths" would let it through unguarded and fail deep in the
# pipeline with an error about credentials that the user cannot act on.
NO_KEY_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}
NO_KEY_PREFIXES = (
    "/api/v1/health",
    "/api/v1/laws/",      # browsing the corpus is pure retrieval, no model call
    "/api/v1/api-keys/",  # where the user goes to validate a key they just got
    "/api/v1/traces/",    # admin dashboard, guarded by its own admin key
    "/docs",
    "/redoc",
)

# Google AI Studio keys are "AIza" + 35 more characters. Checking the shape
# costs nothing and converts the most common user error — pasting the wrong
# string entirely — into an immediate, specific message instead of a failure
# surfacing several layers down as an opaque provider error.
_GOOGLE_KEY_PREFIX = "AIza"
_GOOGLE_KEY_LEN = 39


def looks_like_google_key(key: str) -> bool:
    """Shape check only — proves nothing about whether the key still works."""
    return (
        len(key) == _GOOGLE_KEY_LEN
        and key.startswith(_GOOGLE_KEY_PREFIX)
        and key.isascii()
        and not any(c.isspace() for c in key)
    )


# Headers carrying the caller's personal model choice. Sent on every request
# by the client that stores it, exactly like the key: the selection belongs to
# whoever is paying, so it travels with their request rather than living in a
# deployment-wide setting one user could change for everyone.
MODEL_STRONG_HEADER = "X-Model-Strong"
MODEL_CHEAP_HEADER = "X-Model-Cheap"

# A model id is provider-defined, so it is not validated here beyond basic
# sanity; the model routes smoke-test a choice before the client stores it,
# and an id that slips through fails as a normal provider error.
_MAX_MODEL_ID = 100


def _clean_model(value: str) -> str | None:
    value = value.strip()[:_MAX_MODEL_ID]
    if not value or any(c.isspace() for c in value) or not value.isascii():
        return None
    return value


def extract_model_choice(scope: Scope) -> ModelChoice:
    """The caller's per-tier model selection, if they sent one."""
    if scope["type"] == "websocket":
        strong = _header(scope, MODEL_STRONG_HEADER) or _query_param(scope, "model_strong")
        cheap = _header(scope, MODEL_CHEAP_HEADER) or _query_param(scope, "model_cheap")
    else:
        strong = _header(scope, MODEL_STRONG_HEADER)
        cheap = _header(scope, MODEL_CHEAP_HEADER)
    return ModelChoice(
        strong=_clean_model(strong) if strong else None,
        cheap=_clean_model(cheap) if cheap else None,
    )


def _needs_key(path: str) -> bool:
    if path in NO_KEY_PATHS:
        return False
    return not path.startswith(NO_KEY_PREFIXES)


def _header(scope: Scope, name: str) -> str:
    wanted = name.lower().encode()
    for raw_name, raw_value in scope.get("headers") or []:
        if raw_name.lower() == wanted:
            return raw_value.decode("latin-1").strip()
    return ""


def _query_param(scope: Scope, name: str) -> str:
    qs = scope.get("query_string") or b""
    if not qs:
        return ""
    values = parse_qs(qs.decode("latin-1")).get(name) or []
    return values[0].strip() if values else ""


def extract_caller_key(scope: Scope) -> str:
    """The caller's Google key, from the header (HTTP) or query (WebSocket)."""
    if scope["type"] == "websocket":
        # Browsers cannot set headers on a WebSocket handshake, so the Flutter
        # client puts it in the query string. Header still wins when present
        # (native clients, curl) — see the deployment note about keeping query
        # strings out of the reverse proxy's access log.
        return _header(scope, settings.byok_key_header) or _query_param(scope, "api_key")
    return _header(scope, settings.byok_key_header)


async def _reject_http(send: Send, status: int, code: str, message_ka: str, message_en: str) -> None:
    import json

    body = json.dumps(
        {"error": code, "message": message_ka, "message_en": message_en},
        ensure_ascii=False,
    ).encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})


async def _reject_ws(send: Send, reason: str) -> None:
    # 1008 = policy violation. The handshake is accepted first so the client
    # receives a readable reason instead of a bare connection failure.
    await send({"type": "websocket.accept"})
    await send({
        "type": "websocket.send",
        "text": '{"type":"error","code":"byok_key_required","message":"%s"}' % reason,
    })
    await send({"type": "websocket.close", "code": 1008})


class ByokMiddleware:
    """Bind the caller's Google API key to the request context."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        # The model choice is bound even when BYOK is off, and even on paths
        # that need no key: it is an independent preference, and a request
        # that carries one should be served on it either way.
        model_token = set_model_choice(extract_model_choice(scope))
        try:
            await self._dispatch(scope, receive, send)
        finally:
            reset_model_choice(model_token)

    async def _dispatch(self, scope: Scope, receive: Receive, send: Send) -> None:
        # When BYOK is off the same header carries a legacy access key, which
        # must NOT be handed to Google as a credential.
        if not settings.byok_required:
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if scope["type"] == "http" and scope.get("method") == "OPTIONS":
            return await self.app(scope, receive, send)

        key = extract_caller_key(scope)

        if not key:
            if not _needs_key(path):
                return await self.app(scope, receive, send)
            if scope["type"] == "websocket":
                return await _reject_ws(send, "დაამატეთ Google AI Studio-ს გასაღები.")
            return await _reject_http(
                send, 401, "byok_key_required",
                "AI-ს გამოსაყენებლად საჭიროა Google AI Studio-ს გასაღები. "
                "დაამატეთ იგი პარამეტრებში.",
                "A Google AI Studio API key is required. Add it in settings.",
            )

        if not looks_like_google_key(key):
            # Most likely an old sk_ access key, or a pasted URL/whitespace.
            if scope["type"] == "websocket":
                return await _reject_ws(send, "გასაღები არასწორია. გთხოვთ, შეამოწმოთ.")
            return await _reject_http(
                send, 401, "byok_key_invalid",
                "გასაღები არასწორია. დარწმუნდით, რომ ჩასვით Google AI Studio-ს "
                "გასაღები (იწყება AIza-თი).",
                "That does not look like a Google AI Studio key (they start with AIza).",
            )

        token = set_byok_key(key)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_byok_key(token)
