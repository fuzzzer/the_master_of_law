"""
Tests for the optional Anthropic Claude provider.

Every Anthropic client here is a mock: no test makes a network call, and none
needs an Anthropic key. Two properties matter most:

1. With CLAUDE_MODELS_ENABLED off (the default) nothing changes — not even a
   model id that starts with "claude-" reaches Anthropic.
2. Whoever made the request pays: the caller's own Anthropic key is used, and
   under BYOK the operator's key never stands in for a missing one.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import httpx2
import pytest
from google.genai import types

from app.config.request_context import reset_anthropic_key, set_anthropic_key
from app.integrations import claude_client as cc
from app.integrations import vertex_ai_client as vac
from app.tools.case_tools import ALWAYS_TOOLS
from app.utils.provider_errors import ProviderErrorKind, classify

CLAUDE = "claude-opus-5-5"
KEY_A = "sk-ant-api03-" + "a" * 40
KEY_B = "sk-ant-api03-" + "b" * 40


# ── Fakes ────────────────────────────────────────────────────

def text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def tool_use_block(call_id: str, name: str, args: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=call_id, name=name, input=args)


def message(*blocks: SimpleNamespace, stop_reason: str = "end_turn") -> SimpleNamespace:
    return SimpleNamespace(content=list(blocks), stop_reason=stop_reason, stop_details=None)


def fake_anthropic(*replies: SimpleNamespace) -> MagicMock:
    client = MagicMock()
    client.beta.messages.create = AsyncMock(side_effect=list(replies))
    return client


class FakeStream:
    """Stands in for the SDK's async message-stream context manager."""

    def __init__(self, chunks: list[str], final: SimpleNamespace) -> None:
        self._chunks = chunks
        self._final = final

    async def __aenter__(self) -> FakeStream:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    @property
    def text_stream(self):
        async def gen():
            for chunk in self._chunks:
                yield chunk
        return gen()

    async def get_final_message(self) -> SimpleNamespace:
        return self._final


def api_status_error(cls, status: int, msg: str, headers: dict | None = None):
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(status, headers=headers or {}, request=request)
    return cls(msg, response=response, body=None)


@pytest.fixture
def claude_on():
    with patch.object(cc.settings, "claude_models_enabled", True):
        yield


@pytest.fixture
def no_caller_key():
    token = set_anthropic_key(None)
    cc.reset_client_cache()
    yield
    reset_anthropic_key(token)
    cc.reset_client_cache()


# ── Selection: flag and model id ─────────────────────────────

class TestSelection:
    def test_flag_off_never_selects_claude(self):
        with patch.object(cc.settings, "claude_models_enabled", False):
            assert cc.is_claude_model(CLAUDE) is False
            assert cc.offered_claude_models() == []

    def test_flag_on_selects_by_model_id(self, claude_on):
        assert cc.is_claude_model(CLAUDE) is True
        assert cc.is_claude_model("gemini-3.7-flash") is False
        assert cc.is_claude_model(None) is False

    def test_offered_models_are_the_current_four(self, claude_on):
        assert cc.offered_claude_models() == [
            "claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-fable-5-1",
        ]


# ── Gemini default path is untouched ─────────────────────────

class TestGeminiPathUntouched:
    async def _generate_on(self, model: str) -> tuple[MagicMock, MagicMock]:
        genai_client = MagicMock()
        genai_client.aio.models.generate_content = AsyncMock(
            return_value=SimpleNamespace(text="OK", candidates=[]),
        )
        anthropic_factory = MagicMock()
        with patch.object(vac, "create_genai_client", return_value=genai_client), \
             patch.object(cc, "create_anthropic_client", anthropic_factory):
            await vac.VertexAIClient().generate(prompt="hi", model_name=model)
        return genai_client, anthropic_factory

    async def test_flag_off_sends_even_a_claude_id_to_gemini(self):
        with patch.object(cc.settings, "claude_models_enabled", False):
            genai_client, anthropic_factory = await self._generate_on(CLAUDE)
        genai_client.aio.models.generate_content.assert_awaited_once()
        assert genai_client.aio.models.generate_content.call_args.kwargs["model"] == CLAUDE
        anthropic_factory.assert_not_called()

    async def test_flag_on_gemini_model_stays_on_gemini(self, claude_on):
        genai_client, anthropic_factory = await self._generate_on("gemini-3.7-flash")
        genai_client.aio.models.generate_content.assert_awaited_once()
        anthropic_factory.assert_not_called()

    async def test_flag_on_gemini_chat_stays_on_gemini(self, claude_on):
        genai_client = MagicMock()
        with patch.object(vac, "create_genai_client", return_value=genai_client), \
             patch.object(cc, "create_anthropic_client") as anthropic_factory:
            chat = await vac.VertexAIClient().create_chat(model_name="gemini-3.7-flash")
        assert isinstance(chat, vac._RetryingChat)
        genai_client.aio.chats.create.assert_called_once()
        anthropic_factory.assert_not_called()


