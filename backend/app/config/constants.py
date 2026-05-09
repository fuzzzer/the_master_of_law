"""
App-wide constants — tier definitions, credit costs, conversation phases.

These are static values that don't change per environment.
"""

from __future__ import annotations

import enum


# ── User Tiers ───────────────────────────────────────────────

class UserTier(str, enum.Enum):
    """User subscription tiers."""
    FREE = "FREE"
    PRO = "PRO"
    ADMIN = "ADMIN"


# ── Conversation Phases ──────────────────────────────────────

class ConversationPhase(str, enum.Enum):
    """State machine phases for conversations."""
    GREETING = "GREETING"
    INTAKE = "INTAKE"
    QUESTIONNAIRE = "QUESTIONNAIRE"
    CLARIFICATION = "CLARIFICATION"
    ANALYSIS = "ANALYSIS"
    ADVICE = "ADVICE"
    FOLLOW_UP = "FOLLOW_UP"


# ── Credit Costs ─────────────────────────────────────────────

class CreditAction(str, enum.Enum):
    """Actions that consume credits."""
    CHAT = "chat"
    ANALYSIS = "analysis"
    CASE_FILE = "case_file"
    CASE_UPDATE = "case_update"
    BROWSE = "browse"  # always free

    @property
    def cost(self) -> int:
        """Return the credit cost for this action."""
        return _ACTION_COSTS.get(self, 0)


_ACTION_COSTS: dict[CreditAction, int] = {
    CreditAction.CHAT: 1,
    CreditAction.ANALYSIS: 2,
    CreditAction.CASE_FILE: 3,
    CreditAction.CASE_UPDATE: 1,
    CreditAction.BROWSE: 0,
}


# ── Rate Limits (per tier, requests per minute) ──────────────

TIER_RATE_LIMITS: dict[UserTier, int] = {
    UserTier.FREE: 5,
    UserTier.PRO: 30,
    UserTier.ADMIN: 120,
}


# ── RAG Pipeline ─────────────────────────────────────────────

RAG_VECTOR_SEARCH_TOP_K = 50          # Per expanded query
RAG_FULLTEXT_SEARCH_TOP_K = 50        # Per expanded query
RAG_RERANK_TOP_K = 20                 # After merge + dedup
RAG_QUERY_EXPANSION_COUNT = 8         # Target number of expanded queries

# ── Gemini ───────────────────────────────────────────────────

GEMINI_TEMPERATURE = 1              
GEMINI_MAX_OUTPUT_TOKENS = 8192
GEMINI_TOP_P = 0.8

# ── Guardrails ───────────────────────────────────────────────

GUARDRAIL_ENABLED: bool = True
GUARDRAIL_CONFIDENCE_THRESHOLD: float = 0.7
GUARDRAIL_MODEL: str = "gemini-2.0-flash"

# ── Disclaimer ───────────────────────────────────────────────

LEGAL_DISCLAIMER_KA = (
    "ეს არის AI-ის მიერ გენერირებული იურიდიული ინფორმაცია, "
    "არა ოფიციალური იურიდიული კონსულტაცია. "
    "სერიოზულ შემთხვევებში აუცილებლად მიმართეთ ადვოკატს."
)

LEGAL_DISCLAIMER_EN = (
    "This is AI-generated legal information, not official legal advice. "
    "In serious cases, always consult a licensed lawyer."
)
