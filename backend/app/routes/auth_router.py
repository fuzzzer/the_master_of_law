"""
Auth router — Firebase token verification and user sync.

Now wired to PostgreSQL via UserRepository and CreditRepository.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.repositories.credit_repository import CreditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import UserProfile, VerifyTokenRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/verify-token", response_model=UserProfile)
async def verify_token(body: VerifyTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify a Firebase ID token and create/sync the local user record.

    The Flutter app sends the Firebase ID token after sign-in.
    This endpoint verifies it, syncs the user to PostgreSQL, and
    returns the user profile with real credit balance.
    """
    try:
        from app.integrations.firebase_client import verify_id_token
        decoded = verify_id_token(body.id_token)

        # Sync user to DB (create if new, update last_login if existing)
        user_repo = UserRepository(db)
        user = await user_repo.create_or_update(
            firebase_uid=decoded.get("uid", ""),
            email=decoded.get("email"),
            display_name=decoded.get("name"),
            photo_url=decoded.get("picture"),
        )

        # Get real credit balance
        credit_repo = CreditRepository(db)
        credits = await credit_repo.get_balance(user.id)

        await db.commit()

        return UserProfile(
            uid=user.firebase_uid,
            email=user.email or "",
            display_name=user.display_name or "",
            tier=user.tier,
            credits_remaining=credit_repo.get_remaining_credits(credits),
            daily_credits_used=credits.daily_credits_used,
        )
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": str(e)},
        )


@router.get("/me", response_model=UserProfile)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    """Get the current authenticated user's profile with real credit data."""
    user_info = getattr(request.state, "user", None)
    if not user_info:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": "Not authenticated"},
        )

    uid = user_info.get("uid", "")

    # Fetch real data from DB
    user_repo = UserRepository(db)
    user = await user_repo.get_by_firebase_uid(uid)

    if not user:
        # User exists in Firebase but not yet in our DB — create them
        user = await user_repo.create_or_update(
            firebase_uid=uid,
            email=user_info.get("email"),
        )
        await db.commit()

    credit_repo = CreditRepository(db)
    credits = await credit_repo.get_balance(user.id)

    return UserProfile(
        uid=user.firebase_uid,
        email=user.email or "",
        display_name=user.display_name or "",
        tier=user.tier,
        credits_remaining=credit_repo.get_remaining_credits(credits),
        daily_credits_used=credits.daily_credits_used,
    )