# ── Text generation ──────────────────────────────────────────

class TestGenerate:
    async def test_text_generation_on_claude(self, claude_on):
        client = fake_anthropic(message(text_block("გამარჯობა")))
        with patch.object(cc, "create_anthropic_client", return_value=client), \
             patch.object(vac, "create_genai_client") as genai_factory:
            text = await vac.VertexAIClient().generate(
                prompt="hello", system_instruction="be brief", model_name=CLAUDE,
            )
        assert text == "გამარჯობა"
        genai_factory.assert_not_called()
        request = client.beta.messages.create.call_args.kwargs
        assert request["model"] == CLAUDE
        assert request["system"] == "be brief"
        assert request["messages"] == [{"role": "user", "content": "hello"}]
        assert request["cache_control"] == {"type": "ephemeral"}
        # Current Claude models reject sampling params; thinking stays adaptive.
        assert "temperature" not in request and "top_p" not in request
        assert "thinking" not in request
        assert request["fallbacks"] == "default"
        assert request["betas"] == ["server-side-fallback-2026-07-01"]

    async def test_small_budget_gets_room_and_low_effort(self, claude_on):
        client = fake_anthropic(message(text_block("OK")))
        with patch.object(cc, "create_anthropic_client", return_value=client):
            await vac.VertexAIClient().generate(
                prompt="x", model_name="claude-haiku-5-5",
                max_output_tokens=50, thinking_budget=0,
            )
        request = client.beta.messages.create.call_args.kwargs
        assert request["max_tokens"] == cc.CLAUDE_MIN_MAX_TOKENS
        assert request["output_config"] == {"effort": "low"}
        # Haiku has no server-side fallback.
        assert "fallbacks" not in request and "betas" not in request

    async def test_generate_json_on_claude(self, claude_on):
        client = fake_anthropic(message(text_block('```json\n{"a": 1}\n```')))
        with patch.object(cc, "create_anthropic_client", return_value=client):
            result = await vac.VertexAIClient().generate_json(
                prompt="x", system_instruction="sys", model_name=CLAUDE,
            )
        assert result == {"a": 1}
        system = client.beta.messages.create.call_args.kwargs["system"]
        assert system.startswith("sys") and cc.JSON_ONLY_INSTRUCTION in system

    async def test_refusal_raises(self, claude_on):
        client = fake_anthropic(message(stop_reason="refusal"))
        with patch.object(cc, "create_anthropic_client", return_value=client), \
             pytest.raises(cc.ClaudeRefusalError):
            await vac.VertexAIClient().generate(prompt="x", model_name=CLAUDE)


# ── Streaming ────────────────────────────────────────────────

class TestStreaming:
    async def test_stream_yields_text_deltas(self, claude_on):
        client = MagicMock()
        client.beta.messages.stream = MagicMock(
            return_value=FakeStream(["ერთი ", "ორი"], message(text_block("ერთი ორი"))),
        )
        with patch.object(cc, "create_anthropic_client", return_value=client):
            chunks = [
                c async for c in vac.VertexAIClient().generate_stream(
                    prompt="x", system_instruction="s", model_name=CLAUDE,
                )
            ]
        assert chunks == ["ერთი ", "ორი"]
        assert client.beta.messages.stream.call_args.kwargs["system"] == "s"

    async def test_refusal_after_stream_raises(self, claude_on):
        client = MagicMock()
        client.beta.messages.stream = MagicMock(
            return_value=FakeStream(["part"], message(stop_reason="refusal")),
        )
        with patch.object(cc, "create_anthropic_client", return_value=client), \
             pytest.raises(cc.ClaudeRefusalError):
            async for _ in vac.VertexAIClient().generate_stream(prompt="x", model_name=CLAUDE):
                pass


# ── Tool use ─────────────────────────────────────────────────

