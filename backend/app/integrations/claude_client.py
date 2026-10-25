"""
Claude client — runs a tier on Anthropic Claude when its model id says so.

Gemini stays the default and the only provider unless CLAUDE_MODELS_ENABLED
is on. With it on, any tier whose model id starts with ``claude-`` (from the
caller's X-Model-Strong / X-Model-Cheap headers, the admin default or the
environment) is served here instead of by Gemini. Embeddings never come here:
Claude has no embedding model and the corpus vectors are Gemini's.

The pipeline was written against google-genai objects (chat sessions, Parts,
function calls). Rather than fork it, this module speaks that dialect at its
edge: Gemini tool declarations are translated to Anthropic tools on the way
in, and Claude's replies are handed back as ``GenerateContentResponse``
objects, so the tool loop in agent_pipeline_service runs unchanged.

Every Anthropic client comes from ``create_anthropic_client()``, the one place
that reads the caller's Anthropic key — the same rule as create_genai_client.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from functools import lru_cache

import anthropic
from anthropic.types.beta import (
    BetaContentBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaToolParam,
    BetaToolResultBlockParam,
)
from google.genai import types

from app.config.request_context import get_anthropic_key
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# The models offered in the picker when CLAUDE_MODELS_ENABLED is on. A fixed
# list, unlike Gemini's: listing Anthropic's models needs the caller's key,
# and the picker must work before the caller has added one.
CLAUDE_MODELS = (
    "claude-opus-5-5",
    "claude-sonnet-5-5",
    "claude-haiku-5-5",
    "claude-fable-5-1",
)
CLAUDE_MODEL_PREFIX = "claude-"

# On a policy decline these models can re-run the request on a fallback model
# inside the same call. Haiku has no server-side fallback.
_FALLBACK_MODELS = frozenset({"claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1"})
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

# Thinking cannot be switched off on the current Claude models, and thinking
# tokens are drawn from max_tokens — the same trap _apply_thinking documents
# for Gemini. Small budgets (the guardrail asks for 50) would come back empty,
# so every call gets at least this much room; the prompt keeps answers short.
CLAUDE_MIN_MAX_TOKENS = 4096

_ANTHROPIC_KEY_PREFIX = "sk-ant-"
_ANTHROPIC_KEY_MIN_LEN = 20

# Claude has no response_mime_type switch; the existing JSON parsers already
# tolerate a fenced block, so an instruction is enough.
JSON_ONLY_INSTRUCTION = (
    "Respond with one JSON value only: no prose before or after it, no code fences."
)

BYOK_CLIENT_CACHE_SIZE = 64


class ClaudeKeyMissingError(Exception):
    """A Claude model was selected but nobody supplied an Anthropic key."""


class ClaudeRefusalError(Exception):
    """Claude declined the request (stop_reason "refusal") after any fallback."""

    def __init__(self, category: str | None) -> None:
        super().__init__(f"Claude declined the request (category={category})")
        self.category = category


def is_claude_model(model: str | None) -> bool:
    """True when this model id should be served by Anthropic.

    False whenever the flag is off, so a deployment that never enables Claude
    sends every model id to Gemini exactly as before.
    """
    return bool(
        settings.claude_models_enabled and model and model.startswith(CLAUDE_MODEL_PREFIX)
    )


def offered_claude_models() -> list[str]:
    """Claude models to list in the picker; empty while the flag is off."""
    return list(CLAUDE_MODELS) if settings.claude_models_enabled else []


def looks_like_anthropic_key(key: str) -> bool:
    """Shape check only — proves nothing about whether the key still works."""
    return (
        key.startswith(_ANTHROPIC_KEY_PREFIX)
        and len(key) >= _ANTHROPIC_KEY_MIN_LEN
        and key.isascii()
        and not any(c.isspace() for c in key)
    )


@lru_cache(maxsize=BYOK_CLIENT_CACHE_SIZE)
def _client_for_key(api_key: str) -> anthropic.AsyncAnthropic:
    """One reusable client (and connection pool) per distinct key."""
    return anthropic.AsyncAnthropic(api_key=api_key)


def create_anthropic_client() -> anthropic.AsyncAnthropic:
    """An Anthropic client for whoever is paying for this request.

    1. The caller's own key from the request context.
    2. ANTHROPIC_API_KEY from the environment — only when BYOK is off. Under
       BYOK every caller pays for their own calls; falling back to the
       operator's key there would bill the operator for user traffic.
    3. Neither → ClaudeKeyMissingError, which provider_errors turns into a
       message telling the user to add a key.

    The key is always passed explicitly, so the SDK never falls back to an
    ambient credential (environment, CLI profile) on its own.
    """
    caller_key = get_anthropic_key()
    if caller_key:
        return _client_for_key(caller_key)
    if settings.anthropic_api_key and not settings.byok_required:
        return _client_for_key(settings.anthropic_api_key)
    raise ClaudeKeyMissingError("No Anthropic API key for this request")


def reset_client_cache() -> None:
    """Drop cached clients, so the next call rebuilds from current config."""
    _client_for_key.cache_clear()


async def count_available_models() -> int:
    """How many models the current key can see. Free: no tokens, no quota."""
    client = create_anthropic_client()
    count = 0
    async for _ in client.models.list():
        count += 1
    return count


# ── Translation: google-genai shapes ⇄ Anthropic shapes ─────


def schema_to_json_schema(schema: types.Schema | None) -> dict[str, object]:
    """Translate a Gemini ``Schema`` into the JSON Schema Anthropic expects."""
    if schema is None:
        return {"type": "object", "properties": {}}
    out: dict[str, object] = {}
    if schema.type is not None:
        out["type"] = schema.type.value.lower()
    if schema.description:
        out["description"] = schema.description
    if schema.enum:
        out["enum"] = list(schema.enum)
    if schema.properties is not None:
        out["properties"] = {
            name: schema_to_json_schema(prop) for name, prop in schema.properties.items()
        }
    if schema.required:
        out["required"] = list(schema.required)
    if schema.items is not None:
        out["items"] = schema_to_json_schema(schema.items)
    return out


def tools_to_anthropic(tools: list[types.Tool] | None) -> list[BetaToolParam]:
    """Gemini tool declarations → Anthropic tool definitions, same names."""
    out: list[BetaToolParam] = []
    for tool in tools or []:
        for decl in tool.function_declarations or []:
            out.append({
                "name": decl.name,
                "description": decl.description or "",
                "input_schema": schema_to_json_schema(decl.parameters),
            })
    return out


def history_to_messages(history: list[types.Content] | None) -> list[BetaMessageParam]:
    """Gemini chat history (role user/model) → Anthropic messages."""
    messages: list[BetaMessageParam] = []
    for content in history or []:
        text = "".join(p.text for p in (content.parts or []) if p.text)
        role = "assistant" if content.role == "model" else "user"
        messages.append({"role": role, "content": text})
    return messages


def to_genai_response(message: BetaMessage) -> types.GenerateContentResponse:
    """A Claude reply in the shape the pipeline already reads.

    Tool calls are surfaced only when Claude stopped to call them. A tool_use
    cut off by max_tokens may carry partial input, and running it would act
    on arguments Claude never finished writing.
    """
    parts: list[types.Part] = []
    for block in message.content:
        if block.type == "text" and block.text:
            parts.append(types.Part(text=block.text))
        elif block.type == "tool_use" and message.stop_reason == "tool_use":
            parts.append(types.Part(function_call=types.FunctionCall(
                id=block.id, name=block.name, args=dict(block.input or {}),
            )))
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts))],
    )


def _raise_on_refusal(message: BetaMessage) -> None:
    if message.stop_reason == "refusal":
        details = getattr(message, "stop_details", None)
        raise ClaudeRefusalError(getattr(details, "category", None))


def _text_of(message: BetaMessage) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def _system_prompt(system_instruction: str | None, json_output: bool) -> str | None:
    if not json_output:
        return system_instruction
    if not system_instruction:
        return JSON_ONLY_INSTRUCTION
    return f"{system_instruction}\n\n{JSON_ONLY_INSTRUCTION}"


def build_request(
    *,
    model: str,
    messages: list[BetaMessageParam],
    system: str | None,
    max_output_tokens: int,
    thinking_budget: int | None = None,
    tools: list[BetaToolParam] | None = None,
) -> dict[str, object]:
    """Keyword arguments for ``client.beta.messages.create`` / ``.stream``.

    temperature / top_p are deliberately not sent: the current Claude models
    reject non-default sampling values with a 400. ``thinking`` is left out
    too (adaptive is the default and cannot be disabled); a Gemini caller's
    thinking_budget=0 — "mechanical call, don't reason" — becomes low effort.
    """
    request: dict[str, object] = {
        "model": model,
        "max_tokens": max(max_output_tokens, CLAUDE_MIN_MAX_TOKENS),
        "messages": messages,
        # Caches the stable prefix (tools, system prompt, earlier tool turns),
        # which the tool loop re-sends on every iteration.
        "cache_control": {"type": "ephemeral"},
    }
    if system:
        request["system"] = system
    if tools:
        request["tools"] = tools
    if thinking_budget == 0:
        request["output_config"] = {"effort": "low"}
    if model in _FALLBACK_MODELS:
        request["betas"] = [_FALLBACK_BETA]
        request["fallbacks"] = "default"
    return request


# ── Chat session (tool loop) ─────────────────────────────────


class ClaudeChat:
    """A multi-turn Claude session with the interface of the Gemini AsyncChat.

    ``send_message`` takes what the pipeline sends Gemini — a string, or the
    list of ``Part.from_function_response`` replies to the previous turn's
    calls — and returns a ``GenerateContentResponse``. Claude's own content
    blocks (thinking included) are kept verbatim in the history, as the API
    requires for tool use on the current models.
    """

    def __init__(
        self,
        *,
        client: anthropic.AsyncAnthropic,
        model: str,
        system: str | None,
        tools: list[BetaToolParam],
        history: list[BetaMessageParam],
        max_output_tokens: int,
        thinking_budget: int | None,
    ) -> None:
        self._client = client
        self._model = model
        self._system = system
        self._tools = tools
        self._messages = history
        self._max_output_tokens = max_output_tokens
        self._thinking_budget = thinking_budget
        self._pending_calls: list[tuple[str, str]] = []  # (tool_use_id, name)

    async def send_message(self, message: str | list[types.Part]) -> types.GenerateContentResponse:
        """Send one user turn (text or tool results) and return Claude's reply."""
        turn = [*self._messages, {"role": "user", "content": self._user_content(message)}]
        reply = await self._client.beta.messages.create(**build_request(
            model=self._model,
            messages=turn,
            system=self._system,
            max_output_tokens=self._max_output_tokens,
            thinking_budget=self._thinking_budget,
            tools=self._tools,
        ))
        _raise_on_refusal(reply)
        self._messages = [*turn, {"role": "assistant", "content": reply.content}]
        self._pending_calls = (
            [(b.id, b.name) for b in reply.content if b.type == "tool_use"]
            if reply.stop_reason == "tool_use" else []
        )
        return to_genai_response(reply)

    def _user_content(self, message: str | list[types.Part]) -> str | list[BetaContentBlockParam]:
        if isinstance(message, str):
            return message
        blocks: list[BetaContentBlockParam] = []
        for part in message:
            if part.function_response is not None:
                blocks.append(self._tool_result(part.function_response))
            elif part.text:
                blocks.append({"type": "text", "text": part.text})
        return blocks

    def _tool_result(self, response: types.FunctionResponse) -> BetaToolResultBlockParam:
        """Pair a function response with the tool_use it answers.

        ``Part.from_function_response`` carries the tool name but no call id,
        so replies are matched to the open calls by name, in order — the
        pipeline answers every call of a turn, in the order it received them.
        """
        tool_use_id = response.id or self._take_pending(response.name)
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": json.dumps(response.response or {}, ensure_ascii=False, default=str),
        }

    def _take_pending(self, name: str | None) -> str:
        for index, (call_id, call_name) in enumerate(self._pending_calls):
            if call_name == name:
                del self._pending_calls[index]
                return call_id
        raise ValueError(f"No open Claude tool call named {name!r} to answer")


