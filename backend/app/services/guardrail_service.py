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
    GUARDRAIL_MAX_OUTPUT_TOKENS,
    UserTier,
)
from app.config.settings import settings
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.guardrail import GUARDRAIL_CLASSIFIER
from app.services.trace_service import record_step
from app.utils.logger import get_logger
from app.services.model_config_service import cheap_model, strong_model

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
    confidence: float | None   # 0.0 – 1.0; None = classifier unavailable
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
                # Budget and thinking are set TOGETHER on purpose. This is a
                # four-way label plus a float; there is nothing here to reason
                # about, so reasoning is off and the whole allowance belongs to
                # the answer. Leaving thinking on made this call return empty on
                # EVERY request under gemini-3.7-flash (47 of 50 tokens spent
                # thinking) and the guardrail silently stopped classifying.
                max_output_tokens=GUARDRAIL_MAX_OUTPUT_TOKENS,
                thinking_budget=0,
                response_mime_type="application/json",
                model_name=await cheap_model(),  # CHEAP tier
            )
            if not raw:
                return self._fail_open("empty_response", "Empty response from Gemini")
            parsed = json.loads(raw)
            category = parsed.get("category", "legal")
            confidence = float(parsed.get("confidence", 0.5))
        except Exception as e:
            return self._fail_open("exception", str(e))

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

    @staticmethod
    def _fail_open(reason: str, detail: str) -> GuardrailDecision:
        """Let the request through when the classifier itself failed.

        Failing OPEN is the right call — refusing a real legal question because
        our classifier blipped is worse than letting an off-topic one through.
        But it must never be MISTAKEN for a successful classification: the old
        code returned a plain (legal, 0.0) here, which is exactly what a real
        low-confidence verdict looks like, so a guardrail that had stopped
        working for every single request read as normal in the trace. It now
        records its own step and carries a confidence of None.
        """
        logger.warning("guardrail_unavailable", reason=reason, detail=detail[:300])
        record_step("guardrail_unavailable", reason=reason, detail=detail[:300])
        return GuardrailDecision(category="legal", confidence=None, should_proceed=True)

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
