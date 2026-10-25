"""
MCP protocol tests for the law connector, using the official MCP Python SDK client.

In-process: the SDK's ``Client`` connects straight to the server object.
Over HTTP: JSON-RPC posts to /mcp on the app with the connector enabled,
which is how ChatGPT and Claude reach it.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from mcp import Client

from app.config.settings import settings
from app.routes.connector_mcp import TOOL_DESCRIPTIONS, build_connector_mcp_server

EXPECTED_TOOLS = {
    "list_codes", "search_law", "get_article", "browse_code",
    "find_court_practice", "verify_citation", "search", "fetch",
}
GEORGIAN = range(0x10D0, 0x1100)


def _has_georgian(text: str) -> bool:
    return any(ord(ch) in GEORGIAN for ch in text)


@pytest.fixture
def mcp_server(connector_service):
    return build_connector_mcp_server(connector_service)


class TestListTools:
    async def test_all_tools_listed_read_only_and_bilingual(self, mcp_server):
        async with Client(mcp_server) as client:
            tools = (await client.list_tools()).tools
        assert {t.name for t in tools} == EXPECTED_TOOLS
        for tool in tools:
            assert tool.annotations.read_only_hint is True
            assert tool.annotations.destructive_hint is False
            assert tool.output_schema, tool.name
            assert tool.description == TOOL_DESCRIPTIONS[tool.name]
            assert _has_georgian(tool.description), tool.name

    async def test_server_instructions_carry_the_grounding_rules(self, mcp_server):
        async with Client(mcp_server) as client:
            instructions = client.instructions
        assert "never invent" in instructions
        assert "get_article" in instructions


class TestCallTool:
    async def _call(self, server, name, args):
        async with Client(server) as client:
            result = await client.call_tool(name, args)
        assert not result.is_error, result.content
        # ChatGPT reads the JSON text copy; both must agree.
        assert json.loads(result.content[0].text) == result.structured_content
        return result.structured_content

    async def test_list_codes(self, mcp_server):
        data = await self._call(mcp_server, "list_codes", {})
        assert {c["code"] for c in data["codes"]} >= {"civil_code", "labour_code"}

    async def test_search_law(self, mcp_server):
        data = await self._call(mcp_server, "search_law", {"query": "სააპელაციო საჩივრის ვადა"})
        assert data["found"]
        assert data["results"][0]["source_url"].startswith("https://matsne.gov.ge/")

    async def test_get_article(self, mcp_server):
        data = await self._call(mcp_server, "get_article", {"code": "civil_code", "article": "138"})
        assert data["article"]["article_number"] == "მუხლი 138"

    async def test_browse_code(self, mcp_server):
        data = await self._call(mcp_server, "browse_code", {"code": "labour_code"})
        assert data["total_articles"] == 2

    async def test_find_court_practice(self, mcp_server):
        data = await self._call(mcp_server, "find_court_practice", {"query": "ხანდაზმულობა"})
        assert data["status"] == "source_unavailable"

    async def test_verify_citation(self, mcp_server):
        data = await self._call(mcp_server, "verify_citation", {
            "code": "civil_procedure_code", "article": "369", "claim": "ვადა 14 დღეა",
        })
        assert data["exists"] and data["lexical_check"]["numbers_not_in_text"] == ["14"]

    async def test_search_and_fetch_pair(self, mcp_server):
        hits = await self._call(mcp_server, "search", {"query": "ხანდაზმულობის ვადა"})
        first = hits["results"][0]
        assert set(first) == {"id", "title", "url"}
        doc = await self._call(mcp_server, "fetch", {"id": first["id"]})
        assert set(doc) >= {"id", "title", "text", "url"}
        assert doc["url"] == first["url"]

    async def test_fetch_unknown_id_is_a_tool_error(self, mcp_server):
        async with Client(mcp_server) as client:
            result = await client.call_tool("fetch", {"id": "article:nope:1"})
        assert result.is_error

    async def test_missing_argument_is_a_tool_error(self, mcp_server):
        async with Client(mcp_server) as client:
            result = await client.call_tool("get_article", {"code": "civil_code"})
        assert result.is_error


def _rpc(client: TestClient, method: str, params: dict, rpc_id: int = 1):
    return client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": params},
        headers={"accept": "application/json, text/event-stream"},
    )


class TestHttpEndpoint:
    def test_main_app_serves_mcp_when_enabled(self, connector_service, monkeypatch):
        monkeypatch.setattr(settings, "connector_enabled", True)
        from app.main import create_app

        with TestClient(create_app()) as client:
            listed = _rpc(client, "tools/list", {})
            assert listed.status_code == 200
            names = {t["name"] for t in listed.json()["result"]["tools"]}
            assert names == EXPECTED_TOOLS
            called = _rpc(client, "tools/call", {
                "name": "get_article", "arguments": {"code": "labour_code", "article": "48"},
            }, rpc_id=2)
            structured = called.json()["result"]["structuredContent"]
            assert structured["article"]["source_url"].endswith("#article_48")

    def test_not_mounted_when_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "connector_enabled", False)
        from app.main import create_app

        with TestClient(create_app()) as client:
            assert _rpc(client, "tools/list", {}).status_code == 404
            assert client.get("/api/v1/connector/codes").status_code == 404

    def test_standalone_app_serves_mcp(self, connector_service):
        from app.connector_main import create_connector_app

        with TestClient(create_connector_app()) as client:
            assert _rpc(client, "tools/list", {}).status_code == 200

    def test_wrong_host_rejected_when_hosts_configured(self, connector_service, monkeypatch):
        monkeypatch.setattr(settings, "connector_allowed_hosts", "law-api.example.ge")
        from app.connector_main import create_connector_app

        with TestClient(create_connector_app()) as client:
            assert _rpc(client, "tools/list", {}).status_code == 421
            ok = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
                headers={"accept": "application/json, text/event-stream",
                         "host": "law-api.example.ge"},
            )
            assert ok.status_code == 200
