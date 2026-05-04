"""
Georgian text utilities.

Handles Georgian (Mkhedruli script, U+10D0–U+10FF) text operations
correctly. Never uses ASCII-only operations on Georgian text.
"""

from __future__ import annotations

import re
import unicodedata


def is_georgian(text: str) -> bool:
    """Check if text contains Georgian characters."""
    return bool(re.search(r"[\u10D0-\u10FF]", text))


def normalize_georgian(text: str) -> str:
    """Normalize Georgian text — NFC normalization + whitespace cleanup."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_georgian_tokens(text: str) -> list[str]:
    """Extract Georgian word tokens from text."""
    # Georgian word pattern (Mkhedruli characters)
    return re.findall(r"[\u10D0-\u10FF]+", text)


def truncate_safe(text: str, max_chars: int = 1000) -> str:
    """Truncate text at a word boundary to avoid splitting Georgian characters."""
    if len(text) <= max_chars:
        return text
    # Find the last space before max_chars
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.7:
        return truncated[:last_space] + "…"
    return truncated + "…"
