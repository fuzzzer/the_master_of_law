"""
Credit gate middleware.

Checks if the user has enough credits before allowing AI-powered requests.
Returns 402 Payment Required when credits are exhausted.

Now wired to PostgreSQL — queries real credit balance from DB.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config.constants import CreditAction
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Map route path prefixes to credit actions and costs
CREDIT_ROUTES: dict[str, CreditAction] = {
    "/api/v1/chat/": CreditAction.CHAT,
    "/api/v1/case-files/build": CreditAction.CASE_FILE,
}


class CreditGateMiddleware(BaseHTTPMiddleware):
    """Block AI requests when user has no credits remaining."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        # Only check credit-consuming routes
        needs_credits = False
        credit_action = None
        for route_prefix, action in CREDIT_ROUTES.items():
            if path.startswith(route_prefix):
                needs_credits = True
                credit_action = action
                break

        if not needs_credits:
            return await call_next(request)

        # Only gate POST requests (GET on chat paths shouldn't cost credits)
        if request.method != "POST":
            return await call_next(request)

        # Get user from request state (set by auth middleware)
        user_info = getattr(request.state, "user", None)
        if not user_info:
            # No user context — auth middleware should have handled this
            return await call_next(request)

        uid = user_info.get("uid", "")
        tier = user_info.get("tier", "FREE")
        
        # Bypass credit check for app testers and admins
        if tier in ("ADMIN", "SUPERADMIN"):
            return await call_next(request)
            
        cost = credit_action.cost if credit_action else 1

        # Query real credit balance from DB
        try:
            from app.models.database import get_session_factory
            from app.repositories.credit_repository import CreditRepository
            from app.repositories.user_repository import UserRepository

            factory = get_session_factory()
            async with factory() as db:
                user_repo = UserRepository(db)
                user = await user_repo.get_by_firebase_uid(uid)

                if not user:
                    logger.warning("credit_gate_blocked_user_missing", uid=uid)
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": "unauthorized",
                            "message": "მომხმარებელი ვერ მოიძებნა. გთხოვთ გაიაროთ ავტორიზაცია.",
                            "message_en": "User account not initialized. Please authenticate first."
                        }
                    )

                credit_repo = CreditRepository(db)
                credits = await credit_repo.get_balance(user.id)

                if not credit_repo.has_sufficient_credits(credits, cost):
                    remaining = credit_repo.get_remaining_credits(credits)
                    logger.warning(
                        "credit_gate_blocked",
                        uid=uid,
                        tier=credits.tier,
                        remaining=remaining,
                        cost=cost,
                    )

                    message = (
                        "დღიური კრედიტები ამოიწურა. ხვალ ისევ სცადეთ."
                        if credits.tier == "FREE"
                        else "კრედიტები ამოიწურა. გთხოვთ შეიძინოთ დამატებითი კრედიტები."
                    )

                    return JSONResponse(
                        status_code=402,
                        content={
                            "error": "insufficient_credits",
                            "message": message,
                            "message_en": (
                                "Daily credits exhausted. Try again tomorrow."
                                if credits.tier == "FREE"
                                else "Credits exhausted. Please purchase additional credits."
                            ),
                            "credits_remaining": remaining,
                            "tier": credits.tier,
                            "daily_limit": (
                                settings.free_tier_daily_credits
                                if credits.tier == "FREE"
                                else None
                            ),
                        },
                    )

        except Exception as e:
            # If DB is unavailable, fail open in development, fail closed in production
            if settings.is_production:
                logger.error("credit_gate_db_error", error=str(e), exc_info=True)
                return JSONResponse(
                    status_code=503,
                    content={"error": "service_unavailable", "message": "Credit check unavailable"},
                )
            else:
                logger.warning("credit_gate_db_unavailable", error=str(e))
                # In development, allow through

        return await call_next(request)
