"""
User repository — CRUD for the users table.

Handles user creation/sync from Firebase Auth data,
tier management, and profile queries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Data access layer for user records."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        """Fetch a user by their Firebase UID."""
        stmt = select(User).where(User.firebase_uid == firebase_uid)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch a user by their internal UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        firebase_uid: str,
        email: str | None = None,
        display_name: str | None = None,
        photo_url: str | None = None,
    ) -> User:
        """
        Create a new user or update an existing one on login.

        This is the "sync" operation called by verify-token:
        - If the user doesn't exist → create with FREE tier
        - If the user exists → update profile fields + last_login_at
        """
        existing = await self.get_by_firebase_uid(firebase_uid)

        if existing:
            existing.email = email or existing.email
            existing.display_name = display_name or existing.display_name
            existing.photo_url = photo_url or existing.photo_url
            existing.last_login_at = datetime.now(timezone.utc)
            await self._db.flush()
            logger.info("user_synced", uid=firebase_uid)
            return existing

        user = User(
            id=uuid.uuid4(),
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
            tier="FREE",
            last_login_at=datetime.now(timezone.utc),
        )
        self._db.add(user)
        await self._db.flush()
        logger.info("user_created", uid=firebase_uid)
        return user

    async def update_tier(self, firebase_uid: str, tier: str) -> User | None:
        """Update a user's tier (FREE → PRO, or admin grant)."""
        user = await self.get_by_firebase_uid(firebase_uid)
        if user:
            user.tier = tier
            await self._db.flush()
            logger.info("user_tier_updated", uid=firebase_uid, tier=tier)
        return user
