"""
Georgian Unicode handling and text normalisation utilities.

Georgian Mkhedruli script occupies U+10D0 – U+10FF.
This module provides helpers that are aware of Georgian-specific
punctuation, numbering, and whitespace conventions used in legislation.
"""

from __future__ import annotations

import re
import unicodedata

# ── Unicode ranges ───────────────────────────────────────────

# Modern Georgian (Mkhedruli)
_MKHEDRULI_RANGE = range(0x10D0, 0x10FF + 1)

# Georgian supplement / extensions
_GEORGIAN_EXTENDED_RANGE = range(0x2D00, 0x2D2F + 1)

# Combined set for fast membership checks
GEORGIAN_CODEPOINTS: frozenset[int] = frozenset(
    list(_MKHEDRULI_RANGE) + list(_GEORGIAN_EXTENDED_RANGE)
)


def is_georgian(char: str) -> bool:
    """Return True if *char* is a Georgian-script character."""
    return ord(char) in GEORGIAN_CODEPOINTS


def contains_georgian(text: str) -> bool:
    """Return True if *text* contains at least one Georgian character."""
    return any(is_georgian(c) for c in text)


# ── Normalisation ────────────────────────────────────────────

# Collapse multiple whitespace (including non-breaking spaces) into one.
_MULTI_WS = re.compile(r"[\s\u00A0\u200B\u200C\u200D\uFEFF]+")

# Superscript digits used in Georgian legal article numbering (e.g. მუხლი 1¹).
_SUPERSCRIPT_MAP: dict[str, str] = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3",
    "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7",
    "⁸": "8", "⁹": "9",
}

# Regex for normalising superscript article numbers like "45¹" → "45-1"
_SUPERSCRIPT_RE = re.compile(r"([0-9])\s*([⁰¹²³⁴⁵⁶⁷⁸⁹]+)")


def normalise_whitespace(text: str) -> str:
    """Collapse all Unicode whitespace into single ASCII spaces and strip."""
    return _MULTI_WS.sub(" ", text).strip()


def normalise_superscripts(text: str) -> str:
    """
    Convert superscript article numbers to a canonical form.

    ``"მუხლი 45¹"``  →  ``"მუხლი 45-1"``
    """
    def _replace(m: re.Match[str]) -> str:
        base = m.group(1)
        sup = "".join(_SUPERSCRIPT_MAP.get(c, c) for c in m.group(2))
        return f"{base}-{sup}"

    return _SUPERSCRIPT_RE.sub(_replace, text)


def normalise_georgian(text: str) -> str:
    """
    Full normalisation pass for Georgian legal text.

    1. NFC Unicode normalisation
    2. Whitespace collapse
    3. Superscript digit normalisation
    4. Strip BOM
    """
    text = text.lstrip("\ufeff")  # strip BOM
    text = unicodedata.normalize("NFC", text)
    text = normalise_whitespace(text)
    text = normalise_superscripts(text)
    return text


# ── Legal numbering helpers ──────────────────────────────────

# Georgian alphabet used for sub-point lettering: ა), ბ), გ), …
GEORGIAN_ALPHABET = "აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ"

# Pattern for Georgian paragraph letters: ა), ბ.ა), etc.
_GEO_LETTER_LABEL = re.compile(
    r"^([" + GEORGIAN_ALPHABET + r"](?:\.[" + GEORGIAN_ALPHABET + r"])?)\s*\)"
)


def extract_georgian_label(text: str) -> str | None:
    """
    Extract a Georgian sub-point label (e.g. ``"ა"`` or ``"ბ.ა"``)
    from the start of *text*.  Returns ``None`` if not found.
    """
    m = _GEO_LETTER_LABEL.match(text.strip())
    return m.group(1) if m else None


# ── Article reference pattern ────────────────────────────────

# Matches references like "მუხლი 123", "მუხლი 45¹"
ARTICLE_REF_RE = re.compile(
    r"მუხლი\s+(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)",
    re.UNICODE,
)


def extract_article_references(text: str) -> list[str]:
    """
    Return all article numbers referenced in *text*.

    Example: ``"მუხლი 123-ის"`` → ``["123"]``
    """
    refs: list[str] = []
    for m in ARTICLE_REF_RE.finditer(text):
        raw = normalise_superscripts(m.group(1))
        refs.append(raw)
    return refs
