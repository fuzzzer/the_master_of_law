"""
Firebase Admin SDK initialization.

Verifies Firebase ID tokens sent by the Flutter app.
The backend NEVER handles passwords — Firebase handles all authentication.
"""

from __future__ import annotations

from typing import Any

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_firebase_initialized = False


def _ensure_firebase_init() -> None:
    """Initialize Firebase Admin SDK (once)."""
    global _firebase_initialized
    if _firebase_initialized:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials

        if settings.firebase_service_account_key:
            cred = credentials.Certificate(settings.firebase_service_account_key)
            firebase_admin.initialize_app(cred)
        else:
            # Use Application Default Credentials
            firebase_admin.initialize_app()

        _firebase_initialized = True
        logger.info("firebase_initialized", project=settings.firebase_project_id)
    except Exception as e:
        logger.error("firebase_init_failed", error=str(e))
        raise


def verify_id_token(id_token: str) -> dict[str, Any]:
    """
    Verify a Firebase ID token.

    Returns the decoded token payload with uid, email, etc.
    Raises ValueError if the token is invalid.
    """
    _ensure_firebase_init()

    from firebase_admin import auth

    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except auth.InvalidIdTokenError:
        raise ValueError("Invalid Firebase ID token")
    except auth.ExpiredIdTokenError:
        raise ValueError("Firebase ID token has expired")
    except auth.RevokedIdTokenError:
        raise ValueError("Firebase ID token has been revoked")
    except Exception as e:
        raise ValueError(f"Firebase token verification failed: {e}")
