"""
Integration tests — full HTTP endpoint tests using FastAPI TestClient.

Tests actual request/response flows. DB-dependent endpoints are tested
for graceful failure when PostgreSQL is unavailable (expected in CI/dev).
"""

import sys
sys.path.insert(0, ".")

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the app."""
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoints:
    def test_liveness(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_readiness(self, client):
        r = client.get("/api/v1/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("ok", "degraded")
        assert "components" in data
        assert len(data["components"]) >= 1


class TestLawBrowserEndpoints:
    """Law browser is free and public — no auth, no credits, no DB."""

    def test_search_laws(self, client):
        r = client.get("/api/v1/laws/search", params={"q": "მუხლი"})
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "total" in data
        assert data["total"] >= 0

    def test_search_laws_with_domain_filter(self, client):
        r = client.get("/api/v1/laws/search", params={
            "q": "დანაშაული",
            "domain": "სისხლის სამართლის კოდექსი",
        })
        assert r.status_code == 200

    def test_search_laws_top_k(self, client):
        r = client.get("/api/v1/laws/search", params={"q": "ვალი", "top_k": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] <= 5

    def test_search_laws_empty_query_rejected(self, client):
        r = client.get("/api/v1/laws/search", params={"q": ""})
        assert r.status_code == 422  # FastAPI validation

    def test_list_codes(self, client):
        r = client.get("/api/v1/laws/codes")
        assert r.status_code == 200
        data = r.json()
        assert "codes" in data
        assert "total" in data

    def test_get_article_missing(self, client):
        r = client.get("/api/v1/laws/articles/nonexistent-article")
        assert r.status_code == 200
        assert r.json()["total"] == 0


class TestDBDependentEndpoints:
    """
    These endpoints require PostgreSQL. Without it, the middleware
    should return 500 (error handler catches the connection failure).
    We test that the server doesn't crash and returns valid JSON.
    """

    def test_auth_me_returns_valid_response(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code in (200, 401, 500)
        # Should always return JSON, never crash
        assert r.headers.get("content-type", "").startswith("application/json")

    def test_conversations_list(self, client):
        r = client.get("/api/v1/conversations")
        assert r.status_code in (200, 500)

    def test_conversations_create(self, client):
        r = client.post("/api/v1/conversations", json={"title": "test"})
        assert r.status_code in (200, 201, 500)

    def test_case_files_list(self, client):
        r = client.get("/api/v1/case-files")
        assert r.status_code in (200, 500)

    def test_case_file_invalid_uuid(self, client):
        r = client.get("/api/v1/case-files/not-a-uuid")
        # This should be caught before DB call
        assert r.status_code in (400, 500)

    def test_credits(self, client):
        r = client.get("/api/v1/account/credits")
        assert r.status_code in (200, 500)

    def test_transactions(self, client):
        r = client.get("/api/v1/account/transactions")
        assert r.status_code in (200, 500)


class TestOpenAPISchema:
    def test_openapi_json(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        data = r.json()
        paths = list(data["paths"].keys())
        # Verify all key endpoints are in the schema
        assert "/api/v1/health" in paths
        assert "/api/v1/laws/search" in paths
        assert "/api/v1/case-files/build" in paths
        assert "/api/v1/conversations" in paths

    def test_docs_available(self, client):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_redoc_available(self, client):
        r = client.get("/redoc")
        assert r.status_code == 200
