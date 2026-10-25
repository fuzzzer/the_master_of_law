"""
Access-mode tests for the law connector: open with per-IP limits, API keys and
OAuth sign-in with per-user quotas, and isolation from the app's own auth.
"""

from __future__ import annotations

import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.config.settings import settings
from app.middleware import connector_access_middleware
from app.services import connector_access_service
from app.services.connector_access_service import ConnectorAccessService, hash_key

CODES = "/api/v1/connector/codes"
MCP_LIST = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
MCP_HEADERS = {"accept": "application/json, text/event-stream"}


class FakeLimiter:
    """In-memory stand-in for the Redis sliding window (counts only)."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    async def __call__(self, key: str, limit: int, window: float) -> tuple[bool, int]:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key] <= limit, int(window)


@pytest.fixture
def limiter(monkeypatch):
    fake = FakeLimiter()
    monkeypatch.setattr(connector_access_middleware, "rate_limiter", fake)
    return fake


@pytest.fixture
def access(monkeypatch, tmp_path):
    """A fresh access service whose key file lives in tmp_path."""
    keys_file = tmp_path / "keys.json"
    service = ConnectorAccessService(keys_file=keys_file)
    monkeypatch.setattr(connector_access_service, "_access_service", service)
    return service, keys_file


@pytest.fixture
def client(connector_service, limiter, access):
    from app.connector_main import create_connector_app

    with TestClient(create_connector_app()) as c:
        yield c


class TestOpenMode:
    def test_open_by_default(self, client):
        assert settings.connector_access_mode == "open"
        assert client.get(CODES).status_code == 200

    def test_per_ip_limit(self, client, limiter, monkeypatch):
        monkeypatch.setattr(settings, "connector_rate_limit_per_minute", 3)
        statuses = [client.get(CODES).status_code for _ in range(5)]
        assert statuses == [200, 200, 200, 429, 429]
        assert set(limiter.counts) == {"connector:minute:ip:testclient"}

    def test_limit_covers_mcp_too(self, client, monkeypatch):
        monkeypatch.setattr(settings, "connector_rate_limit_per_minute", 1)
        assert client.post("/mcp", json=MCP_LIST, headers=MCP_HEADERS).status_code == 200
        limited = client.post("/mcp", json=MCP_LIST, headers=MCP_HEADERS)
        assert limited.status_code == 429
        assert limited.headers["retry-after"]

    def test_real_redis_limiter_admits_under_limit(self, client, monkeypatch):
        """The default limiter is the app's Redis sliding window (fails open in dev)."""
        from app.middleware.rate_limit_middleware import check_redis_rate_limit

        monkeypatch.setattr(connector_access_middleware, "rate_limiter", check_redis_rate_limit)
        assert client.get(CODES).status_code == 200


class TestApiKeyMode:
    @pytest.fixture(autouse=True)
    def _key_mode(self, monkeypatch, access):
        monkeypatch.setattr(settings, "connector_access_mode", "api_key")
        _, keys_file = access
        keys_file.write_text(json.dumps({
            hash_key("good-key"): {"user": "alice", "daily_quota": 2},
            hash_key("other-key"): {"user": "bob"},
        }))

    def test_missing_key_is_401_with_challenge(self, client):
        response = client.get(CODES)
        assert response.status_code == 401
        assert response.json()["error"] == "connector_auth_required"
        assert response.headers["www-authenticate"].startswith("Bearer")

    def test_wrong_key(self, client):
        response = client.get(CODES, headers={"Authorization": "Bearer nope"})
        assert response.status_code == 401
        assert response.json()["error"] == "connector_key_invalid"

    def test_valid_key_and_daily_quota(self, client, limiter):
        auth = {"Authorization": "Bearer good-key"}
        assert [client.get(CODES, headers=auth).status_code for _ in range(3)] == [200, 200, 429]
        assert "connector:day:key:alice" in limiter.counts

    def test_quotas_are_per_user(self, client):
        for _ in range(2):
            client.get(CODES, headers={"Authorization": "Bearer good-key"})
        assert client.get(CODES, headers={"Authorization": "Bearer other-key"}).status_code == 200

    def test_mcp_needs_the_key_too(self, client):
        assert client.post("/mcp", json=MCP_LIST, headers=MCP_HEADERS).status_code == 401
        ok = client.post(
            "/mcp", json=MCP_LIST, headers=MCP_HEADERS | {"Authorization": "Bearer other-key"}
        )
        assert ok.status_code == 200

    def test_only_hashes_are_stored(self, access):
        _, keys_file = access
        assert "good-key" not in keys_file.read_text()


