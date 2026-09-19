"""Generate threshold_catalog.json from parsed legal sources.

Reads:
  1. Narcotics Law PDF → drug quantity thresholds
  2. Criminal Code JSON → monetary thresholds from შენიშვნა notes
  3. Existing catalog → non-drug/non-monetary entries (kept as-is)

Writes:
  law_corpus/data/thresholds/threshold_catalog.json

Usage:
  python3 scripts/generate_threshold_catalog.py              # write
  python3 scripts/generate_threshold_catalog.py --dry-run    # preview
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.parser.narcotics_table_parser import DrugQuantityRow, parse_narcotics_pdf
from pipeline.parser.criminal_code_note_parser import MonetaryThreshold, parse_criminal_code_notes


PROJECT_ROOT = Path(__file__).parent.parent
NARCOTICS_PDF_DIR = PROJECT_ROOT.parent / ".assets"
CRIMINAL_CODE_JSON = PROJECT_ROOT / "data" / "georgian_laws" / "parsed" / "criminal_code.json"
CATALOG_PATH = PROJECT_ROOT / "data" / "thresholds" / "threshold_catalog.json"

NARCOTICS_LAW_URL = "https://matsne.gov.ge/ka/document/view/1670322"
CRIMINAL_CODE_URL = "https://matsne.gov.ge/ka/document/view/16426"
TODAY = "2026-05-09"


def find_narcotics_pdf() -> Path:
    pdfs = list(NARCOTICS_PDF_DIR.glob("ნარკოტიკული*"))
    if not pdfs:
        raise FileNotFoundError(f"Narcotics Law PDF not found in {NARCOTICS_PDF_DIR}")
    return pdfs[0]


def drug_row_to_catalog_entry(row: DrugQuantityRow) -> dict:
    entry_id = f"drug_{row.section}_{row.row_number.replace(' ', '_')}"

    values: dict[str, str] = {}
    no_quantity = row.small_grams is None and row.large_grams is None and row.extra_large_grams is None

    if row.small_grams:
        values["მცირე_ოდენობა"] = f"≤ {row.small_grams} გრამი"
    if row.large_grams:
        values["დიდი_ოდენობა_ზღვარი"] = f"{row.large_grams} გრამი"
    if row.extra_large_grams:
        values["განსაკუთრებით_დიდი_ოდენობა_ზღვარი"] = f"{row.extra_large_grams} გრამი"
    if no_quantity:
        values["შენიშვნა"] = "ოდენობა განსაზღვრული არ არის — ნებისმიერი ოდენობა = სისხლის სამართლის პასუხისმგებლობა"

    consequence = _build_drug_consequence(row, no_quantity)

    return {
        "id": entry_id,
        "type": "legal_threshold",
        "code_name": "ნარკოტიკული საშუალებების შესახებ კანონი",
        "article_number": "დანართი №2",
        "threshold_type": "drug_quantity",
        "description_ka": f"ნარკოტიკული საშუალების ოდენობა — {row.substance_ka}",
        "substance": row.substance_ka,
        "values": values,
        "consequence_ka": consequence,
        "source_url": NARCOTICS_LAW_URL,
        "last_verified": TODAY,
    }


def _build_drug_consequence(row: DrugQuantityRow, no_quantity: bool) -> str:
    if no_quantity:
        return "ნებისმიერი ოდენობა — სისხლის სამართლის პასუხისმგებლობა (სსკ მუხლი 260)"

    parts = []
    if row.small_grams:
        parts.append(f"≤{row.small_grams}გ → მცირე ოდენობა (სსკ 273)")
    if row.small_grams and row.large_grams:
        parts.append(f">{row.small_grams}გ–{row.large_grams}გ → სისხლის სამართლის საწყისი (სსკ 260)")
    elif row.large_grams:
        parts.append(f"≤{row.large_grams}გ → დიდი ოდენობა")
    if row.large_grams and row.extra_large_grams:
        parts.append(f">{row.large_grams}გ–{row.extra_large_grams}გ → დიდი ოდენობა (სსკ 260²)")
    if row.extra_large_grams:
        parts.append(f">{row.extra_large_grams}გ → განსაკუთრებით დიდი (სსკ 260³)")
    return "; ".join(parts)


def monetary_threshold_to_catalog_entry(item: MonetaryThreshold) -> dict:
    entry_id = f"criminal_monetary_{item.article_number.replace(' ', '_').replace('მუხლი_', '')}"

    values = {}
    label_map = {
        "small_amount_lari": "მცირე ოდენობა",
        "significant_damage_lari": "მნიშვნელოვანი ზიანი",
        "large_amount_lari": "დიდი ოდენობა",
        "extra_large_amount_lari": "განსაკუთრებით დიდი ოდენობა",
    }
    for key, amount in item.thresholds.items():
        label = label_map.get(key, key)
        values[label] = f"> {amount:,} ლარი"

    return {
        "id": entry_id,
        "type": "legal_threshold",
        "code_name": "სისხლის სამართლის კოდექსი",
        "article_number": item.article_number,
        "threshold_type": "monetary_limit",
        "description_ka": f"ფულადი ზღვრები — {item.article_title}",
        "substance": None,
        "values": values,
        "consequence_ka": f"დეტალები იხ. {item.article_number}, შენიშვნა",
        "source_url": CRIMINAL_CODE_URL,
        "last_verified": TODAY,
    }


def load_existing_non_replaceable_entries() -> list[dict]:
    if not CATALOG_PATH.exists():
        return []
    with open(CATALOG_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return [
        entry for entry in data.get("thresholds", [])
        if entry.get("threshold_type") not in ("drug_quantity", "monetary_limit")
    ]


def generate(*, dry_run: bool = False) -> dict:
    narcotics_pdf = find_narcotics_pdf()
    print(f"Narcotics PDF: {narcotics_pdf.name}")

    drug_rows = parse_narcotics_pdf(narcotics_pdf)
    active_drug_rows = [r for r in drug_rows if not r.is_removed]
    print(f"Drug rows: {len(drug_rows)} total, {len(active_drug_rows)} active")

    cc_thresholds = parse_criminal_code_notes(CRIMINAL_CODE_JSON)
    print(f"Criminal Code monetary thresholds: {len(cc_thresholds)} articles")

    drug_entries = [drug_row_to_catalog_entry(r) for r in active_drug_rows]
    monetary_entries = [monetary_threshold_to_catalog_entry(t) for t in cc_thresholds]
    kept_entries = load_existing_non_replaceable_entries()
    print(f"Kept from existing catalog: {len(kept_entries)} entries")

    catalog = {
        "version": "2.0.0",
        "last_updated": TODAY,
        "source": "Auto-extracted: Narcotics Law PDF (drug quantities) + Criminal Code JSON (monetary thresholds)",
        "thresholds": drug_entries + monetary_entries + kept_entries,
    }

    total = len(catalog["thresholds"])
    print(f"\nTotal: {total} entries ({len(drug_entries)} drug + {len(monetary_entries)} monetary + {len(kept_entries)} kept)")

    if dry_run:
        print("\n[DRY RUN] Not writing to disk.")
        return catalog

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Written: {CATALOG_PATH}")

    return catalog


if __name__ == "__main__":
    generate(dry_run="--dry-run" in sys.argv)
