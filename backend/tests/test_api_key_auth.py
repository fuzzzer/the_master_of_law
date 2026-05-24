"""
Tests for API key management and Firebase auth middleware.

Tests API key generation, validation, router endpoints,
and auth middleware paths (public, dev, API key, admin key).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── API Key Utility Tests ────────────────────────────────────

class TestApiKeyGeneration:
    """Tests for app.utils.api_keys functions."""

    def test_generate_key_prefix(self):
        """Generated key should have sk_ prefix."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"keys": []}, f)
            f.flush()
            with patch("app.utils.api_keys.settings") as mock_settings:
                mock_settings.api_keys_file = Path(f.name)
                from app.utils.api_keys import generate_api_key
                key = generate_api_key()
                assert key.startswith("sk_")
                assert len(key) > 34  # sk_ + 32 hex chars

    def test_generate_key_unique(self):
        """Each generated key should be unique."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"keys": []}, f)
            f.flush()
            with patch("app.utils.api_keys.settings") as mock_settings:
                mock_settings.api_keys_file = Path(f.name)
                from app.utils.api_keys import generate_api_key
                key1 = generate_api_key()
                key2 = generate_api_key()
                assert key1 != key2

    def test_valid_key_check(self):
        """Valid key should be recognized."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"keys": ["sk_test123"]}, f)
            f.flush()
            with patch("app.utils.api_keys.settings") as mock_settings:
                mock_settings.api_keys_file = Path(f.name)
                from app.utils.api_keys import is_valid_api_key
                assert is_valid_api_key("sk_test123") is True

    def test_invalid_key_check(self):
        """Invalid key should be rejected."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"keys": ["sk_real"]}, f)
            f.flush()
            with patch("app.utils.api_keys.settings") as mock_settings:
                mock_settings.api_keys_file = Path(f.name)
                from app.utils.api_keys import is_valid_api_key
                assert is_valid_api_key("sk_fake") is False

    def test_missing_key_file(self):
        """Missing key file should return empty set."""
        with patch("app.utils.api_keys.settings") as mock_settings:
            mock_settings.api_keys_file = Path("/nonexistent/path.json")
            from app.utils.api_keys import load_api_keys
            assert load_api_keys() == set()

    def test_corrupt_json_file(self):
        """Corrupt JSON file should return empty set."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json!!")
            f.flush()
            with patch("app.utils.api_keys.settings") as mock_settings:
                mock_settings.api_keys_file = Path(f.name)
                from app.utils.api_keys import load_api_keys
                assert load_api_keys() == set()

    def test_key_persisted(self):
        """Generated key should be persisted to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"keys": []}, f)
            f.flush()
            with patch("app.utils.api_keys.settings") as mock_settings:
                mock_settings.api_keys_file = Path(f.name)
                from app.utils.api_keys import generate_api_key, load_api_keys
                key = generate_api_key()
                keys = load_api_keys()
                assert key in keys


# ── API Key Router Tests ─────────────────────────────────────

class TestApiKeyRouter:
    """Tests for API key router endpoints."""

    @pytest.mark.asyncio
    async def test_check_valid_admin_key(self):
        """GET /check with valid admin key should return ok."""
        from app.routes.api_key_router import check_admin_key
        with patch("app.routes.api_key_router.settings") as mock_settings:
            mock_settings.admin_api_key = "test-admin-key"
            result = await check_admin_key(x_admin_key="test-admin-key")
            assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_check_invalid_admin_key(self):
        """GET /check with wrong admin key should raise 403."""
        from fastapi import HTTPException
        from app.routes.api_key_router import check_admin_key
        with patch("app.routes.api_key_router.settings") as mock_settings:
            mock_settings.admin_api_key = "test-admin-key"
            with pytest.raises(HTTPException) as exc_info:
                await check_admin_key(x_admin_key="wrong-key")
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_key_endpoint(self):
        """POST /api-keys should return a new key."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"keys": []}, f)
            f.flush()
            with patch("app.utils.api_keys.settings") as mock_settings:
                mock_settings.api_keys_file = Path(f.name)
                from app.routes.api_key_router import create_api_key
                result = await create_api_key()
                assert result.api_key.startswith("sk_")


