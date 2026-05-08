"""
Hard Guardrails — pre-filter for all incoming user messages.

Uses Gemini Flash (gemini-2.0-flash) for fast classification.
Latency budget: < 300ms.
Categories: legal, greeting, off_topic, harmful.

Integration point: call BEFORE RAG in the chat flow.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.config.constants import UserTier
from app.config.settings import settings
from app.schemas.guardrail_schema import GuardrailCategory, GuardrailDecision
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Georgian response messages ───────────────────────────────

GUARDRAIL_RESPONSES_KA: dict[GuardrailCategory, str] = {
    GuardrailCategory.GREETING: (
        "გამარჯობა! 👋 მე ვარ კანონის ოსტატი — თქვენი იურიდიული ასისტენტი. "
        "აღწერეთ თქვენი სამართლებრივი სიტუაცია და დაგეხმარებით."
    ),
    GuardrailCategory.OFF_TOPIC: (
        "ბოდიში, მე მხოლოდ სამართლებრივ საკითხებში შემიძლია დახმარება. "
        "გთხოვთ, აღწერეთ თქვენი იურიდიული სიტუაცია."
    ),
    GuardrailCategory.HARMFUL: (
        "ბოდიში, ამ ტიპის მოთხოვნაზე პასუხის გაცემა არ შემიძლია."
    ),
}

# ── Classification prompt ────────────────────────────────────

_GUARDRAIL_SYSTEM_PROMPT = """You are a legal topic classifier for a Georgian law application.
Classify the user's message into exactly one category:
- "legal": related to Georgian law, legal rights, court procedures, legal situations, contracts, property, criminal cases, family law, labor disputes, taxes, administrative violations, or any situation that might require legal advice
- "greeting": hello, how are you, good morning, good evening, etc. — any social greeting without legal content
- "off_topic": weather, sports, recipes, coding, math problems, general trivia, anything clearly non-legal
- "harmful": requests for illegal activity, threats, abuse, hate speech, self-harm instructions

Respond with JSON only: {"category": "...", "confidence": 0.0-1.0}

IMPORTANT RULES:
1. Err heavily on the side of "legal". If there's ANY chance the message relates to a legal situation, classify as "legal".
2. Casual phrasing about legal situations (e.g., "my boss fired me", "my landlord kicked me out", "someone hit my car") is LEGAL.
3. Messages mentioning Georgian legal terms, courts, police, lawyers, contracts, property, or rights are LEGAL.
4. Greetings mixed with legal questions are LEGAL, not greeting.
5. Messages in Georgian about everyday problems that could have legal implications are LEGAL.
"""


class GuardrailService:
    """Fast pre-filter using Gemini Flash."""

    def __init__(
        self,
        gemini_client: Any | None = None,
        confidence_threshold: float = 0.7,
        enabled: bool = True,
    ) -> None:
        self._gemini = gemini_client
        self.confidence_threshold = confidence_threshold
        self.enabled = enabled
        self._model = getattr(settings, "guardrail_model", "gemini-2.0-flash")

    @property
    def gemini(self) -> Any:
        if self._gemini is None:
            from app.integrations.vertex_ai_client import get_vertex_ai_client

            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def classify(self, message: str) -> GuardrailDecision:
        """Classify a user message. Returns LEGAL if guardrails are disabled."""
        if not self.enabled:
            return GuardrailDecision.legal(confidence=1.0)

        if not message or not message.strip():
            return GuardrailDecision.off_topic(confidence=1.0)

        try:
            raw = await self.gemini.generate(
                prompt=message,
                system_instruction=_GUARDRAIL_SYSTEM_PROMPT,
                temperature=0.0,
                max_output_tokens=50,
                response_mime_type="application/json",
            )
            parsed = json.loads(raw.strip())
            category_str = parsed.get("category", "legal").lower()
            confidence = float(parsed.get("confidence", 0.5))

            try:
                category = GuardrailCategory(category_str)
            except ValueError:
                category = GuardrailCategory.LEGAL
                confidence = 0.5

            # Low-confidence off_topic/harmful → treat as legal to reduce false positives
            if category in (GuardrailCategory.OFF_TOPIC, GuardrailCategory.HARMFUL):
                if confidence < self.confidence_threshold:
                    category = GuardrailCategory.LEGAL
                    confidence = 1.0 - confidence

            return GuardrailDecision(
                category=category,
                confidence=confidence,
                is_legal=(category == GuardrailCategory.LEGAL),
            )
        except Exception as e:
            logger.error("guardrail_classification_failed", error=str(e))
            # Fail open — treat as legal so user isn't blocked
            return GuardrailDecision.legal(confidence=0.0)

    def should_bypass(self, user_tier: str | UserTier) -> bool:
        """ADMIN users skip guardrails entirely."""
        if isinstance(user_tier, str):
            return user_tier.upper() == UserTier.ADMIN.value
        return user_tier == UserTier.ADMIN

    def get_response(self, decision: GuardrailDecision) -> str | None:
        """Return the Georgian response for non-legal categories, or None for legal."""
        if decision.is_legal:
            return None
        return GUARDRAIL_RESPONSES_KA.get(decision.category)

    def log_decision(
        self,
        user_id: str,
        message: str,
        decision: GuardrailDecision,
        bypassed: bool = False,
    ) -> dict[str, Any]:
        """Log a guardrail decision for audit purposes.

        Does NOT log the full message text — only a SHA-256 hash.
        """
        message_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
        entry = {
            "user_id": user_id,
            "message_hash": message_hash,
            "decision": decision.category.value,
            "confidence": round(decision.confidence, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "bypassed": bypassed,
        }
        logger.info("guardrail_decision", **entry)
        return entry


# ── Singleton ────────────────────────────────────────────────

_guardrail_service: GuardrailService | None = None


def get_guardrail_service() -> GuardrailService:
    """Return the singleton GuardrailService."""
    global _guardrail_service
    if _guardrail_service is None:
        from app.config.constants import (
            GUARDRAIL_CONFIDENCE_THRESHOLD,
            GUARDRAIL_ENABLED,
        )

        _guardrail_service = GuardrailService(
            enabled=GUARDRAIL_ENABLED,
            confidence_threshold=GUARDRAIL_CONFIDENCE_THRESHOLD,
        )
    return _guardrail_service
