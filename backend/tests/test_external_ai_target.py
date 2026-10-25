"""
Tests for the scorecard's "outside AI + connector" target (eval/scorecard/targets/external_ai.py).

No model is called: fake ``anthropic`` / ``openai`` modules stand in for the SDKs, and the
connector's HTTP calls are answered by the real connector app in-process. This proves the tool
list comes from the connector's own OpenAPI, tool calls reach the connector, citations are
collected, and the target skips cleanly without a key.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TARGET_FILE = Path(__file__).resolve().parents[2] / "eval" / "scorecard" / "targets" / "external_ai.py"


@pytest.fixture
def target_module():
    spec = importlib.util.spec_from_file_location("external_ai_under_test", TARGET_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def connector_http(connector_service):
    from app.connector_main import create_connector_app

    with TestClient(create_connector_app()) as client:
        def http(self, method, path, params=None, body=None):
            response = client.request(method, path, params=params, json=body)
            return response.json()

        yield http


def _block(**fields):
    return types.SimpleNamespace(**fields)


class FakeAnthropic:
    """Asks for getArticle once, then answers."""

    calls: list[dict] = []

    def __init__(self, api_key, max_retries):
        self.beta = types.SimpleNamespace(messages=types.SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        FakeAnthropic.calls.append(kwargs)
        if len(FakeAnthropic.calls) == 1:
            return _block(stop_reason="tool_use", model=kwargs["model"], content=[
                _block(type="tool_use", id="t1", name="getArticle",
                       input={"code": "civil_procedure_code", "article": "369"}),
            ])
        return _block(stop_reason="end_turn", model=kwargs["model"], content=[
            _block(type="text", text="„სააპელაციო საჩივრის შეტანის ვადა...“ (მუხლი 369)"),
        ])


class TestTarget:
    def test_skips_without_key(self, target_module):
        assert not target_module.ExternalConnectorTarget("claude", None, connector=True).available
        assert target_module.ExternalConnectorTarget("claude", "k", connector=True).available

    def test_tools_come_from_the_connector_openapi(self, target_module):
        from app.routes.connector_router import connector_openapi

        tools = target_module.tools_from_openapi(connector_openapi())
        names = {t["name"] for t in tools}
        assert names == {"listCodes", "searchLaw", "getArticle", "browseCode",
                         "findCourtPractice", "verifyCitation"}
        verify = next(t for t in tools if t["name"] == "verifyCitation")
        assert verify["body"] and set(verify["schema"]["required"]) == {"code", "article", "claim"}
        search = next(t for t in tools if t["name"] == "searchLaw")
        assert search["schema"]["required"] == ["query"]

    def test_claude_with_connector_calls_tools_and_collects_citations(
        self, target_module, connector_http, monkeypatch
    ):
        monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=FakeAnthropic))
        monkeypatch.setattr(target_module.ExternalConnectorTarget, "_http", connector_http)
        FakeAnthropic.calls = []
        target = target_module.ExternalConnectorTarget("claude", "secret-key", connector=True)
        rec = target._answer_sync({"id": "x", "message": "რა ვადაა სააპელაციო საჩივრისთვის?"})

        assert rec["status"] == 200
        assert rec["body"]["tool_calls"] == ["getArticle"]
        cite = rec["body"]["citations"][0]
        assert cite["article_number"] == "მუხლი 369"
        assert cite["article_url"].startswith("https://matsne.gov.ge/")
        first = FakeAnthropic.calls[0]
        assert first["fallbacks"] == "default"
        assert "Fuzzzy Law" in first["system"]
        tool_result = FakeAnthropic.calls[1]["messages"][2]["content"][0]
        assert json.loads(tool_result["content"])["found"] is True

    def test_claude_without_connector_gets_no_tools(self, target_module, monkeypatch):
        monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=FakeAnthropic))
        FakeAnthropic.calls = [{}]  # skip the tool-use turn
        target = target_module.ExternalConnectorTarget("claude", "k", connector=False)
        rec = target._answer_sync({"id": "x", "message": "q"})
        assert rec["status"] == 200
        assert "tools" not in FakeAnthropic.calls[1]
        assert "Fuzzzy Law" not in FakeAnthropic.calls[1]["system"]

    def test_remote_mcp_mode_hands_the_url_to_claude(self, target_module, monkeypatch):
        monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=FakeAnthropic))
        monkeypatch.setenv("FL_CONNECTOR_MODE", "remote_mcp")
        FakeAnthropic.calls = [{}]
        target = target_module.ExternalConnectorTarget(
            "claude", "k", connector=True, connector_url="https://law-api.example.ge"
        )
        target._answer_sync({"id": "x", "message": "q"})
        sent = FakeAnthropic.calls[1]
        assert sent["mcp_servers"][0]["url"] == "https://law-api.example.ge/mcp"
        assert sent["tools"] == [{"type": "mcp_toolset", "mcp_server_name": "fuzzzy-law"}]
        assert "mcp-client-2025-11-20" in sent["betas"]

    def test_provider_error_is_recorded_and_key_scrubbed(self, target_module, monkeypatch):
        class Boom:
            def __init__(self, api_key, max_retries):
                raise RuntimeError(f"bad key {api_key}")

        monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Boom))
        rec = target_module.ExternalConnectorTarget("claude", "sk-secret", connector=False)._answer_sync(
            {"id": "x", "message": "q"}
        )
        assert rec["status"] == 599
        assert "sk-secret" not in rec["error"]
