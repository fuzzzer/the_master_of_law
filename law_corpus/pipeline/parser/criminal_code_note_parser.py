"""Extract monetary thresholds from Criminal Code შენიშვნა (Note) sections.

Source: Parsed criminal_code.json from the pipeline.
These notes define what "large amount", "significant damage", etc. mean
in Lari for specific crime categories.

Example: Article 177 (theft) → "large amount" = > 10,000 ლარი
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MonetaryThreshold:
    article_number: str
    article_title: str
    thresholds: dict[str, int] = field(default_factory=dict)
    note_text: str = ""


def parse_criminal_code_notes(json_path: Path) -> list[MonetaryThreshold]:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    results: list[MonetaryThreshold] = []

    for article in data.get("articles", []):
        content = article.get("content_ka", "")
        if "შენიშვნა" not in content:
            continue

        note_text = content[content.find("შენიშვნა"):]
        thresholds = _extract_lari_thresholds(note_text)
        if not thresholds:
            continue

        results.append(MonetaryThreshold(
            article_number=article.get("article_number", ""),
            article_title=article.get("article_title", ""),
            thresholds=thresholds,
            note_text=note_text[:1000],
        ))

    return results


THRESHOLD_PATTERNS: list[tuple[str, str]] = [
    (r"მცირე\w*\s+ოდენობ\w*[^.]*?(\d[\d\s]*)\s*ლარ", "small_amount_lari"),
    (r"მნიშვნელოვან\w*.{0,30}(?:ზიან\w*|ოდენობ\w*)[^.]*?(\d[\d\s]*)\s*ლარ", "significant_damage_lari"),
    (r"განსაკუთრებით\s+დიდ\w*\s+ოდენობ\w*[^.]*?(\d[\d\s]*)\s*ლარ", "extra_large_amount_lari"),
    (r"(?<!განსაკუთრებით\s)დიდ\w*\s+ოდენობ\w*[^.]*?(\d[\d\s]*)\s*ლარ", "large_amount_lari"),
]


def _extract_lari_thresholds(note_text: str) -> dict[str, int]:
    found: dict[str, int] = {}

    for pattern, key in THRESHOLD_PATTERNS:
        match = re.search(pattern, note_text, re.UNICODE)
        if match:
            raw_num = match.group(1).replace(" ", "").strip()
            try:
                found[key] = int(raw_num)
            except ValueError:
                continue

    return found
