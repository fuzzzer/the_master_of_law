"""
Legal Classifier service — classifies legal domain from user input.

Determines which area of law a user's situation falls under,
used to optimize RAG retrieval and conversation flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.classifier import LEGAL_CLASSIFIER
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class LegalDomain:
    """A recognized legal domain with Georgian and English names."""
    key: str
    name_ka: str
    name_en: str
    keywords: tuple[str, ...] = ()


# All legal domains recognized by the system
LEGAL_DOMAINS_LIST: tuple[LegalDomain, ...] = (
    LegalDomain("criminal", "სისხლის სამართალი", "Criminal law",
                ("დანაშაული", "ბრალი", "დაკავება", "პატიმრობა", "ცემა", "ქურდობა", "მკვლელობა", "ძალადობა", "პოლიცია")),
    LegalDomain("civil", "სამოქალაქო სამართალი", "Civil law",
                ("ხელშეკრულება", "ზიანი", "ვალი", "საკუთრება", "დავა", "ანაზღაურება")),
    LegalDomain("administrative", "ადმინისტრაციული სამართალი", "Administrative law",
                ("ჯარიმა", "ნებართვა", "ლიცენზია", "ადმინისტრაციული")),
    LegalDomain("labor", "შრომის სამართალი", "Labor law",
                ("სამსახური", "დათხოვნა", "ხელფასი", "შრომა", "დამსაქმებელი", "თანამშრომელი")),
    LegalDomain("family", "საოჯახო სამართალი", "Family law",
                ("განქორწინება", "ალიმენტი", "მეურვეობა", "ქორწინება", "შვილი", "მემკვიდრეობა")),
    LegalDomain("tax", "საგადასახადო სამართალი", "Tax law",
                ("გადასახადი", "საგადასახადო", "დეკლარაცია")),
    LegalDomain("land", "მიწის სამართალი", "Land/property law",
                ("მიწა", "ნაკვეთი", "მეზობელი", "საზღვარი", "უძრავი")),
    LegalDomain("constitutional", "კონსტიტუციური სამართალი", "Constitutional law", ()),
    LegalDomain("commercial", "სამეწარმეო სამართალი", "Commercial/business law", ()),
)

# Lookup dicts for fast access
LEGAL_DOMAINS: dict[str, str] = {d.key: d.name_ka for d in LEGAL_DOMAINS_LIST}
_DOMAIN_BY_KEY: dict[str, LegalDomain] = {d.key: d for d in LEGAL_DOMAINS_LIST}


@dataclass
class ClassificationResult:
    """Typed result of legal domain classification."""
    primary: str
    secondary: list[str]
    confidence: float
    reasoning: str
    primary_ka: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "primary_ka": self.primary_ka,
        }


class KeywordClassifier:
    """Georgian keyword-based classification fallback (no Gemini needed)."""

    def __init__(self, domains: tuple[LegalDomain, ...] = LEGAL_DOMAINS_LIST) -> None:
        self._domains = domains

    def classify(self, text: str) -> ClassificationResult:
        """Classify text by counting keyword matches per domain."""
        text_lower = text.lower()
        scores: dict[str, int] = {}

        for domain in self._domains:
            if not domain.keywords:
                continue
            score = sum(1 for kw in domain.keywords if kw in text_lower)
            if score > 0:
                scores[domain.key] = score

        if scores:
            primary = max(scores, key=scores.get)  # type: ignore[arg-type]
            secondary = [d for d in scores if d != primary]
            return ClassificationResult(
                primary=primary,
                secondary=secondary,
                confidence=min(scores[primary] / 3.0, 1.0),
                reasoning="Classified by keyword matching (Gemini unavailable)",
                primary_ka=LEGAL_DOMAINS.get(primary, ""),
            )

        return ClassificationResult(
            primary="civil",
            secondary=[],
            confidence=0.1,
            reasoning="Default fallback — could not determine domain",
            primary_ka=LEGAL_DOMAINS.get("civil", ""),
        )


class LegalClassifierService:
    """Classifies user situations into legal domains using Gemini with keyword fallback."""

    def __init__(self, gemini_client: VertexAIClient | None = None) -> None:
        self._gemini = gemini_client
        self._keyword_classifier = KeywordClassifier()

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def classify(self, user_message: str) -> dict[str, Any]:
        """
        Classify a user's message into legal domains.

        Uses Gemini for smart classification, falls back to keyword heuristics.
        """
        prompt = LEGAL_CLASSIFIER.render(user_message=user_message)

        try:
            result = await self.gemini.generate_json(
                prompt=prompt,
                temperature=LEGAL_CLASSIFIER.temperature,
            )

            if isinstance(result, dict):
                primary = result.get("primary", "civil")
                result["primary_ka"] = LEGAL_DOMAINS.get(primary, "")
                logger.info(
                    "legal_domain_classified",
                    primary=primary,
                    confidence=result.get("confidence", 0),
                )
                return result
        except Exception as e:
            logger.error("legal_classification_failed", error=str(e))

        return self._heuristic_classify(user_message)

    def _heuristic_classify(self, text: str) -> dict[str, Any]:
        """Keyword-based fallback classification."""
        return self._keyword_classifier.classify(text).to_dict()


_classifier: LegalClassifierService | None = None

def get_legal_classifier_service() -> LegalClassifierService:
    global _classifier
    if _classifier is None:
        _classifier = LegalClassifierService()
    return _classifier
