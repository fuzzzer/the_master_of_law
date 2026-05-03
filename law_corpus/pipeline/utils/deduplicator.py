"""
Content deduplication helpers.

Used to detect when the same article or chunk has been downloaded /
processed more than once (e.g. consolidated vs. original version).
"""

from __future__ import annotations

import hashlib


def content_hash(text: str) -> str:
    """Return a SHA-256 hex digest of *text* (UTF-8 encoded)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_hash_short(text: str, length: int = 12) -> str:
    """Shorter hash suitable for IDs and filenames."""
    return content_hash(text)[:length]


class DeduplicationIndex:
    """
    In-memory set of content hashes for fast duplicate detection.

    Can optionally be persisted to / loaded from a file.
    """

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_duplicate(self, text: str) -> bool:
        """Return True if *text* was already seen."""
        h = content_hash(text)
        if h in self._seen:
            return True
        self._seen.add(h)
        return False

    def add(self, text: str) -> None:
        """Register *text* without performing a duplicate check."""
        self._seen.add(content_hash(text))

    @property
    def count(self) -> int:
        return len(self._seen)
