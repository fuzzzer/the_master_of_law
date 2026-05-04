"""
Account router — credit balance and transaction history.

Now wired to PostgreSQL via CreditRepository.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.database import get_db
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import CreditBalance, CreditHistoryResponse, CreditTransactionItem
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/account", tags=["account"])


@router.get("/credits", response_model=CreditBalance)
async def get_credits(request: Request, db: AsyncSession = Depends(get_db)):
    """Get the current user's credit balance and daily usage."""
    user_info = getattr(request.state, "user", None)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    uid = user_info.get("uid", "")

    # Get user from DB
    user_repo = UserRepository(db)
    user = await user_repo.get_by_firebase_uid(uid)
    if not user:
        user = await user_repo.create_or_update(firebase_uid=uid)
        await db.commit()

    # Get real credit balance
    credit_repo = CreditRepository(db)
    credits = await credit_repo.get_balance(user.id)

    return CreditBalance(
        tier=credits.tier,
        credit_balance=credit_repo.get_remaining_credits(credits),
        daily_credits_used=credits.daily_credits_used,
        daily_limit=settings.free_tier_daily_credits if credits.tier == "FREE" else None,
    )


@router.get("/transactions", response_model=CreditHistoryResponse)
async def get_transactions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get credit transaction history."""
    user_info = getattr(request.state, "user", None)
    if not user_info:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})

    uid = user_info.get("uid", "")

    # Get user from DB
    user_repo = UserRepository(db)
    user = await user_repo.get_by_firebase_uid(uid)
    if not user:
        return CreditHistoryResponse(transactions=[], total=0)

    # Get real transaction history
    credit_repo = CreditRepository(db)
    transactions = await credit_repo.get_transactions(user.id, limit=limit, offset=offset)
    total = await credit_repo.get_transaction_count(user.id)

    return CreditHistoryResponse(
        transactions=[
            CreditTransactionItem(
                amount=txn.amount,
                transaction_type=txn.transaction_type,
                description=txn.description or "",
                created_at=txn.created_at.isoformat() if txn.created_at else "",
            )
            for txn in transactions
        ],
        total=total,
    )
