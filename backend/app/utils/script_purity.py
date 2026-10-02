"""
Find letters of another script inside a Georgian answer.

Models — the lite ones especially — sometimes write a Cyrillic, Greek or
Armenian letter or word into Georgian text (QA, 2026-10-01: `задნებით`,
`ακριβώς`, `მიեր`). Latin is not counted: links, code names and "AI" are
expected. An answer that is mostly in another script (a Russian question
answered in Russian) is not a Georgian answer and is left alone.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"\w+", re.UNICODE)


def _is_georgian(ch: str) -> bool:
    return "Ⴀ" <= ch <= "ჿ" or "Ა" <= ch <= "Ჿ"


def _is_foreign(ch: str) -> bool:
    return (
        "Ѐ" <= ch <= "ԯ"      # Cyrillic
        or "Ͱ" <= ch <= "Ͽ"   # Greek
        or "ἀ" <= ch <= "῿"   # Greek extended
        or "԰" <= ch <= "֏"   # Armenian
    )


def foreign_script_words(text: str) -> list[str]:
    """Words of a Georgian text that contain Cyrillic, Greek or Armenian letters."""
    words = _WORD.findall(text)
    georgian = sum(1 for w in words if any(_is_georgian(c) for c in w))
    foreign = [w for w in words if any(_is_foreign(c) for c in w)]
    if georgian <= len(foreign):
        return []
    return list(dict.fromkeys(foreign))