# ── Entry points used by VertexAIClient ──────────────────────


async def claude_generate(
    *,
    prompt: str,
    model_name: str,
    system_instruction: str | None = None,
    max_output_tokens: int,
    json_output: bool = False,
    thinking_budget: int | None = None,
) -> str:
    """One-shot text generation. Returns the text of Claude's reply."""
    client = create_anthropic_client()
    reply = await client.beta.messages.create(**build_request(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        system=_system_prompt(system_instruction, json_output),
        max_output_tokens=max_output_tokens,
        thinking_budget=thinking_budget,
    ))
    _raise_on_refusal(reply)
    text = _text_of(reply)
    if not text:
        logger.warning("claude_empty_response", model=model_name, stop_reason=reply.stop_reason)
    return text


async def claude_generate_stream(
    *,
    prompt: str,
    model_name: str,
    system_instruction: str | None = None,
    max_output_tokens: int,
) -> AsyncIterator[str]:
    """Stream text deltas as Claude writes them."""
    client = create_anthropic_client()
    request = build_request(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        system=system_instruction,
        max_output_tokens=max_output_tokens,
    )
    async with client.beta.messages.stream(**request) as stream:
        async for text in stream.text_stream:
            yield text
        final = await stream.get_final_message()
    _raise_on_refusal(final)


def claude_create_chat(
    *,
    model_name: str,
    history: list[types.Content] | None = None,
    system_instruction: str | None = None,
    tools: list[types.Tool] | None = None,
    max_output_tokens: int,
    json_output: bool = False,
    thinking_budget: int | None = None,
) -> ClaudeChat:
    """A chat session that the Gemini tool loop can drive unchanged."""
    return ClaudeChat(
        client=create_anthropic_client(),
        model=model_name,
        system=_system_prompt(system_instruction, json_output),
        tools=tools_to_anthropic(tools),
        history=history_to_messages(history),
        max_output_tokens=max_output_tokens,
        thinking_budget=thinking_budget,
    )