# ── Firebase Auth Middleware Tests ────────────────────────────

class TestFirebaseAuthMiddleware:
    """Tests for the auth middleware dispatch logic."""

    def setup_method(self):
        from app.middleware.firebase_auth_middleware import FirebaseAuthMiddleware
        self.middleware = FirebaseAuthMiddleware(MagicMock())

    @pytest.mark.asyncio
    async def test_public_path_passes_through(self):
        """Public paths like /api/v1/health should skip auth."""
        request = MagicMock()
        request.url.path = "/api/v1/health"
        request.method = "GET"
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_options_passes_through(self):
        """CORS preflight (OPTIONS) should pass through."""
        request = MagicMock()
        request.method = "OPTIONS"
        request.url.path = "/api/v1/conversations"
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dev_mode_mock_user(self):
        """In dev mode with no token, mock user should be set."""
        request = MagicMock()
        request.url.path = "/api/v1/conversations"
        request.method = "GET"
        request.headers = {}
        request.state = MagicMock()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        with patch("app.middleware.firebase_auth_middleware.settings") as mock_settings:
            mock_settings.app_env = "development"
            mock_settings.admin_api_key = "admin-key"
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 200
            assert request.state.user["uid"] == "dev-user-001"

    @pytest.mark.asyncio
    async def test_admin_api_key(self):
        """Admin API key should give SUPERADMIN tier."""
        headers = MagicMock()
        headers.get = MagicMock(side_effect=lambda k, d="": {"X-API-Key": "admin-key", "Authorization": ""}.get(k, d))
        request = MagicMock()
        request.url.path = "/api/v1/conversations"
        request.method = "GET"
        request.headers = headers
        request.state = MagicMock()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        with patch("app.middleware.firebase_auth_middleware.settings") as mock_settings:
            mock_settings.app_env = "production"
            mock_settings.admin_api_key = "admin-key"
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 200
            assert request.state.user["tier"] == "SUPERADMIN"

    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """Invalid API key should return 401."""
        headers = MagicMock()
        headers.get = MagicMock(side_effect=lambda k, d="": {"X-API-Key": "fake-key", "Authorization": ""}.get(k, d))
        request = MagicMock()
        request.url.path = "/api/v1/conversations"
        request.method = "GET"
        request.headers = headers
        request.state = MagicMock()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        with patch("app.middleware.firebase_auth_middleware.settings") as mock_settings:
            mock_settings.app_env = "production"
            mock_settings.admin_api_key = "admin-key"
            with patch("app.utils.api_keys.is_valid_api_key", return_value=False):
                response = await self.middleware.dispatch(request, call_next)
                assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_auth_in_prod(self):
        """No token and no API key in production should return 401."""
        headers = MagicMock()
        headers.get = MagicMock(side_effect=lambda k, d="": {"Authorization": "", "X-API-Key": ""}.get(k, d))
        request = MagicMock()
        request.url.path = "/api/v1/conversations"
        request.method = "GET"
        request.headers = headers
        request.state = MagicMock()
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        with patch("app.middleware.firebase_auth_middleware.settings") as mock_settings:
            mock_settings.app_env = "production"
            mock_settings.admin_api_key = "admin-key"
            response = await self.middleware.dispatch(request, call_next)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_law_browsing_public(self):
        """Law browsing paths should be public."""
        request = MagicMock()
        request.url.path = "/api/v1/laws/codes"
        request.method = "GET"
        call_next = AsyncMock(return_value=MagicMock(status_code=200))

        response = await self.middleware.dispatch(request, call_next)
        assert response.status_code == 200
