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
    DOCUMENT_GENERATION = "document_generation"
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
    CreditAction.DOCUMENT_GENERATION: 5,
    CreditAction.BROWSE: 0,
}


# ── Rate Limits (per tier, requests per minute) ──────────────

TIER_RATE_LIMITS: dict[UserTier, int] = {
    UserTier.FREE: 5,
    UserTier.PRO: 30,
    UserTier.ADMIN: 120,
}


# ── RAG Pipeline ─────────────────────────────────────────────

RAG_VECTOR_SEARCH_TOP_K = 75          # Per expanded query (fallback for unknown collections)
RAG_VECTOR_TOP_K_PER_COLLECTION = {   # Per expanded query, per collection —
    "georgian_laws": 40,              # separate quotas so court practice cannot
    "court_practice": 25,             # crowd statutes out of the candidate pool
    "grand_chamber": 10,
}
RAG_FULLTEXT_SEARCH_TOP_K = 50        # Per expanded query
RAG_RERANK_POOL_PER_COLLECTION = {    # Rerank candidate caps — court practice
    "georgian_laws": 50,              # embeds systematically closer than statutes,
    "court_practice": 40,             # so the pre-rerank pool must also be balanced
    "grand_chamber": 10,
}
RAG_RERANK_TOP_K = 35                 # Send more to Gemini to have a large pool
RAG_LAWS_QUOTA = 15                   # Max laws to keep after rerank
RAG_CASES_QUOTA = 8                   # Max cases to keep after rerank
RAG_QUERY_EXPANSION_COUNT = 8         # Target number of expanded queries

# ── Full-code injection (grounding mechanism C) ──────────────
# Domains whose statute questions are answered from ONE unambiguous, small
# enough code. Big codes (civil 545k, criminal 442k, tax 719k, admin
# offences 763k chars) stay on RAG + navigation tools.
FULL_CODE_INJECTION_DOMAIN_CODES: dict[str, list[str]] = {
    "labor": ["labour_code"],
    "constitutional": ["constitution"],
}

# ── Gemini ───────────────────────────────────────────────────

GEMINI_TEMPERATURE = 1              
GEMINI_MAX_OUTPUT_TOKENS = 8192
GEMINI_TOP_P = 0.8

# ── Guardrails ───────────────────────────────────────────────

GUARDRAIL_ENABLED: bool = True
GUARDRAIL_CONFIDENCE_THRESHOLD: float = 0.7

# Headroom, not a target: the classifier emits ~11 tokens of JSON with thinking
# disabled. The old value was 50, which is fine for the ANSWER and fatal on a
# thinking model, where reasoning is drawn from the same allowance. Sized so
# that re-enabling thinking here could not silently empty the response again.
GUARDRAIL_MAX_OUTPUT_TOKENS: int = 256

# There is deliberately NO GUARDRAIL_MODEL here. One was declared and pinned
# at "gemini-2.0-flash", imported by guardrail_service, and then never read —
# the classifier has always run on the cheap tier from settings. Dead config
# that names a model is worse than none: the next person to touch the
# guardrail would have believed it ran two majors behind everything else.
# The guardrail is CHEAP-tier work; it uses settings.gemini_cheap_model.

# ── Disclaimer ───────────────────────────────────────────────

# Prepended when a statute-type question got ZERO statute grounding
# (no chunks, no successful tool lookup, no full-code injection) — plan 2.4.
UNGROUNDED_STATUTE_DISCLAIMER_KA = (
    "⚠️ **გაფრთხილება:** ამ პასუხისთვის შესაბამისი საკანონმდებლო ნორმები "
    "ბაზაში ვერ მოიძებნა. პასუხი ეყრდნობა ზოგად სამართლებრივ ცოდნას და "
    "შესაძლოა უზუსტო იყოს — აუცილებლად გადაამოწმეთ ინფორმაცია ადვოკატთან "
    "ან matsne.gov.ge-ზე.\n\n"
)

# Appended when the response advises legal action but states no deadline —
# the deadline duty (plan 0.2) enforced structurally, not just by prompt.
DEADLINE_GUARD_KA = (
    "\n\n⚠️ სამართლებრივ ქმედებებს კანონით დადგენილი ვადები აქვს — "
    "მოქმედების დაწყებამდე აუცილებლად გადაამოწმეთ შესაბამისი ვადა "
    "კანონში ან იურისტთან."
)

LEGAL_DISCLAIMER_KA = (
    "ეს არის AI-ის მიერ გენერირებული იურიდიული ინფორმაცია, "
    "არა ოფიციალური იურიდიული კონსულტაცია. "
    "სერიოზულ შემთხვევებში აუცილებლად მიმართეთ ადვოკატს."
)

LEGAL_DISCLAIMER_EN = (
    "This is AI-generated legal information, not official legal advice. "
    "In serious cases, always consult a licensed lawyer."
)
