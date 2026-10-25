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

REPO = Path(__file__).resolve().parents[2]
TARGET_FILE = REPO / "eval" / "scorecard" / "targets" / "external_ai.py"


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


USAGE = types.SimpleNamespace(input_tokens=10_000, output_tokens=1_000)


@pytest.fixture(autouse=True)
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("FL_LEDGER", str(path))
    for var in ("FL_CLAUDE_MODEL", "FL_CONNECTOR_MODE", "FL_MAX_USD", "FL_RUN_MAX_USD"):
        monkeypatch.delenv(var, raising=False)
    return path


def _install_fake_anthropic(monkeypatch):
    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=FakeAnthropic))


class FakeAnthropic:
    """Asks for getArticle once, then answers."""

    calls: list[dict] = []

    def __init__(self, api_key, max_retries):
        self.beta = types.SimpleNamespace(messages=types.SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        FakeAnthropic.calls.append(kwargs)
        if len(FakeAnthropic.calls) == 1:
            return _block(stop_reason="tool_use", model=kwargs["model"], usage=USAGE, content=[
                _block(type="tool_use", id="t1", name="getArticle",
                       input={"code": "civil_procedure_code", "article": "369"}),
            ])
        return _block(stop_reason="end_turn", model=kwargs["model"], usage=USAGE, content=[
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
        _install_fake_anthropic(monkeypatch)
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
        assert first["model"] == "claude-haiku-5-5"  # cheapest by default (owner's cap)
        assert "fallbacks" not in first  # Haiku has no server-side fallback
        assert "Fuzzzy Law" in first["system"]
        tool_result = FakeAnthropic.calls[1]["messages"][2]["content"][0]
        assert json.loads(tool_result["content"])["found"] is True

    def test_claude_without_connector_gets_no_tools(self, target_module, monkeypatch):
        _install_fake_anthropic(monkeypatch)
        FakeAnthropic.calls = [{}]  # skip the tool-use turn
        target = target_module.ExternalConnectorTarget("claude", "k", connector=False)
        rec = target._answer_sync({"id": "x", "message": "q"})
        assert rec["status"] == 200
        assert "tools" not in FakeAnthropic.calls[1]
        assert "Fuzzzy Law" not in FakeAnthropic.calls[1]["system"]

    def test_remote_mcp_mode_hands_the_url_to_claude(self, target_module, monkeypatch):
        _install_fake_anthropic(monkeypatch)
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
        target = target_module.ExternalConnectorTarget("claude", "sk-secret", connector=False)
        rec = target._answer_sync({"id": "x", "message": "q"})
        assert rec["status"] == 599
        assert "sk-secret" not in rec["error"]


class TestCostCap:
    def _fake(self, monkeypatch):
        _install_fake_anthropic(monkeypatch)
        FakeAnthropic.calls = [{}]

    def test_usage_is_priced_and_written_to_the_ledger(self, target_module, ledger, monkeypatch):
        self._fake(monkeypatch)
        rec = target_module.ExternalConnectorTarget("claude", "k", connector=False)._answer_sync(
            {"id": "item-1", "message": "q"}
        )
        # 10,000 in x $0.10/M + 1,000 out x $0.50/M
        assert rec["body"]["usage"] == {"in_tokens": 10_000, "out_tokens": 1_000, "usd": 0.0015}
        line = json.loads(ledger.read_text().splitlines()[-1])
        assert line["usd"] == 0.0015 and line["in_tokens"] == 10_000 and line["item"] == "item-1"

    def test_no_call_once_the_night_total_reaches_the_cap(self, target_module, ledger, monkeypatch):
        self._fake(monkeypatch)
        ledger.write_text(json.dumps({"worker": "scorecard", "usd": 8.0}) + "\n")
        rec = target_module.ExternalConnectorTarget("claude", "k", connector=False)._answer_sync(
            {"id": "x", "message": "q"}
        )
        assert rec["status"] == 402 and "cost cap" in rec["error"]
        assert FakeAnthropic.calls == [{}]  # nothing was sent

    def test_per_run_cap(self, target_module, monkeypatch):
        self._fake(monkeypatch)
        monkeypatch.setenv("FL_RUN_MAX_USD", "0.002")
        target = target_module.ExternalConnectorTarget("claude", "k", connector=False)
        assert target._answer_sync({"id": "a", "message": "q"})["status"] == 200
        FakeAnthropic.calls = [{}]
        assert target._answer_sync({"id": "b", "message": "q"})["status"] == 200
        FakeAnthropic.calls = [{}]
        assert target._answer_sync({"id": "c", "message": "q"})["status"] == 402

    def test_unpriced_models_are_not_run(self, target_module, monkeypatch):
        monkeypatch.delenv("FL_OPENAI_PRICE_IN", raising=False)
        assert not target_module.ExternalConnectorTarget("chatgpt", "k", connector=True).available
        monkeypatch.setenv("FL_CLAUDE_MODEL", "claude-unknown-9")
        assert not target_module.ExternalConnectorTarget("claude", "k", connector=True).available

    def test_bigger_claude_models_get_the_refusal_fallback(self, target_module, monkeypatch):
        self._fake(monkeypatch)
        monkeypatch.setenv("FL_CLAUDE_MODEL", "claude-opus-5-5")
        target_module.ExternalConnectorTarget("claude", "k", connector=False)._answer_sync(
            {"id": "x", "message": "q"}
        )
        assert FakeAnthropic.calls[1]["fallbacks"] == "default"
