"""
Gemini client — powers legal analysis, query expansion, and reranking.

Uses the ``google-genai`` SDK with Vertex AI.
Set VERTEX_AI_API_KEY in .env.
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai.types import GenerateContentConfig

from app.config.constants import (
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_TOP_P,
)
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VertexAIClient:
    """Wrapper around google-genai SDK for Gemini via Vertex AI."""

    def __init__(self) -> None:
        self._model = settings.gemini_model
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
            )
            logger.info("vertex_ai_client_init", model=self._model)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = GEMINI_TEMPERATURE,
        max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
        response_mime_type: str | None = None,
        model_name: str | None = None,
    ) -> str:
        """Generate text using Gemini."""
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

        response = await client.aio.models.generate_content(
            model=model_name or self._model,
            contents=prompt,
            config=config,
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
            model=model_name or self._model,
            contents=prompt,
            config=config,
        )

        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text

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
            model=model_name or self._model,
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
            model=model_name or self._model,
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