class TestToolTranslation:
    def test_always_tools_translate_with_schemas(self):
        tools = {t["name"]: t for t in cc.tools_to_anthropic(ALWAYS_TOOLS)}
        assert set(tools) == {"search_law", "get_article", "browse_code"}
        schema = tools["get_article"]["input_schema"]
        assert schema["type"] == "object"
        assert {"code", "article", "paragraph"} <= set(schema["properties"])
        assert schema["properties"]["article"]["type"] == "string"
        assert "required" in schema

    def test_nested_array_schema(self):
        from app.tools.case_tools import CREATE_CASE_DECLARATION

        tool = cc.tools_to_anthropic([types.Tool(function_declarations=[CREATE_CASE_DECLARATION])])
        facts = tool[0]["input_schema"]["properties"]["initial_facts"]
        assert facts["type"] == "array"
        assert facts["items"]["type"] == "object"
        assert facts["items"]["properties"]["classification"]["enum"]

    def test_history_maps_model_to_assistant(self):
        history = [
            types.Content(role="user", parts=[types.Part.from_text(text="q")]),
            types.Content(role="model", parts=[types.Part.from_text(text="a")]),
        ]
        assert cc.history_to_messages(history) == [
            {"role": "user", "content": "q"},
            {"role": "assistant", "content": "a"},
        ]


class TestToolLoop:
    async def test_pipeline_tool_loop_runs_get_article_on_claude(self, claude_on):
        """The unchanged phase-2 loop grounds through get_article on Claude."""
        from app.services import agent_pipeline_service as aps

        first = message(
            text_block("ვამოწმებ მუხლს."),
            tool_use_block("toolu_1", "get_article", {"code": "labor", "article": "37"}),
            tool_use_block("toolu_2", "browse_code", {"code": "labor"}),
            stop_reason="tool_use",
        )
        second = message(text_block("შრომის კოდექსის 37-ე მუხლის მიხედვით..."))
        client = fake_anthropic(first, second)

        pipeline = aps.AgentPipelineService(
            gemini=vac.VertexAIClient(), rag=MagicMock(), citation_svc=MagicMock(),
        )
        with patch.object(cc, "create_anthropic_client", return_value=client), \
             patch.object(aps, "strong_model", AsyncMock(return_value=CLAUDE)), \
             patch.object(pipeline, "_handle_get_article",
                          AsyncMock(return_value={"found": True, "article": "37"})), \
             patch.object(pipeline, "_handle_browse_code",
                          AsyncMock(return_value={"found": True, "chapters": []})):
            text, _chunks, tool_results, _ = await pipeline._phase_2_execute(
                plan=aps.PipelinePlan(needs_rag=False),
                user_message="რა წერია შრომის კოდექსის 37-ე მუხლში?",
                system_prompt="system",
                history=[],
                collections=None,
                case_file_id=None,
                user_id=None,
                conversation_id=None,
                db=None,
                redis_client=None,
                is_case_chat=False,
            )

        assert text == "შრომის კოდექსის 37-ე მუხლის მიხედვით..."
        assert [t.tool_name for t in tool_results] == ["get_article", "browse_code"]

        first_call, second_call = client.beta.messages.create.call_args_list
        tool_names = {t["name"] for t in first_call.kwargs["tools"]}
        assert {"get_article", "browse_code", "search_law"} <= tool_names

        turns = second_call.kwargs["messages"]
        # Claude's own content (text + tool_use) goes back verbatim...
        assert turns[1] == {"role": "assistant", "content": first.content}
        # ...and both results come back in ONE user turn, matched by id.
        results = turns[2]["content"]
        assert turns[2]["role"] == "user"
        assert [r["tool_use_id"] for r in results] == ["toolu_1", "toolu_2"]
        assert all(r["type"] == "tool_result" for r in results)
        assert '"article": "37"' in results[0]["content"]

    async def test_truncated_tool_call_is_not_run(self, claude_on):
        reply = message(
            tool_use_block("toolu_1", "get_article", {"code": "lab"}),
            stop_reason="max_tokens",
        )
        chat = cc.ClaudeChat(
            client=fake_anthropic(reply), model=CLAUDE, system=None, tools=[],
            history=[], max_output_tokens=100, thinking_budget=None,
        )
        response = await chat.send_message("q")
        assert not response.function_calls

    async def test_answer_without_open_call_is_an_error(self, claude_on):
        chat = cc.ClaudeChat(
            client=fake_anthropic(), model=CLAUDE, system=None, tools=[],
            history=[], max_output_tokens=100, thinking_budget=None,
        )
        with pytest.raises(ValueError):
            await chat.send_message([types.Part.from_function_response(name="x", response={})])


# ── Key selection (BYOK) ─────────────────────────────────────

