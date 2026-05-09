"""
Tests for constants, settings, and core configuration.
"""

from __future__ import annotations

import sys
sys.path.insert(0, ".")

import pytest
from app.config.constants import (
    ConversationPhase, CreditAction, TIER_RATE_LIMITS, UserTier,
    RAG_VECTOR_SEARCH_TOP_K, RAG_RERANK_TOP_K, GEMINI_TEMPERATURE,
    LEGAL_DISCLAIMER_KA, LEGAL_DISCLAIMER_EN,
)


class TestUserTiers:
    def test_all_tiers(self):
        assert len(UserTier) == 3
        assert UserTier.FREE.value == "FREE"

class TestConversationPhases:
    def test_phase_count(self):
        assert len(ConversationPhase) == 7

class TestCreditActions:
    def test_costs(self):
        assert CreditAction.CHAT.cost == 1
        assert CreditAction.ANALYSIS.cost == 2
        assert CreditAction.CASE_FILE.cost == 3
        assert CreditAction.BROWSE.cost == 0

class TestRateLimits:
    def test_limits(self):
        assert TIER_RATE_LIMITS[UserTier.FREE] == 5
        assert TIER_RATE_LIMITS[UserTier.PRO] == 30
        assert TIER_RATE_LIMITS[UserTier.ADMIN] == 120

class TestRAGConstants:
    def test_values(self):
        assert RAG_VECTOR_SEARCH_TOP_K == 50
        assert RAG_RERANK_TOP_K == 20
        assert GEMINI_TEMPERATURE == 0.1

class TestDisclaimers:
    def test_exist(self):
        assert "AI" in LEGAL_DISCLAIMER_KA
        assert "AI-generated" in LEGAL_DISCLAIMER_EN

class TestSettings:
    def test_defaults(self):
        from app.config.settings import settings
        assert settings.app_name == "the-master-of-law"
        assert settings.free_tier_daily_credits == 5
        assert settings.is_production is False
        assert isinstance(settings.cors_origins, list)
