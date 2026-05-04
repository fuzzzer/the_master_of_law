"""
Legal Analysis Service — Gemini-powered legal reasoning.

Constructs the system prompt, builds context from retrieved law chunks,
sends to Gemini 2.5 Pro, and returns a structured legal analysis.
"""

from __future__ import annotations

from typing import Any

from app.config.constants import LEGAL_DISCLAIMER_KA
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.legal_analysis import LEGAL_ANALYSIS_SYSTEM
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LawContextFormatter:
    """Formats retrieved law chunks into context for Gemini prompts."""

    @staticmethod
    def format(chunks: list[dict[str, Any]]) -> str:
        """Format retrieved law chunks into a numbered context block."""
        if not chunks:
            return "No relevant law articles were found."

        parts = ["RELEVANT GEORGIAN LAW ARTICLES:\n"]
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            code = meta.get("code_name", "Unknown")
            article = meta.get("article_number", "")
            title = meta.get("article_title", "")
            citation = meta.get("citation_text", "")
            url = meta.get("article_url", "")
            content = chunk.get("content", "")

            header = f"[{i}] {code}, {article}"
            if title:
                header += f" — {title}"
            parts.append(header)
            if citation:
                parts.append(f"   Citation: {citation}")
            if url:
                parts.append(f"   URL: {url}")
            parts.append(f"   Text: {content[:2000]}")
            parts.append("")

        return "\n".join(parts)


class ConversationHistoryFormatter:
    """Formats conversation history for multi-turn Gemini context."""

    @staticmethod
    def format(history: list[dict[str, str]], max_turns: int = 10) -> str:
        """Format conversation history into a labeled text block."""
        if not history:
            return ""

        parts = ["CONVERSATION HISTORY:\n"]
        for msg in history[-max_turns:]:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            parts.append(f"{role.upper()}: {text}\n")
        parts.append("\n---\n")
        return "\n".join(parts)


class LegalAnalysisService:
    """Generates grounded legal analysis using Gemini + retrieved law chunks."""

    def __init__(self, gemini_client: VertexAIClient | None = None):
        self._gemini = gemini_client
        self._law_formatter = LawContextFormatter()
        self._history_formatter = ConversationHistoryFormatter()

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def analyze(
        self,
        user_message: str,
        retrieved_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Generate a legal analysis response.

        Args:
            user_message: The user's current message.
            retrieved_chunks: Law chunks from the RAG pipeline.
            conversation_history: Previous messages for context.

        Returns:
            The AI-generated legal analysis text.
        """
        user_prompt = self._build_user_prompt(
            user_message, retrieved_chunks, conversation_history,
        )

        logger.info(
            "legal_analysis_start",
            chunks_count=len(retrieved_chunks),
            prompt_length=len(user_prompt),
        )

        response = await self.gemini.generate(
            prompt=user_prompt,
            system_instruction=LEGAL_ANALYSIS_SYSTEM.template,
            temperature=LEGAL_ANALYSIS_SYSTEM.temperature,
            max_output_tokens=LEGAL_ANALYSIS_SYSTEM.max_output_tokens,
        )

        response += f"\n\n---\n⚠️ {LEGAL_DISCLAIMER_KA}"

        logger.info("legal_analysis_done", response_length=len(response))
        return response

    def _build_user_prompt(
        self,
        user_message: str,
        chunks: list[dict[str, Any]],
        history: list[dict[str, str]] | None,
    ) -> str:
        """Assemble the full user prompt from law context + history + message."""
        parts = [self._law_formatter.format(chunks), "\n---\n"]

        if history:
            parts.append(self._history_formatter.format(history))

        parts.append(f"USER'S CURRENT MESSAGE:\n{user_message}")
        return "\n".join(parts)


_analysis_service: LegalAnalysisService | None = None

def get_legal_analysis_service() -> LegalAnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = LegalAnalysisService()
    return _analysis_service
