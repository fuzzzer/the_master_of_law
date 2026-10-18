"""Parse the drug quantity table (დანართი №2) from the Narcotics Law PDF.

Source: https://matsne.gov.ge/ka/document/view/1670322
Table location: Appendix №2, pages 34–42 in the consolidated PDF.

The table has 5 columns:
  №  |  Substance name  |  Small qty (გრამი)  |  Large qty  |  Extra-large qty

Column interpretation (from table notes):
  - col3 and below = მცირე ოდენობა (small — administrative, სსკ 273)
  - above col3 up to col4 = სისხლის სამართლის საწყისი (criminal start, სსკ 260)
  - above col4 up to col5 = დიდი ოდენობა (large, სსკ 260²)
  - above col5 = განსაკუთრებით დიდი (extra-large, სსკ 260³)
  - empty col3 → col4 = large quantity boundary directly
  - '-' in all columns → any amount triggers criminal liability
  - quantities are pure substance, without fillers
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pdfplumber


TABLE_START_PAGE = 33  # 0-indexed; page 34 in the PDF
TABLE_END_PAGE = 42    # inclusive


@dataclass
class DrugQuantityRow:
    row_number: str
    substance_ka: str
    small_grams: str | None
    large_grams: str | None
    extra_large_grams: str | None
    section: str  # "narcotics" or "psychotropic"
    is_removed: bool


def parse_narcotics_pdf(pdf_path: Path) -> list[DrugQuantityRow]:
    rows: list[DrugQuantityRow] = []
    section = "narcotics"

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx in range(TABLE_START_PAGE, min(TABLE_END_PAGE + 1, len(pdf.pages))):
            for table in pdf.pages[page_idx].extract_tables():
                if not table:
                    continue
                for raw_row in table:
                    parsed = _try_parse_row(raw_row, section)
                    if parsed == "narcotics":
                        section = "narcotics"
                    elif parsed == "psychotropic":
                        section = "psychotropic"
                    elif isinstance(parsed, DrugQuantityRow):
                        rows.append(parsed)

    return rows


def _try_parse_row(
    raw_row: list[str | None], section: str
) -> DrugQuantityRow | str | None:
    if not raw_row or len(raw_row) < 2:
        return None

    row_text = " ".join(str(c or "") for c in raw_row)

    if "ნარკოტიკული საშუალებები" in row_text:
        return "narcotics"
    if "ფსიქოტროპული ნივთიერებ" in row_text:
        return "psychotropic"

    first_cell = str(raw_row[0] or "").strip()
    if first_cell in ("№", "N", "") or "მცირე" in row_text or "ოდენობა" in row_text:
        return None

    try:
        int(first_cell.split()[0])
    except (ValueError, IndexError):
        return None

    if len(raw_row) < 5:
        return None

    name_raw = str(raw_row[1] or "").strip()
    name_ka = name_raw.split("\n")[0].strip()

    if not any("\u10d0" <= ch <= "\u10ff" for ch in name_ka):
        return None

    is_removed = "(ამოღებულია" in name_raw

    return DrugQuantityRow(
        row_number=first_cell,
        substance_ka=name_ka,
        small_grams=_normalize_qty(raw_row[2]),
        large_grams=_normalize_qty(raw_row[3]),
        extra_large_grams=_normalize_qty(raw_row[4]),
        section=section,
        is_removed=is_removed,
    )


def _normalize_qty(raw: str | None) -> str | None:
    val = str(raw or "").strip()
    if val in ("-", "_", "", "None"):
        return None
    if "\n" in val:
        val = val.split("\n")[-1].strip()
    return val
