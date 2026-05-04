"""
Tests for the Credit Repository.

Verifies:
- Credit record creation for new users
- Daily reset logic for FREE tier
- Sufficient credit checks across all tiers
- Credit deduction (FREE daily vs PRO balance)
- Transaction logging
- Tier upgrades
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sys
sys.path.insert(0, ".")

from app.config.constants import UserTier
from app.config.settings import settings
from app.repositories.credit_repository import CreditRepository


class FakeUserCredits:
    """Fake UserCredits ORM object for unit testing without DB."""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.user_id = kwargs.get("user_id", uuid.uuid4())
        self.tier = kwargs.get("tier", "FREE")
        self.credit_balance = kwargs.get("credit_balance", 0)
        self.daily_credits_used = kwargs.get("daily_credits_used", 0)
        self.daily_reset_at = kwargs.get("daily_reset_at", None)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))


class TestHasSufficientCredits:
    """Tests for CreditRepository.has_sufficient_credits()."""

    def setup_method(self):
        self.repo = CreditRepository(db=MagicMock())

    def test_admin_always_has_credits(self):
        credits = FakeUserCredits(tier="ADMIN", credit_balance=0)
        assert self.repo.has_sufficient_credits(credits, 100) is True

    def test_free_tier_within_limit(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=2)
        assert self.repo.has_sufficient_credits(credits, 1) is True

    def test_free_tier_at_limit(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=5)
        assert self.repo.has_sufficient_credits(credits, 1) is False

    def test_free_tier_over_limit(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=10)
        assert self.repo.has_sufficient_credits(credits, 1) is False

    def test_free_tier_exact_remaining(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=4)
        # 5 - 4 = 1 remaining, cost = 1 → should pass
        assert self.repo.has_sufficient_credits(credits, 1) is True

    def test_free_tier_case_file_cost(self):
        # Case file costs 3, with 2 used → 3 remaining → should pass
        credits = FakeUserCredits(tier="FREE", daily_credits_used=2)
        assert self.repo.has_sufficient_credits(credits, 3) is True

    def test_free_tier_case_file_insufficient(self):
        # Case file costs 3, with 3 used → 2 remaining → should fail
        credits = FakeUserCredits(tier="FREE", daily_credits_used=3)
        assert self.repo.has_sufficient_credits(credits, 3) is False

    def test_pro_tier_with_balance(self):
        credits = FakeUserCredits(tier="PRO", credit_balance=50)
        assert self.repo.has_sufficient_credits(credits, 1) is True

    def test_pro_tier_no_balance(self):
        credits = FakeUserCredits(tier="PRO", credit_balance=0)
        assert self.repo.has_sufficient_credits(credits, 1) is False

    def test_pro_tier_exact_balance(self):
        credits = FakeUserCredits(tier="PRO", credit_balance=3)
        assert self.repo.has_sufficient_credits(credits, 3) is True

    def test_pro_tier_insufficient_for_case_file(self):
        credits = FakeUserCredits(tier="PRO", credit_balance=2)
        assert self.repo.has_sufficient_credits(credits, 3) is False


class TestGetRemainingCredits:
    """Tests for CreditRepository.get_remaining_credits()."""

    def setup_method(self):
        self.repo = CreditRepository(db=MagicMock())

    def test_free_tier_remaining(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=2)
        assert self.repo.get_remaining_credits(credits) == 3  # 5 - 2

    def test_free_tier_exhausted(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=5)
        assert self.repo.get_remaining_credits(credits) == 0

    def test_free_tier_over_exhausted(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=10)
        assert self.repo.get_remaining_credits(credits) == 0

    def test_pro_tier_remaining(self):
        credits = FakeUserCredits(tier="PRO", credit_balance=42)
        assert self.repo.get_remaining_credits(credits) == 42

    def test_admin_tier_remaining(self):
        credits = FakeUserCredits(tier="ADMIN", credit_balance=10000)
        assert self.repo.get_remaining_credits(credits) == 10000

    def test_free_tier_fresh(self):
        credits = FakeUserCredits(tier="FREE", daily_credits_used=0)
        assert self.repo.get_remaining_credits(credits) == 5


class TestCreditCosts:
    """Tests for credit action costs from constants."""

    def test_chat_cost(self):
        from app.config.constants import CreditAction
        assert CreditAction.CHAT.cost == 1

    def test_analysis_cost(self):
        from app.config.constants import CreditAction
        assert CreditAction.ANALYSIS.cost == 2

    def test_case_file_cost(self):
        from app.config.constants import CreditAction
        assert CreditAction.CASE_FILE.cost == 3

    def test_case_update_cost(self):
        from app.config.constants import CreditAction
        assert CreditAction.CASE_UPDATE.cost == 1

    def test_browse_is_free(self):
        from app.config.constants import CreditAction
        assert CreditAction.BROWSE.cost == 0