class TestKeySelection:
    def test_caller_key_is_used(self, no_caller_key):
        set_anthropic_key(KEY_A)
        with patch.object(cc.anthropic, "AsyncAnthropic") as ctor:
            cc.create_anthropic_client()
        ctor.assert_called_once_with(api_key=KEY_A)

    def test_two_callers_get_two_clients(self, no_caller_key):
        with patch.object(cc.anthropic, "AsyncAnthropic",
                          side_effect=lambda **kw: MagicMock(**kw)) as ctor:
            set_anthropic_key(KEY_A)
            first = cc.create_anthropic_client()
            set_anthropic_key(KEY_B)
            second = cc.create_anthropic_client()
        assert first is not second
        assert [c.kwargs["api_key"] for c in ctor.call_args_list] == [KEY_A, KEY_B]

    def test_server_key_when_byok_is_off(self, no_caller_key):
        with patch.object(cc.settings, "anthropic_api_key", KEY_B), \
             patch.object(cc.settings, "byok_required", False), \
             patch.object(cc.anthropic, "AsyncAnthropic") as ctor:
            cc.create_anthropic_client()
        ctor.assert_called_once_with(api_key=KEY_B)

    def test_server_key_never_pays_under_byok(self, no_caller_key):
        with patch.object(cc.settings, "anthropic_api_key", KEY_B), \
             patch.object(cc.settings, "byok_required", True), \
             patch.object(cc.anthropic, "AsyncAnthropic") as ctor, \
             pytest.raises(cc.ClaudeKeyMissingError):
            cc.create_anthropic_client()
        ctor.assert_not_called()

    def test_no_key_at_all_is_a_clear_error(self, no_caller_key):
        with patch.object(cc.settings, "anthropic_api_key", ""), \
             pytest.raises(cc.ClaudeKeyMissingError) as info:
            cc.create_anthropic_client()
        err = classify(info.value)
        assert (err.status_code, err.error_code) == (401, "anthropic_key_required")

    def test_key_shape(self):
        assert cc.looks_like_anthropic_key(KEY_A)
        assert not cc.looks_like_anthropic_key("AIza" + "A" * 35)
        assert not cc.looks_like_anthropic_key("sk-ant-short")
        assert not cc.looks_like_anthropic_key(KEY_A + " ")


# ── Error mapping ────────────────────────────────────────────

class TestErrorMapping:
    def test_auth_error_is_the_callers_key(self):
        err = classify(api_status_error(anthropic.AuthenticationError, 401, "invalid x-api-key"))
        assert err.kind is ProviderErrorKind.INVALID_KEY
        assert (err.status_code, err.error_code) == (401, "anthropic_key_invalid")
        assert "Anthropic" in err.message_ka

    def test_permission_denied_is_the_callers_key(self):
        err = classify(api_status_error(anthropic.PermissionDeniedError, 403, "denied"))
        assert err.error_code == "anthropic_key_invalid"

    def test_rate_limit_carries_retry_after(self):
        exc = api_status_error(anthropic.RateLimitError, 429, "rate_limit_error",
                               headers={"retry-after": "30"})
        err = classify(exc)
        assert err.kind is ProviderErrorKind.QUOTA_EXHAUSTED
        assert (err.status_code, err.retry_after_s) == (503, 30)
        assert "30" in err.message_ka

    def test_low_credit_balance_is_quota(self):
        exc = api_status_error(anthropic.BadRequestError, 400,
                               "Your credit balance is too low to access the Anthropic API.")
        assert classify(exc).kind is ProviderErrorKind.QUOTA_EXHAUSTED

    def test_overload_is_unavailable(self):
        err = classify(api_status_error(anthropic.OverloadedError, 529, "Overloaded"))
        assert err.kind is ProviderErrorKind.PROVIDER_UNAVAILABLE
        assert (err.status_code, err.error_code) == (503, "ai_unavailable")

    def test_server_error_and_timeout_are_unavailable(self):
        assert classify(api_status_error(anthropic.InternalServerError, 500, "boom")).kind \
            is ProviderErrorKind.PROVIDER_UNAVAILABLE
        timeout = anthropic.APITimeoutError(
            request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"),
        )
        assert classify(timeout).kind is ProviderErrorKind.PROVIDER_UNAVAILABLE

    def test_context_too_long(self):
        exc = api_status_error(anthropic.BadRequestError, 400,
                               "prompt is too long: 1200000 tokens > 1000000 maximum")
        err = classify(exc)
        assert err.kind is ProviderErrorKind.CONTEXT_TOO_LONG
        assert (err.status_code, err.error_code) == (400, "ai_context_too_long")

    def test_refusal(self):
        err = classify(cc.ClaudeRefusalError("cyber"))
        assert (err.status_code, err.error_code) == (422, "ai_refused")

    def test_other_claude_bad_request_is_a_bug(self):
        """A malformed request is our defect, not a soothing 'try later'."""
        err = classify(api_status_error(anthropic.BadRequestError, 400, "messages: invalid"))
        assert err.kind is ProviderErrorKind.UNKNOWN
        assert err.status_code == 500

    def test_gemini_errors_classify_as_before(self):
        err = classify(RuntimeError("429 RESOURCE_EXHAUSTED retryDelay: '20s'"))
        assert (err.error_code, err.retry_after_s) == ("ai_quota_exhausted", 20)


