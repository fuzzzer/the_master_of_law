"""Answer target: an outside AI assistant (Claude or ChatGPT's model) with or without the law connector.

Implements the scorecard's external target interface (see targets/external_connector.py on the
scorecard branch): ``info``, ``available`` and ``async answer(item) -> record``.

How the connector is offered (FL_CONNECTOR_MODE):
  client      (default) The connector's REST operations, read from its own OpenAPI document at
              <FL_CONNECTOR_URL>/api/v1/connector/openapi.json, are given to the model as tools and
              executed here over HTTP. Works against a connector on this Mac (no public URL needed);
              it is the same set of operations a custom GPT Action gets.
  remote_mcp  The provider connects to <FL_CONNECTOR_URL>/mcp itself (Claude: MCP connector beta;
              OpenAI: Responses API "mcp" tool). Needs the connector on a public HTTPS address.

With the connector the assistant gets connector/instructions/system_prompt.txt (the custom-instructions
pack); without it, a plain one-line instruction. The caller's key comes in as ``key`` (run_answers reads
FL_KEY, set inline from the keychain); it is never printed, and error texts are scrubbed of it.

Environment: FL_CONNECTOR_URL (default http://127.0.0.1:8010), FL_CONNECTOR_MODE, FL_CONNECTOR_TOKEN
(only when the connector runs in a signed-in mode), FL_CLAUDE_MODEL (default claude-opus-5-5),
FL_CLAUDE_EFFORT (default high), FL_OPENAI_MODEL (default gpt-6-astra), FL_MAX_TOOL_TURNS (default 10).
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INSTRUCTIONS = REPO / "connector" / "instructions" / "system_prompt.txt"
PLAIN_SYSTEM = "You answer questions about Georgian law. Answer in the user's language (Georgian by default)."
TOOL_RESULT_CHARS = 40_000
UA = "fuzzzy-law-scorecard/1.0 (external assistant target)"
CLAUDE_FALLBACK_BETA = "server-side-fallback-2026-07-01"
CLAUDE_MCP_BETA = "mcp-client-2025-11-20"
MCP_SERVER_NAME = "fuzzzy-law"


def tools_from_openapi(spec: dict) -> list[dict]:
    """Neutral tool list {name, description, schema, method, path, body} from the connector's OpenAPI."""
    schemas = spec.get("components", {}).get("schemas", {})

    def resolve(s: dict) -> dict:
        ref = s.get("$ref")
        return schemas[ref.rsplit("/", 1)[-1]] if ref else s

    tools = []
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            props, required, body = {}, [], False
            for p in op.get("parameters", []):
                props[p["name"]] = {k: v for k, v in resolve(p["schema"]).items() if k != "title"} | {
                    "description": p.get("description", "")}
                if p.get("required"):
                    required.append(p["name"])
            content = op.get("requestBody", {}).get("content", {}).get("application/json")
            if content:
                body = True
                s = resolve(content["schema"])
                props.update(s.get("properties", {}))
                required += s.get("required", [])
            tools.append({
                "name": op["operationId"],
                "description": " ".join(x for x in (op.get("summary"), op.get("description")) if x),
                "schema": {"type": "object", "properties": props, "required": required},
                "method": method.upper(), "path": path, "body": body,
            })
    return tools


def citations_from(tool_name: str, result: dict) -> list[dict]:
    """Articles the assistant read in full (getArticle / verifyCitation)."""
    if tool_name == "getArticle" and result.get("article"):
        a = result["article"]
        return [{"code_name": a["code_name"], "article_number": a["article_number"],
                 "paragraph": (a.get("requested_paragraph") or {}).get("number"),
                 "article_url": a["source_url"], "version_date": a.get("version_date")}]
    if tool_name == "verifyCitation" and result.get("exists"):
        return [{"code_name": result["code"], "article_number": result["article_number"],
                 "paragraph": result.get("paragraph_requested"), "article_url": result.get("source_url"),
                 "version_date": result.get("version_date")}]
    return []


