"""
Explanation service — simplifies legal language for laypersons.

Takes complex legal text (law articles, court language) and rewrites it
in simple, everyday Georgian that anyone can understand.
"""

from __future__ import annotations

from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.explanation import EXPLAIN_ARTICLE, SIMPLIFY_TEXT
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExplanationService:
    """Simplifies legal language into plain Georgian/English."""

    def __init__(self, gemini_client: VertexAIClient | None = None) -> None:
        self._gemini = gemini_client

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def simplify(self, legal_text: str) -> str:
        """
        Simplify legal text into plain language.

        Args:
            legal_text: Complex legal text to simplify.

        Returns:
            Plain-language explanation.
        """
        if not legal_text.strip():
            return ""

        prompt = SIMPLIFY_TEXT.render(legal_text=legal_text)

        try:
            result = await self.gemini.generate(
                prompt=prompt,
                temperature=SIMPLIFY_TEXT.temperature,
                max_output_tokens=SIMPLIFY_TEXT.max_output_tokens,
            )
            logger.info(
                "text_simplified",
                input_length=len(legal_text),
                output_length=len(result),
            )
            return result
        except Exception as e:
            logger.error("simplification_failed", error=str(e))
            return f"[Simplification unavailable] {legal_text}"

    async def explain_article(
        self, code_name: str, article_number: str, article_text: str,
    ) -> str:
        """
        Explain a specific law article in simple terms.

        Provides additional context about what the article means in practice.
        """
        prompt = EXPLAIN_ARTICLE.render(
            code_name=code_name,
            article_number=article_number,
            article_text=article_text,
        )

        try:
            return await self.gemini.generate(
                prompt=prompt,
                temperature=EXPLAIN_ARTICLE.temperature,
                max_output_tokens=EXPLAIN_ARTICLE.max_output_tokens,
            )
        except Exception as e:
            logger.error("article_explanation_failed", error=str(e))
            return f"[Explanation unavailable] {article_text}"


_explanation_service: ExplanationService | None = None

def get_explanation_service() -> ExplanationService:
    global _explanation_service
    if _explanation_service is None:
        _explanation_service = ExplanationService()
    return _explanation_service
