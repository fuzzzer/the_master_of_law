"""
Firebase Authentication middleware.

Extracts and verifies the Firebase ID token from the Authorization header.
Adds the authenticated user info to the request state.

For development, set APP_ENV=development to allow unauthenticated requests
with a mock user context.

Now enriches user context with real tier from PostgreSQL.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/api/v1/health",
    "/api/v1/health/ready",
    "/api/v1/laws/search",
    "/api/v1/laws/codes",
    "/api/v1/traces/dashboard",  # static HTML only; trace data endpoints stay admin-guarded
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Path prefixes that don't require authentication
PUBLIC_PREFIXES = (
    "/api/v1/laws/",
    "/api/v1/health",
    "/docs",
    "/redoc",
)


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """Verify Firebase ID tokens on protected routes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        # CORS preflight requests must pass through unauthenticated
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for public endpoints
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # In development, allow unauthenticated requests with mock user
        if settings.app_env == "development":
            auth_header = request.headers.get("Authorization", "")
            if not auth_header and not request.headers.get("X-API-Key"):
                # Set mock user for development
                request.state.user = {
                    "uid": "dev-user-001",
                    "email": "dev@masteroflaw.ge",
                    "tier": "ADMIN",
                }
                return await call_next(request)

        # Temporary Staging API Key Auth
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            if settings.app_env == "development" and api_key == settings.admin_api_key:
                request.state.user = {
                    "uid": "admin-api-key",
                    "email": "admin@masteroflaw.ge",
                    "tier": "SUPERADMIN",
                }
                return await call_next(request)
            
            from app.utils.api_keys import is_valid_api_key
            if is_valid_api_key(api_key):
                request.state.user = {
                    "uid": f"api-user-{api_key[:8]}",
                    "email": "tester@masteroflaw.ge",
                    "tier": "FREE",
                }
                return await call_next(request)
            else:
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "message": "Invalid Access Key"},
                )

        # Extract token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Missing or invalid Authorization header"},
            )

        token = auth_header[7:]  # Strip "Bearer "

        try:
            from app.integrations.firebase_client import verify_id_token
            decoded = verify_id_token(token)

            uid = decoded.get("uid", "")

            # Enrich with real tier from DB
            tier = "FREE"
            try:
                from app.models.database import get_session_factory
                from app.repositories.user_repository import UserRepository

                factory = get_session_factory()
                async with factory() as db:
                    user_repo = UserRepository(db)
                    user = await user_repo.get_by_firebase_uid(uid)
                    if user:
                        tier = user.tier
            except Exception as e:
                logger.warning("auth_middleware_db_lookup_failed", error=str(e))
                # Fall back to FREE tier if DB is unavailable

            request.state.user = {
                "uid": uid,
                "email": decoded.get("email", ""),
                "tier": tier,
            }
        except ValueError as e:
            return JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": str(e)},
            )

        return await call_next(request)