# ── HTTP surface: middleware, key check, model list ──────────

class TestHttpSurface:
    def _client(self):
        from fastapi.testclient import TestClient

        from app.main import create_app

        return TestClient(create_app())

    @pytest.fixture(autouse=True)
    def _byok_off(self):
        with patch.object(cc.settings, "byok_required", False):
            yield

    def test_malformed_anthropic_key_is_rejected(self, claude_on):
        r = self._client().get(
            "/api/v1/api-keys/validate-anthropic", headers={"X-Anthropic-Key": "nope"},
        )
        assert r.status_code == 401
        assert r.json()["error"] == "anthropic_key_invalid"

    def test_header_is_ignored_while_flag_is_off(self):
        with patch.object(cc.settings, "claude_models_enabled", False):
            r = self._client().get(
                "/api/v1/api-keys/validate-anthropic", headers={"X-Anthropic-Key": "nope"},
            )
        assert r.status_code == 404

    def test_validate_without_key(self, claude_on):
        r = self._client().get("/api/v1/api-keys/validate-anthropic")
        assert r.status_code == 401
        assert r.json()["error"] == "anthropic_key_required"

    def test_validate_binds_the_callers_key(self, claude_on):
        seen: list[str | None] = []

        async def count():
            from app.config.request_context import get_anthropic_key

            seen.append(get_anthropic_key())
            return 7

        with patch.object(cc, "count_available_models", count):
            r = self._client().get(
                "/api/v1/api-keys/validate-anthropic", headers={"X-Anthropic-Key": KEY_A},
            )
        assert r.status_code == 200
        assert r.json() == {"valid": True, "models_available": 7}
        assert seen == [KEY_A]

    def test_validate_rejected_key(self, claude_on):
        async def count():
            raise api_status_error(anthropic.AuthenticationError, 401, "invalid x-api-key")

        with patch.object(cc, "count_available_models", count):
            r = self._client().get(
                "/api/v1/api-keys/validate-anthropic", headers={"X-Anthropic-Key": KEY_A},
            )
        assert r.status_code == 401
        assert r.json()["error"] == "anthropic_key_invalid"


class TestModelList:
    def _gemini_listing(self, names: list[str]) -> MagicMock:
        async def pager():
            for name in names:
                yield SimpleNamespace(name=f"models/{name}", supported_actions=None)

        client = MagicMock()
        client.aio.models.list = AsyncMock(return_value=pager())
        return client

    async def test_flag_off_lists_gemini_only(self):
        from app.routes import model_router

        with patch.object(cc.settings, "claude_models_enabled", False), \
             patch.object(vac, "create_genai_client",
                          return_value=self._gemini_listing(["gemini-3.7-flash"])):
            assert await model_router._available_models() == ["gemini-3.7-flash"]

    async def test_flag_on_appends_claude(self, claude_on):
        from app.routes import model_router

        with patch.object(vac, "create_genai_client",
                          return_value=self._gemini_listing(["gemini-3.7-flash"])):
            names = await model_router._available_models()
        assert names == ["gemini-3.7-flash", *cc.CLAUDE_MODELS]

    async def test_gemini_outage_still_yields_empty(self, claude_on):
        """An empty list is what tells validation to skip the unknown check."""
        from app.routes import model_router

        with patch.object(vac, "create_genai_client", side_effect=RuntimeError("503")):
            assert await model_router._available_models() == []


def test_anthropic_key_is_redacted_from_logs():
    from app.utils.logger import redact_secrets

    line = f"GET /ws?anthropic_api_key={KEY_A} header {KEY_B}"
    out = redact_secrets(line)
    assert KEY_A not in out and KEY_B not in out
