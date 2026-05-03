"""
Parse Georgian-style legal cross-references.

Handles patterns like:
  - "მუხლი 123-ის შესაბამისად" (in accordance with Article 123)
  - "ამ კოდექსის 45-ე მუხლი"   (Article 45 of this Code)
  - "მუხლი 100¹"               (Article 100-1 — superscript numbering)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.utils.georgian_text import normalise_superscripts


@dataclass(frozen=True, slots=True)
class LegalReference:
    """A single parsed legal reference."""
    article_number: str          # e.g. "123" or "45-1"
    paragraph_number: str | None = None  # e.g. "2"
    sub_point: str | None = None         # e.g. "ა"
    source_text: str = ""                # original matched substring


# ── Patterns ─────────────────────────────────────────────────

# მუხლი 123 / მუხლი 45¹ / მუხლი 100-ის
_ARTICLE_PATTERN = re.compile(
    r"მუხლი\s+"
    r"(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)"  # article number
    r"(?:\s*-?\s*ი?ს?)?"                   # optional Georgian case suffix
    r"(?:\s+(\d+)\s*\.?\s*პუნქტ)?"         # optional paragraph
    r"(?:\s*\"?([ა-ჰ])\"?\s*\)\s*ქვეპუნქტ)?",  # optional sub-point
    re.UNICODE,
)

# Reverse-order pattern: "ამ კოდექსის 45-ე მუხლი"
_REVERSE_ARTICLE_PATTERN = re.compile(
    r"(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)"
    r"\s*-?\s*ე?\s+მუხლ",
    re.UNICODE,
)


def parse_references(text: str) -> list[LegalReference]:
    """
    Extract all legal cross-references from *text*.

    Returns a deduplicated list of ``LegalReference`` objects.
    """
    seen: set[str] = set()
    refs: list[LegalReference] = []

    for m in _ARTICLE_PATTERN.finditer(text):
        art_num = normalise_superscripts(m.group(1))
        para = m.group(2)
        sub = m.group(3)
        key = f"{art_num}:{para}:{sub}"
        if key not in seen:
            seen.add(key)
            refs.append(LegalReference(
                article_number=art_num,
                paragraph_number=para,
                sub_point=sub,
                source_text=m.group(0).strip(),
            ))

    for m in _REVERSE_ARTICLE_PATTERN.finditer(text):
        art_num = normalise_superscripts(m.group(1))
        key = f"{art_num}:None:None"
        if key not in seen:
            seen.add(key)
            refs.append(LegalReference(
                article_number=art_num,
                source_text=m.group(0).strip(),
            ))

    return refs
