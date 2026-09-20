"""
Who the caller is when there is no login.

v1 ships without accounts: anyone may use the app, and each user pays for
their own model calls with their own Google key. There is still a need for a
STABLE per-caller identity, because cases, conversations and messages are all
owned by a user row — without one, every device would share a single pile of
legal matters, which for this app is a privacy failure rather than a cosmetic
bug.

The identity is the device id the client generates once and stores locally.
It is not a credential and proves nothing: anyone who copies another device's
id sees that device's cases. That is the accepted trade for shipping without
accounts, and it is exactly what real login (already built, just switched off
via AUTH_ENABLED) replaces later — the user row is keyed the same way, so the
migration is a re-key of firebase_uid rather than a data model change.
"""

from __future__ import annotations

import hashlib

from app.utils.logger import get_logger

logger = get_logger(__name__)

ANON_UID_PREFIX = "anon:"
# String(128) column; device ids are client-generated so they get truncated
# rather than trusted to be short.
_MAX_DEVICE_ID = 100


def anonymous_uid(device_id: str | None, client_host: str | None) -> str:
    """Build the stable uid for an unauthenticated caller.

    Falls back to a hash of the client address when the client sends no device
    id. The fallback is deliberately weak — several users behind one NAT share
    a uid and therefore each other's cases — so it exists only to keep older
    app builds working, not as a supported mode. Clients SHOULD send the
    header; the log line below is how we notice ones that don't.
    """
    cleaned = (device_id or "").strip()[:_MAX_DEVICE_ID]
    if cleaned:
        return f"{ANON_UID_PREFIX}{cleaned}"

    host = (client_host or "unknown").encode()
    digest = hashlib.sha256(host).hexdigest()[:32]
    logger.info("anon_identity_ip_fallback", digest=digest)
    return f"{ANON_UID_PREFIX}ip-{digest}"


async def ensure_user_row(uid: str) -> str:
    """Create the caller's user row on first sight. Returns their tier.

    Idempotent and safe under concurrency: the app fires several requests the
    moment it opens, so two of them racing to create the same brand-new user
    is the normal case, not an edge case. The loser of that race hits the
    unique constraint on firebase_uid and re-reads instead of failing.
    """
    from sqlalchemy.exc import IntegrityError

    from app.models.database import get_session_factory
    from app.repositories.user_repository import UserRepository

    factory = get_session_factory()
    async with factory() as db:
        repo = UserRepository(db)
        user = await repo.get_by_firebase_uid(uid)
        if user:
            return user.tier

        try:
            user = await repo.create_or_update(firebase_uid=uid)
            await db.commit()
            return user.tier
        except IntegrityError:
            await db.rollback()
            user = await repo.get_by_firebase_uid(uid)
            return user.tier if user else "FREE"
