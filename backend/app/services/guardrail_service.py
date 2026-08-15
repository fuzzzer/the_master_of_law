"""
Hard Guardrail Service — pre-answer topic classification.

Uses Gemini Flash to cheaply classify whether a user message is
legal, greeting, off-topic, or harmful BEFORE burning expensive
RAG + Gemini Pro credits.

Integration: called in chat_router / ws_chat_router BEFORE the RAG pipeline.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from app.config.constants import (
    GUARDRAIL_CONFIDENCE_THRESHOLD,
    GUARDRAIL_ENABLED,
    UserTier,
)
from app.config.settings import settings
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.guardrail import GUARDRAIL_CLASSIFIER
from app.utils.logger import get_logger

logger = get_logger(__name__)


GUARDRAIL_RESPONSES = {
    "greeting": (
        "გამარჯობა! 👋 მე ვარ ბუნდოვანი კანონი — თქვენი იურიდიული ასისტენტი. "
        "აღწერეთ თქვენი სამართლებრივი სიტუაცია და დაგეხმარებით."
    ),
    "off_topic": (
        "ბოდიში, მე მხოლოდ სამართლებრივ საკითხებში შემიძლია დახმარება. "
        "გთხოვთ, აღწერეთ თქვენი იურიდიული სიტუაცია."
    ),
    "harmful": "ბოდიში, ამ ტიპის მოთხოვნაზე პასუხის გაცემა არ შემიძლია.",
}


@dataclass(frozen=True)
class GuardrailDecision:
    category: str       # "legal" | "greeting" | "off_topic" | "harmful"
    confidence: float   # 0.0 – 1.0
    should_proceed: bool  # True = run RAG pipeline, False = return canned response

    @property
    def response_text(self) -> str | None:
        """Returns a canned response for non-legal categories, or None if legal."""
        return GUARDRAIL_RESPONSES.get(self.category)


class GuardrailService:
    """Lightweight topic classifier that runs before the RAG pipeline."""

    def __init__(self, gemini_client: VertexAIClient | None = None) -> None:
        self._gemini = gemini_client

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def classify(
        self,
        message: str,
        user_tier: str = "FREE",
    ) -> GuardrailDecision:
        """Classify a user message into a guardrail category.

        ADMIN users always bypass guardrails (category='legal').
        If guardrails are disabled globally, always returns 'legal'.
        """
        if not GUARDRAIL_ENABLED:
            return GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)

        if user_tier == UserTier.ADMIN:
            self._log_decision(message, "legal", 1.0, bypassed=True)
            return GuardrailDecision(category="legal", confidence=1.0, should_proceed=True)

        prompt = GUARDRAIL_CLASSIFIER.render(user_message=message)
        try:
            raw = await self.gemini.generate(
                prompt=prompt,
                temperature=0.0,
                max_output_tokens=50,
                response_mime_type="application/json",
                model_name=settings.gemini_cheap_model,  # CHEAP tier
            )
            if not raw:
                logger.warning("guardrail_classification_empty", message="Empty response from Gemini")
                return GuardrailDecision(category="legal", confidence=0.0, should_proceed=True)
            parsed = json.loads(raw)
            category = parsed.get("category", "legal")
            confidence = float(parsed.get("confidence", 0.5))
        except Exception as e:
            logger.error("guardrail_classification_failed", error=str(e))
            return GuardrailDecision(category="legal", confidence=0.0, should_proceed=True)

        if category not in ("legal", "greeting", "off_topic", "harmful"):
            category = "legal"

        # Low confidence → default to legal (err on side of not blocking)
        if category != "legal" and confidence < GUARDRAIL_CONFIDENCE_THRESHOLD:
            category = "legal"

        should_proceed = category == "legal"
        self._log_decision(message, category, confidence)
        return GuardrailDecision(
            category=category,
            confidence=confidence,
            should_proceed=should_proceed,
        )

    def _log_decision(
        self,
        message: str,
        category: str,
        confidence: float,
        *,
        bypassed: bool = False,
    ) -> None:
        message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]
        logger.info(
            "guardrail_decision",
            message_hash=message_hash,
            category=category,
            confidence=confidence,
            bypassed=bypassed,
        )


_guardrail_service: GuardrailService | None = None


def get_guardrail_service() -> GuardrailService:
    global _guardrail_service
    if _guardrail_service is None:
        _guardrail_service = GuardrailService()
    return _guardrail_service
