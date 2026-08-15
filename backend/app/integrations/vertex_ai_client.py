"""
Gemini client — powers legal analysis, query expansion, and reranking.

Uses the ``google-genai`` SDK with Vertex AI.
Set VERTEX_AI_API_KEY in .env.
"""

from __future__ import annotations

import asyncio
import json
import random
from typing import Any

from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig

from app.config.constants import (
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_TOP_P,
)
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Transient-failure retry ──────────────────────────────────
# The provider returns 503 UNAVAILABLE ("high demand") and 429 RESOURCE_EXHAUSTED
# under load. Without a retry these do NOT surface as errors anywhere the user
# can see: every caller in this app has a defensive fallback, so a transient
# blip silently degrades output quality instead. The planner is the worst case —
# it falls back to searching the raw user message as ONE query instead of the
# 3-8 it would have planned, and the answer still comes back looking fine.
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 0.75
_TRANSIENT_MARKERS = (
    "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED",
    "500", "INTERNAL", "deadline", "DEADLINE_EXCEEDED",
)


def _is_transient(exc: Exception) -> bool:
    """True for provider-side blips that are worth retrying verbatim.

    Deliberately string-based: the SDK raises several exception types across
    the Vertex and Developer-API backends and normalising them is not worth a
    hard dependency on the SDK's private error hierarchy.
    """
    text = f"{type(exc).__name__}: {exc}"
    return any(m in text for m in _TRANSIENT_MARKERS)


async def with_retry(operation, *, what: str):
    """Await ``operation()``, retrying transient provider failures.

    Quota exhaustion (a hard 429 with no remaining budget) looks identical to
    rate limiting from here, so attempts are capped low and backoff is short:
    the goal is to ride out a spike, not to grind against a spent quota.
    """
    last: Exception | None = None
    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001 — re-raised below
            last = exc
            if not _is_transient(exc) or attempt == RETRY_MAX_ATTEMPTS - 1:
                raise
            delay = RETRY_BASE_DELAY_S * (2 ** attempt) + random.uniform(0, 0.25)
            logger.warning(
                "gemini_transient_retry",
                what=what,
                attempt=attempt + 1,
                of=RETRY_MAX_ATTEMPTS,
                delay_s=round(delay, 2),
                error=str(exc)[:200],
            )
            await asyncio.sleep(delay)
    raise last  # unreachable; keeps type checkers honest


def _apply_thinking(config: GenerateContentConfig, thinking_budget: int | None) -> None:
    """Set the thinking budget when the caller asked for one.

    WHY THIS EXISTS: on a thinking model, reasoning tokens are drawn from
    max_output_tokens. A small budget is therefore not "a short answer" — it is
    NO answer: the model spends the whole allowance thinking, returns
    finishReason=MAX_TOKENS with empty text, and any caller that treats empty
    as a soft failure silently stops working. That is exactly what happened to
    the guardrail on the 3.7-flash retarget (47 of its 50 tokens went to
    thinking). Mechanical, schema-shaped calls pass thinking_budget=0.
    """
    if thinking_budget is not None:
        config.thinking_config = ThinkingConfig(thinking_budget=thinking_budget)


def create_genai_client() -> genai.Client:
    """Create a google-genai client for the configured provider.

    GEMINI_API_KEY set → Gemini Developer API (free tier, local debugging).
    Empty (default)    → Vertex AI with ADC, exactly as before.
    """
    if settings.gemini_api_key:
        return genai.Client(api_key=settings.gemini_api_key)
    return genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


class _RetryingChat:
    """Passes ``send_message`` through with_retry; everything else delegates.

    The SDK's chat object is what appends the model's function_call and our
    function_response to history, so the tool loop must keep talking to THAT
    object — this wraps it rather than reimplementing it. A transient failure
    raises before the SDK records the turn, so a retry re-sends against
    unchanged history rather than duplicating it.
    """

    __slots__ = ("_chat", "_model")

    def __init__(self, chat: Any, model: str) -> None:
        self._chat = chat
        self._model = model

    async def send_message(self, *args: Any, **kwargs: Any) -> Any:
        return await with_retry(
            lambda: self._chat.send_message(*args, **kwargs),
            what=f"chat:{self._model}",
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)


