"""
REST mirror and OpenAPI tests — what a custom GPT Action imports and calls.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from openapi_spec_validator import validate

from app.config.settings import settings
from app.routes.connector_router import connector_openapi

GPT_OPERATIONS = {
    "listCodes", "searchLaw", "getArticle", "browseCode", "findCourtPractice", "verifyCitation",
}


@pytest.fixture
def client(connector_service):
    from app.connector_main import create_connector_app

    with TestClient(create_connector_app()) as c:
        yield c


class TestOpenApi:
    def test_valid_openapi_3_1(self):
        spec = connector_openapi()
        assert spec["openapi"].startswith("3.1")
        validate(spec)

    def test_only_connector_operations_each_with_an_id(self):
        spec = connector_openapi()
        ops = [op for path in spec["paths"].values() for op in path.values()]
        assert {op["operationId"] for op in ops} == GPT_OPERATIONS
        assert all(p.startswith("/api/v1/connector/") for p in spec["paths"])

    def test_fits_gpt_action_limits(self):
        """GPT Actions cut operation descriptions at 300 and parameters at 700 characters."""
        spec = connector_openapi()
        for path in spec["paths"].values():
            for op in path.values():
                assert len(op.get("description", "")) <= 300
                for param in op.get("parameters", []):
                    assert len(param.get("description", "")) <= 700

    def test_servers_use_public_base_url(self, monkeypatch):
        monkeypatch.setattr(settings, "connector_public_base_url", "https://law-api.example.ge/")
        assert connector_openapi()["servers"] == [{"url": "https://law-api.example.ge"}]

    def test_served_without_credentials_even_in_key_mode(self, client, monkeypatch):
        monkeypatch.setattr(settings, "connector_access_mode", "api_key")
        response = client.get("/api/v1/connector/openapi.json")
        assert response.status_code == 200
        assert response.json()["info"]["title"].startswith("Fuzzzy Law")


class TestEndpoints:
    def test_codes(self, client):
        data = client.get("/api/v1/connector/codes").json()
        assert len(data["codes"]) == 3

    def test_search(self, client):
        params = {"query": "სააპელაციო საჩივრის ვადა"}
        data = client.get("/api/v1/connector/search", params=params).json()
        assert data["found"]
        assert all(r["source_url"] for r in data["results"])

    def test_search_needs_a_query(self, client):
        assert client.get("/api/v1/connector/search").status_code == 422

    def test_article(self, client):
        data = client.get(
            "/api/v1/connector/articles", params={"code": "labour_code", "article": "48"}
        ).json()
        assert data["found"] and data["article"]["text"]

    def test_structure(self, client):
        data = client.get("/api/v1/connector/structure", params={"code": "civil_code"}).json()
        assert data["total_articles"] == 3

    def test_court_practice(self, client):
        data = client.get("/api/v1/connector/court-practice", params={"query": "ვადა"}).json()
        assert data["status"] == "source_unavailable"

    def test_verify_citation(self, client):
        data = client.post("/api/v1/connector/verify-citation", json={
            "code": "civil_code", "article": "138", "claim": "სარჩელის შეტანით წყდება",
        }).json()
        assert data["exists"]
        assert data["text"]

    def test_same_answer_as_the_mcp_tool(self, client, connector_service):
        rest = client.get(
            "/api/v1/connector/articles", params={"code": "civil_code", "article": "137"}
        ).json()
        assert rest == connector_service.get_article("civil_code", "137").model_dump(mode="json")