class TestOAuthMode:
    @pytest.fixture
    def signer(self, monkeypatch, access):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        service, _ = access
        monkeypatch.setattr(service, "_signing_key", lambda token: private_key.public_key())
        monkeypatch.setattr(settings, "connector_access_mode", "oauth")
        monkeypatch.setattr(settings, "connector_oauth_issuer", "https://auth.example.ge/")
        monkeypatch.setattr(settings, "connector_oauth_jwks_url", "https://auth.example.ge/jwks")
        monkeypatch.setattr(settings, "connector_oauth_audience", "https://law-api.example.ge/mcp")
        monkeypatch.setattr(settings, "connector_public_base_url", "https://law-api.example.ge")

        def sign(**overrides):
            claims = {
                "iss": "https://auth.example.ge/", "aud": "https://law-api.example.ge/mcp",
                "sub": "user-7", "exp": int(time.time()) + 600,
            } | overrides
            return jwt.encode(claims, private_key, algorithm="RS256")

        return sign

    def test_valid_token(self, client, signer, limiter):
        response = client.get(CODES, headers={"Authorization": f"Bearer {signer()}"})
        assert response.status_code == 200
        assert "connector:day:user:user-7" in limiter.counts

    def test_wrong_audience(self, client, signer):
        token = signer(aud="https://someone-else.example/mcp")
        assert client.get(CODES, headers={"Authorization": f"Bearer {token}"}).status_code == 401

    def test_expired(self, client, signer):
        token = signer(exp=int(time.time()) - 10)
        assert client.get(CODES, headers={"Authorization": f"Bearer {token}"}).status_code == 401

    def test_challenge_points_at_resource_metadata(self, client, signer):
        challenge = client.get(CODES).headers["www-authenticate"]
        expected = "https://law-api.example.ge/.well-known/oauth-protected-resource"
        assert f'resource_metadata="{expected}"' in challenge

    def test_not_configured_is_refused(self, client, signer, monkeypatch):
        monkeypatch.setattr(settings, "connector_oauth_issuer", "")
        response = client.get(CODES, headers={"Authorization": f"Bearer {signer()}"})
        assert response.json()["error"] == "connector_oauth_not_configured"

    def test_protected_resource_metadata(self, connector_service, signer, limiter):
        from app.connector_main import create_connector_app

        with TestClient(create_connector_app()) as c:
            meta = c.get("/.well-known/oauth-protected-resource").json()
        assert meta["resource"] == "https://law-api.example.ge/mcp"
        assert meta["authorization_servers"] == ["https://auth.example.ge/"]


class TestIsolationFromAppAuth:
    def test_connector_not_blocked_by_firebase_or_byok(
        self, connector_service, limiter, monkeypatch
    ):
        """With login and BYOK required for the app, the open connector still answers."""
        monkeypatch.setattr(settings, "connector_enabled", True)
        monkeypatch.setattr(settings, "auth_enabled", True)
        monkeypatch.setattr(settings, "byok_required", True)
        monkeypatch.setattr(settings, "app_env", "staging")
        from app.main import create_app

        with TestClient(create_app()) as c:
            assert c.get(CODES).status_code == 200
            assert c.post("/mcp", json=MCP_LIST, headers=MCP_HEADERS).status_code == 200
            assert c.get("/api/v1/conversations").status_code in (400, 401)