class VertexAIClient:
    """Wrapper around google-genai SDK for Gemini (Vertex AI or Gemini API)."""

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    async def _default_model(self) -> str:
        """Model used when a caller names none.

        Resolved per call rather than pinned in __init__: this object is a
        process-lifetime singleton, so a value captured at construction would
        outlive any runtime model change and quietly serve the old model to
        whichever call sites do not pass one explicitly.
        """
        from app.services.model_config_service import strong_model

        return await strong_model()

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = create_genai_client()
            logger.info("vertex_ai_client_init", provider=settings.gemini_provider)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = GEMINI_TEMPERATURE,
        max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
        response_mime_type: str | None = None,
        model_name: str | None = None,
        thinking_budget: int | None = None,
    ) -> str:
        """Generate text using Gemini.

        thinking_budget: 0 disables reasoning tokens — see _apply_thinking.
        """
        client = self._get_client()

        config = GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=GEMINI_TOP_P,
        )

        if system_instruction:
            config.system_instruction = system_instruction

        if response_mime_type:
            config.response_mime_type = response_mime_type

        _apply_thinking(config, thinking_budget)

        model = model_name or await self._default_model()
        response = await with_retry(
            lambda: client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            ),
            what=f"generate:{model}",
        )

        # An empty body on a thinking model almost always means the output
        # budget was eaten by reasoning. Say so, rather than leaving each
        # caller to guess from a bare empty string.
        if not response.text:
            finish = None
            if response.candidates:
                finish = getattr(response.candidates[0], "finish_reason", None)
            logger.warning(
                "gemini_empty_response",
                model=model,
                finish_reason=str(finish),
                max_output_tokens=max_output_tokens,
                thinking_budget=thinking_budget,
                hint=("output budget exhausted by reasoning tokens — raise "
                      "max_output_tokens or pass thinking_budget=0")
                     if str(finish).endswith("MAX_TOKENS") else None,
            )

        return response.text

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = GEMINI_TEMPERATURE,
        max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
        model_name: str | None = None,
    ):
        """Generate text using Gemini in a stream."""
        client = self._get_client()

        config = GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=GEMINI_TOP_P,
        )

        if system_instruction:
            config.system_instruction = system_instruction

        response_stream = await client.aio.models.generate_content_stream(
            model=model_name or await self._default_model(),
            contents=prompt,
            config=config,
        )

        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    async def create_chat(
        self,
        history: list[Any] | None = None,
        system_instruction: str | None = None,
        tools: list[Any] | None = None,
        temperature: float = GEMINI_TEMPERATURE,
        max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
        model_name: str | None = None,
        response_mime_type: str | None = None,
        thinking_budget: int | None = None,
    ) -> Any:
        """Create a native multi-turn chat session.

        The returned chat object manages conversation history automatically.
        Use ``await chat.send_message(...)`` for each turn — no need to
        manually build a contents array.

        Args:
            history: Pre-existing conversation as list[types.Content].
            system_instruction: System prompt for the session.
            tools: Tool declarations available in this chat.
            temperature: Sampling temperature.
            max_output_tokens: Max output tokens per turn.
            model_name: Override the default model.
            response_mime_type: e.g. "application/json" for JSON output.

        Returns:
            An AsyncChat object (``client.aio.chats.create(...)``).
        """
        client = self._get_client()

        config = GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=GEMINI_TOP_P,
        )

        if tools:
            config.tools = tools
        if system_instruction:
            config.system_instruction = system_instruction
        if response_mime_type:
            config.response_mime_type = response_mime_type

        _apply_thinking(config, thinking_budget)

        model = model_name or await self._default_model()
        chat = client.aio.chats.create(
            model=model,
            config=config,
            history=history or [],
        )
        return _RetryingChat(chat, model)

    async def generate_with_tools(
        self,
        contents: list[Any],
        tools: list[Any],
        system_instruction: str | None = None,
        temperature: float = GEMINI_TEMPERATURE,
        max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
        model_name: str | None = None,
    ) -> Any:
        """Generate content with function calling tools.

        Returns the raw response object so callers can inspect
        function_call parts vs text parts.
        """
        client = self._get_client()

        config = GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=GEMINI_TOP_P,
            tools=tools,
        )

        if system_instruction:
            config.system_instruction = system_instruction

        return await client.aio.models.generate_content(
            model=model_name or await self._default_model(),
            contents=contents,
            config=config,
        )

    async def generate_stream_with_tools(
        self,
        contents: list[Any],
        tools: list[Any] | None = None,
        system_instruction: str | None = None,
        temperature: float = GEMINI_TEMPERATURE,
        max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
        model_name: str | None = None,
    ):
        """Stream text with optional function calling support.

        Yields text chunks as they arrive. After the stream completes,
        yields any function_call parts as dicts: {"function_call": FunctionCall}.
        The caller must handle tool execution and re-invocation.
        """
        client = self._get_client()

        config = GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=GEMINI_TOP_P,
        )
        if tools:
            config.tools = tools
        if system_instruction:
            config.system_instruction = system_instruction

        response_stream = await client.aio.models.generate_content_stream(
            model=model_name or await self._default_model(),
            contents=contents,
            config=config,
        )

        function_calls = []
        async for chunk in response_stream:
            if chunk.candidates:
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        yield {"text": part.text}
                    elif part.function_call:
                        function_calls.append(part.function_call)

        for fc in function_calls:
            yield {"function_call": fc}

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = GEMINI_TEMPERATURE,
        model_name: str | None = None,
    ) -> Any:
        """Generate JSON output from Gemini. Returns parsed JSON."""
        raw = await self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
            model_name=model_name,
        )

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        if "```json" in raw:
            start = raw.index("```json") + 7
            end = raw.index("```", start)
            return json.loads(raw[start:end].strip())

        if "```" in raw:
            start = raw.index("```") + 3
            end = raw.index("```", start)
            return json.loads(raw[start:end].strip())

        return json.loads(raw.strip())


_vertex_ai_client: VertexAIClient | None = None


def get_vertex_ai_client() -> VertexAIClient:
    """Return the singleton VertexAIClient."""
    global _vertex_ai_client
    if _vertex_ai_client is None:
        _vertex_ai_client = VertexAIClient()
    return _vertex_ai_client