class ExternalConnectorTarget:
    name = "external"

    def __init__(self, assistant: str, key: str | None, connector: bool, connector_url: str | None = None):
        self.assistant, self.key, self.connector = assistant, key, connector
        self.connector_url = (connector_url or os.environ.get("FL_CONNECTOR_URL") or "http://127.0.0.1:8010").rstrip("/")
        self.mode = os.environ.get("FL_CONNECTOR_MODE", "client")
        self.token = os.environ.get("FL_CONNECTOR_TOKEN", "")
        self.max_turns = int(os.environ.get("FL_MAX_TOOL_TURNS", "10"))
        if assistant == "claude":
            self.model = os.environ.get("FL_CLAUDE_MODEL", "claude-opus-5-5")
        else:
            self.model = os.environ.get("FL_OPENAI_MODEL", "gpt-6-astra")
        self._tools: list[dict] | None = None
        self.info = {"target": "external", "assistant": assistant, "model": self.model, "connector": connector,
                     "connector_url": self.connector_url if connector else None,
                     "connector_mode": self.mode if connector else None, "wired": True}

    @property
    def available(self) -> bool:
        return bool(self.key) and self.assistant in ("claude", "chatgpt")

    def scrub(self, text: str) -> str:
        for secret in (self.key, self.token):
            if secret:
                text = text.replace(secret, "[REDACTED]")
        return text

    # ── connector over HTTP ──────────────────────────────────

    def _http(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        url = self.connector_url + path
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        headers = {"User-Agent": UA, "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "detail": e.read().decode("utf-8", "replace")[:500]}

    def tools(self) -> list[dict]:
        if self._tools is None:
            self._tools = tools_from_openapi(self._http("GET", "/api/v1/connector/openapi.json"))
        return self._tools

    def run_tool(self, name: str, args: dict) -> dict:
        tool = next((t for t in self.tools() if t["name"] == name), None)
        if tool is None:
            return {"error": f"unknown tool {name}"}
        if tool["body"]:
            return self._http(tool["method"], tool["path"], body=args)
        return self._http(tool["method"], tool["path"], params=args)

    def system_prompt(self) -> str:
        return INSTRUCTIONS.read_text(encoding="utf-8") if self.connector else PLAIN_SYSTEM

    # ── Claude ───────────────────────────────────────────────

    def _claude(self, message: str, rec: dict) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.key, max_retries=2)
        betas = [CLAUDE_FALLBACK_BETA]
        extra: dict = {}
        if self.connector and self.mode == "remote_mcp":
            betas.append(CLAUDE_MCP_BETA)
            server = {"type": "url", "url": self.connector_url + "/mcp", "name": MCP_SERVER_NAME}
            if self.token:
                server["authorization_token"] = self.token
            extra = {"mcp_servers": [server], "tools": [{"type": "mcp_toolset", "mcp_server_name": MCP_SERVER_NAME}]}
        elif self.connector:
            extra = {"tools": [{"name": t["name"], "description": t["description"], "input_schema": t["schema"]}
                               for t in self.tools()]}
        messages: list = [{"role": "user", "content": message}]
        response = None
        for _ in range(self.max_turns):
            response = client.beta.messages.create(
                model=self.model, max_tokens=16000, system=self.system_prompt(), messages=messages,
                thinking={"type": "adaptive"}, output_config={"effort": os.environ.get("FL_CLAUDE_EFFORT", "high")},
                betas=betas, fallbacks="default", **extra)
            if response.stop_reason == "refusal":
                rec["refusal"] = True
                break
            messages.append({"role": "assistant", "content": response.content})
            rec["tool_calls"] += [b.name for b in response.content if b.type == "mcp_tool_use"]
            if response.stop_reason == "pause_turn":
                continue
            calls = [b for b in response.content if b.type == "tool_use"]
            if response.stop_reason != "tool_use" or not calls:
                break
            results = []
            for call in calls:
                rec["tool_calls"].append(call.name)
                out = self.run_tool(call.name, dict(call.input))
                rec["citations"] += citations_from(call.name, out)
                results.append({"type": "tool_result", "tool_use_id": call.id,
                                "content": json.dumps(out, ensure_ascii=False)[:TOOL_RESULT_CHARS]})
            messages.append({"role": "user", "content": results})
        rec["model_served"] = getattr(response, "model", None)
        return "".join(b.text for b in (response.content if response else []) if b.type == "text")

    # ── OpenAI (the model behind ChatGPT) ────────────────────

    def _openai(self, message: str, rec: dict) -> str:
        import openai

        client = openai.OpenAI(api_key=self.key, max_retries=2)
        tools: list = []
        if self.connector and self.mode == "remote_mcp":
            mcp = {"type": "mcp", "server_label": "fuzzzy_law", "server_url": self.connector_url + "/mcp",
                   "require_approval": "never"}
            if self.token:
                mcp["authorization"] = self.token
            tools = [mcp]
        elif self.connector:
            tools = [{"type": "function", "name": t["name"], "description": t["description"],
                      "parameters": t["schema"], "strict": False} for t in self.tools()]
        kwargs: dict = {"model": self.model, "instructions": self.system_prompt()}
        if tools:
            kwargs["tools"] = tools
        response = client.responses.create(input=message, **kwargs)
        for _ in range(self.max_turns):
            rec["tool_calls"] += [o.name for o in response.output if o.type == "mcp_call"]
            calls = [o for o in response.output if o.type == "function_call"]
            if not calls:
                break
            outputs = []
            for call in calls:
                rec["tool_calls"].append(call.name)
                out = self.run_tool(call.name, json.loads(call.arguments or "{}"))
                rec["citations"] += citations_from(call.name, out)
                outputs.append({"type": "function_call_output", "call_id": call.call_id,
                                "output": json.dumps(out, ensure_ascii=False)[:TOOL_RESULT_CHARS]})
            response = client.responses.create(previous_response_id=response.id, input=outputs, **kwargs)
        rec["model_served"] = response.model
        return response.output_text

    # ── record ───────────────────────────────────────────────

    def _answer_sync(self, item: dict) -> dict:
        rec = {"id": item["id"], "message": item["message"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "degraded": False, "degraded_events": []}
        trace = {"tool_calls": [], "citations": []}
        start = time.time()
        try:
            text = (self._claude if self.assistant == "claude" else self._openai)(item["message"], trace)
            rec.update({"status": 200, "error": None})
        except Exception as e:  # noqa: BLE001 — one bad item must not stop the run; recorded, not hidden
            status = getattr(e, "status_code", None) or 599
            rec.update({"status": status, "error": self.scrub(f"{type(e).__name__}: {e}")[:500]})
            rec["degraded"] = status == 429
            rec["degraded_events"] = ["HTTP 429"] if status == 429 else []
            text = ""
        rec["latency_s"] = round(time.time() - start, 2)
        rec["body"] = {"response": text, "citations": trace["citations"], "tool_calls": trace["tool_calls"],
                       "refusal": trace.get("refusal", False), "model_served": trace.get("model_served")}
        return rec

    async def answer(self, item: dict) -> dict:
        return await asyncio.to_thread(self._answer_sync, item)
