"""
Credit repository — balance queries, deduction, daily reset, transaction log.

Manages the user_credits and credit_transactions tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, cast, Date, update, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import UserTier
from app.config.settings import settings
from app.models.user_credits import CreditTransaction, UserCredits
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CreditRepository:
    """Data access layer for credit balance and transactions."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create(self, user_id: uuid.UUID) -> UserCredits:
        """
        Get a user's credit record, creating it with defaults if absent.

        New FREE users start with 0 balance (daily grants are auto-applied).
        """
        stmt = select(UserCredits).where(UserCredits.user_id == user_id)
        result = await self._db.execute(stmt)
        credits = result.scalar_one_or_none()

        if credits:
            return credits

        from sqlalchemy.dialects.postgresql import insert
        stmt = insert(UserCredits).values(
            id=uuid.uuid4(),
            user_id=user_id,
            tier="FREE",
            credit_balance=0,
            daily_credits_used=0,
            daily_reset_at=None,
        ).on_conflict_do_update(
            index_elements=["user_id"],
            set_={"updated_at": func.now()}
        )
        await self._db.execute(stmt)
        await self._db.flush()

        stmt = select(UserCredits).where(UserCredits.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_balance(self, user_id: uuid.UUID) -> UserCredits:
        """
        Get credit balance, applying daily reset if needed.

        For FREE tier users:
        - Resets daily_credits_used to 0 at midnight UTC
        - Balance is effectively: daily_limit - daily_credits_used
        """
        credits = await self.get_or_create(user_id)

        # Check if daily reset is needed (FREE tier resets daily)
        if credits.tier == UserTier.FREE.value:
            now = datetime.now(timezone.utc)
            if credits.daily_reset_at is None or credits.daily_reset_at.date() < now.date():
                # Acquire row lock to prevent race on reset update
                stmt = select(UserCredits).where(UserCredits.id == credits.id).with_for_update()
                res = await self._db.execute(stmt)
                locked_credits = res.scalar_one()
                # Check again under lock
                if locked_credits.daily_reset_at is None or locked_credits.daily_reset_at.date() < now.date():
                    locked_credits.daily_credits_used = 0
                    locked_credits.daily_reset_at = now
                    await self._db.flush()
                    logger.info("daily_credits_reset", user_id=str(user_id))
                return locked_credits

        return credits

    def has_sufficient_credits(self, credits: UserCredits, cost: int) -> bool:
        """
        Check if a user has enough credits for an action.

        FREE tier: checks daily_credits_used < daily_limit
        PRO tier: checks credit_balance >= cost
        ADMIN tier: always True (10,000 credits)
        """
        tier = credits.tier

        if tier == UserTier.ADMIN.value:
            return True

        if tier == UserTier.FREE.value:
            remaining = settings.free_tier_daily_credits - credits.daily_credits_used
            return remaining >= cost

        # PRO tier
        return credits.credit_balance >= cost

    def get_remaining_credits(self, credits: UserCredits) -> int:
        """Return the effective number of credits remaining."""
        tier = credits.tier

        if tier == UserTier.ADMIN.value:
            return credits.credit_balance

        if tier == UserTier.FREE.value:
            return max(0, settings.free_tier_daily_credits - credits.daily_credits_used)

        # PRO tier
        return credits.credit_balance

    async def deduct(
        self,
        user_id: uuid.UUID,
        cost: int,
        action: str,
        description: str = "",
    ) -> UserCredits:
        """
        Deduct credits after a successful AI response.

        For FREE tier: increments daily_credits_used
        For PRO/ADMIN: decrements credit_balance
        Logs a credit_transaction for auditing.
        """
        # 1. Ensure user credits row exists
        credits = await self.get_or_create(user_id)

        # 2. Perform atomic update with limit/tier guards and daily reset folded in
        daily_limit = settings.free_tier_daily_credits
        is_reset_needed = (UserCredits.daily_reset_at == None) | (
            cast(UserCredits.daily_reset_at, Date) < func.current_date()
        )

        stmt = (
            update(UserCredits)
            .where(UserCredits.user_id == user_id)
            .where(
                (UserCredits.tier == UserTier.ADMIN.value)
                | (
                    (UserCredits.tier == UserTier.FREE.value)
                    & (
                        (is_reset_needed & (cost <= daily_limit))
                        | (UserCredits.daily_credits_used + cost <= daily_limit)
                    )
                )
                | (
                    (UserCredits.tier == UserTier.PRO.value)
                    & (UserCredits.credit_balance >= cost)
                )
            )
            .values(
                daily_credits_used=case(
                    (UserCredits.tier == UserTier.FREE.value,
                     case(
                         (is_reset_needed, cost),
                         else_=UserCredits.daily_credits_used + cost
                     )),
                    else_=UserCredits.daily_credits_used
                ),
                credit_balance=case(
                    (UserCredits.tier == UserTier.FREE.value, UserCredits.credit_balance),
                    else_=case(
                        (UserCredits.credit_balance - cost < 0, 0),
                        else_=UserCredits.credit_balance - cost
                    )
                ),
                daily_reset_at=case(
                    ((UserCredits.tier == UserTier.FREE.value) & is_reset_needed, func.now()),
                    else_=UserCredits.daily_reset_at
                ),
                updated_at=func.now()
            )
            .returning(UserCredits)
        )

        res = await self._db.execute(stmt)
        updated_credits = res.scalars().first()

        if not updated_credits:
            # Atomic update failed, likely because of insufficient credits
            raise ValueError("Insufficient credits for action")

        # 3. Log the transaction
        txn = CreditTransaction(
            id=uuid.uuid4(),
            user_id=user_id,
            amount=-cost,
            transaction_type=action,
            description=description or f"Deducted {cost} credit(s) for {action}",
        )
        self._db.add(txn)
        await self._db.flush()

        logger.info(
            "credits_deducted",
            user_id=str(user_id),
            cost=cost,
            action=action,
            remaining=self.get_remaining_credits(updated_credits),
        )
        return updated_credits

    async def add_credits(
        self,
        user_id: uuid.UUID,
        amount: int,
        transaction_type: str = "admin_grant",
        description: str = "",
    ) -> UserCredits:
        """Add credits to a user (purchase, admin grant, etc.)."""
        credits = await self.get_or_create(user_id)
        credits.credit_balance += amount

        txn = CreditTransaction(
            id=uuid.uuid4(),
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description or f"Added {amount} credit(s) via {transaction_type}",
        )
        self._db.add(txn)
        await self._db.flush()

        logger.info("credits_added", user_id=str(user_id), amount=amount, type=transaction_type)
        return credits

    async def get_transactions(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CreditTransaction]:
        """Get credit transaction history, most recent first."""
        stmt = (
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_transaction_count(self, user_id: uuid.UUID) -> int:
        """Get total number of transactions for a user."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(CreditTransaction).where(
            CreditTransaction.user_id == user_id
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def set_tier(self, user_id: uuid.UUID, tier: str, initial_balance: int = 0) -> UserCredits:
        """
        Update a user's tier and optionally set an initial balance.

        Used for tier upgrades (FREE→PRO, admin grants).
        """
        credits = await self.get_or_create(user_id)
        credits.tier = tier
        if initial_balance > 0:
            credits.credit_balance = initial_balance
        await self._db.flush()
        logger.info("tier_set", user_id=str(user_id), tier=tier, balance=initial_balance)
        return credits
