"""
Connector Access Service — who is calling the law connector, and how much.

Three modes, chosen by ``settings.connector_access_mode`` because free versus
paid is still the owner's decision:

* ``open``    — anyone; the caller is their IP address, limited per minute.
* ``api_key`` — ``Authorization: Bearer <key>``; keys are stored only as
  SHA-256 hashes in ``connector_api_keys_file``, each with its own user name
  and optional daily quota.
* ``oauth``   — ``Authorization: Bearer <JWT>`` from the configured issuer
  (the sign-in service a ChatGPT or Claude connector sends users through);
  the caller is the token's subject.

Signed-in callers get a per-minute limit and a daily quota.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import jwt

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

MINUTE = 60.0
DAY = 86_400.0


@dataclass(frozen=True)
class ConnectorCaller:
    """An admitted caller and the limits that apply to them."""

    caller_id: str
    per_minute: int
    daily_quota: int | None  # None = no daily quota (open mode)


class ConnectorAccessDenied(Exception):
    """The request carries no usable credential for the configured mode."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def hash_key(key: str) -> str:
    """The form a connector API key is stored in."""
    return hashlib.sha256(key.encode()).hexdigest()


def _bearer_token(authorization: str) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ConnectorAccessDenied(
            "connector_auth_required",
            "Sign-in required: send 'Authorization: Bearer <token>'.",
        )
    return token.strip()


class ConnectorAccessService:
    """Resolve a request's caller under the configured access mode."""

    def __init__(self, keys_file: Path | None = None) -> None:
        self._keys_file = keys_file
        self._jwks_client: jwt.PyJWKClient | None = None

    def resolve(self, client_ip: str, authorization: str) -> ConnectorCaller:
        """Identify the caller or raise :class:`ConnectorAccessDenied`."""
        mode = settings.connector_access_mode
        if mode == "open":
            return ConnectorCaller(
                caller_id=f"ip:{client_ip}",
                per_minute=settings.connector_rate_limit_per_minute,
                daily_quota=None,
            )
        token = _bearer_token(authorization)
        if mode == "api_key":
            return self._caller_from_key(token)
        return self._caller_from_jwt(token)

    def _load_keys(self) -> dict[str, dict]:
        path = self._keys_file or settings.connector_api_keys_file
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.error("connector_keys_unreadable", path=str(path), error=str(e))
            return {}

    def _caller_from_key(self, key: str) -> ConnectorCaller:
        entry = self._load_keys().get(hash_key(key))
        if not entry:
            raise ConnectorAccessDenied("connector_key_invalid", "This connector key is not valid.")
        return ConnectorCaller(
            caller_id=f"key:{entry.get('user') or hash_key(key)[:12]}",
            per_minute=settings.connector_rate_limit_per_minute,
            daily_quota=int(entry.get("daily_quota") or settings.connector_daily_quota),
        )

    def _signing_key(self, token: str) -> object:
        if self._jwks_client is None:
            self._jwks_client = jwt.PyJWKClient(settings.connector_oauth_jwks_url)
        return self._jwks_client.get_signing_key_from_jwt(token).key

    def _caller_from_jwt(self, token: str) -> ConnectorCaller:
        if not (settings.connector_oauth_issuer and settings.connector_oauth_jwks_url):
            raise ConnectorAccessDenied(
                "connector_oauth_not_configured",
                "Sign-in is not configured on this server yet.",
            )
        try:
            claims = jwt.decode(
                token,
                self._signing_key(token),
                algorithms=["RS256", "ES256"],
                issuer=settings.connector_oauth_issuer,
                audience=settings.connector_oauth_audience or None,
                options={"verify_aud": bool(settings.connector_oauth_audience)},
            )
        except jwt.PyJWTError as e:
            raise ConnectorAccessDenied(
                "connector_token_invalid", f"Sign-in token rejected: {e}"
            ) from e
        subject = claims.get("sub")
        if not subject:
            raise ConnectorAccessDenied("connector_token_invalid", "Sign-in token has no subject.")
        return ConnectorCaller(
            caller_id=f"user:{subject}",
            per_minute=settings.connector_rate_limit_per_minute,
            daily_quota=settings.connector_daily_quota,
        )


def protected_resource_metadata() -> dict:
    """OAuth protected-resource metadata (RFC 9728) for MCP clients' discovery."""
    base = settings.connector_public_base_url.rstrip("/")
    return {
        "resource": f"{base}/mcp",
        "authorization_servers": [settings.connector_oauth_issuer],
        "bearer_methods_supported": ["header"],
        "resource_name": "Fuzzzy Law — Georgian law sources",
    }


_access_service: ConnectorAccessService | None = None


def get_connector_access_service() -> ConnectorAccessService:
    global _access_service
    if _access_service is None:
        _access_service = ConnectorAccessService()
    return _access_service
