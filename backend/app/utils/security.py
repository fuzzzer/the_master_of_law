"""
Security utilities — input sanitization and token helpers.
"""

from __future__ import annotations

import re
import secrets
import string


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input text.

    - Strips leading/trailing whitespace
    - Removes null bytes
    - Limits length
    - Preserves Georgian characters (U+10D0-U+10FF)
    """
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text


def generate_secret_key(length: int = 32) -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(length)


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID format."""
    pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    return bool(pattern.match(value))
