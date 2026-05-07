#!/usr/bin/env python3
"""
Extract evaluation test cases from processed Georgian court decisions.

Approach:
  1. Split each case into FACTS (აღწერილობითი ნაწილი) and COURT DECISION
  2. The FACTS become the input to the AI legal assistant
  3. The COURT DECISION is the ground truth to compare against
  4. The AI should assess: what legal outcome is most likely?
  5. Compare AI's assessment vs actual court ruling → quality score

Georgian court decision structure:
  ┌─ Header (case #, date, court chamber)
  ├─ აღწერილობითი ნაწილი (Facts - what happened)
  ├─ სამოტივაციო ნაწილი (Court's legal reasoning)
  └─ დ ა ა დ გ ი ნ ა / სარეზოლუციო (Resolution/verdict)

For evaluation:
  - Input to AI:  Header + Facts section
  - Ground truth: Court reasoning + Resolution

Usage:
  python3 extract_test_cases.py                    # Extract top 50
  python3 extract_test_cases.py --top 80           # More cases
  python3 extract_test_cases.py --only criminal    # One category
  python3 extract_test_cases.py --preview FILE     # Preview one file
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROCESSED_DIR = BASE_DIR / "processed"
OUTPUT_FILE = BASE_DIR / "cases.json"

# ─────────────────────────────────────────────
# Section delimiters
# ─────────────────────────────────────────────

# Patterns that mark section boundaries in Georgian court texts
FACTS_START = re.compile(r'აღწერილობით\w*\s*(?:ნაწილი|[-–])', re.IGNORECASE)
REASONING_START = re.compile(r'სამოტივაციო\s*ნაწილი', re.IGNORECASE)
# The resolution uses spaced-out letters: დ ა ა დ გ ი ნ ა
RESOLUTION_START = re.compile(r'დ\s*ა\s*ა\s*დ\s*გ\s*ი\s*ნ\s*ა\s*:', re.IGNORECASE)
# Also match non-spaced variants
RESOLUTION_ALT = re.compile(r'სარეზოლუციო\s*ნაწილი', re.IGNORECASE)

# Case number
CASE_NUM = re.compile(r'#([\w\-]+)')
# Date
DATE_PATTERN = re.compile(
    r'(\d{1,2})\s+'
    r'(იანვარი|თებერვალი|მარტი|აპრილი|მაისი|ივნისი|'
    r'ივლისი|აგვისტო|სექტემბერი|ოქტომბერი|ნოემბერი|დეკემბერი)'
    r',?\s*(\d{4})',
)
MONTH_MAP = {
    "იანვარი": 1, "თებერვალი": 2, "მარტი": 3, "აპრილი": 4,
    "მაისი": 5, "ივნისი": 6, "ივლისი": 7, "აგვისტო": 8,
    "სექტემბერი": 9, "ოქტომბერი": 10, "ნოემბერი": 11, "დეკემბერი": 12,
}

# Subject of dispute
SUBJECT_PATTERN = re.compile(r'დავის\s+საგანი:\s*(.+?)(?:\n|აღწერილობითი)', re.DOTALL)

# Article references: სსკ-ის 177-ე მუხლი, სმკ-ის 405-ე მუხლი
ARTICLE_PATTERN = re.compile(r'(\d+)[\-ეი]*\s*მუხლ')

# Verdict keywords
VERDICT_PATTERNS = [
    (re.compile(r'საკასაციო\s+საჩივარი?\s+არ\s+(?:უნდა\s+)?დაკმაყოფილდეს?'), "საკასაციო საჩივარი არ დაკმაყოფილდა"),
    (re.compile(r'საკასაციო\s+საჩივარი?\s+(?:უნდა\s+)?დაკმაყოფილდეს?\s+ნაწილობრივ'), "ნაწილობრივ დაკმაყოფილდა"),
    (re.compile(r'საკასაციო\s+საჩივარი?\s+(?:უნდა\s+)?დაკმაყოფილდეს?'), "საკასაციო საჩივარი დაკმაყოფილდა"),
    (re.compile(r'სარჩელი?\s+არ\s+დაკმაყოფილდეს?'), "სარჩელი არ დაკმაყოფილდა"),
    (re.compile(r'სარჩელი?\s+დაკმაყოფილდეს?\s+ნაწილობრივ'), "სარჩელი ნაწილობრივ დაკმაყოფილდა"),
    (re.compile(r'სარჩელი?\s+(?:უნდა\s+)?დაკმაყოფილდეს?'), "სარჩელი დაკმაყოფილდა"),
    (re.compile(r'განაჩენი?\s+(?:უცვლელად\s+)?დარჩეს?\s+ძალაში'), "განაჩენი ძალაში დარჩა"),
    (re.compile(r'განაჩენი?\s+გაუქმდეს?'), "განაჩენი გაუქმდა"),
    (re.compile(r'განაჩენში?\s+(?:უნდა\s+)?შევიდეს?\s+ცვლილება'), "განაჩენში შევიდა ცვლილება"),
    (re.compile(r'გადაწყვეტილება\s+გაუქმდეს?'), "გადაწყვეტილება გაუქმდა"),
    (re.compile(r'არაკონსტიტუციურ(?:ად)?\s+იქნეს?\s+ცნობილ'), "არაკონსტიტუციურად ცნობილი"),
    (re.compile(r'არ\s+დაკმაყოფილდეს?'), "არ დაკმაყოფილდა"),
    (re.compile(r'დაკმაყოფილდეს?\s+ნაწილობრივ'), "ნაწილობრივ დაკმაყოფილდა"),
    (re.compile(r'საჩივარი?\s+დაუშვებლად'), "საჩივარი დაუშვებლად ცნობილი"),
]


def split_case_sections(text: str) -> dict:
    """
    Split a court decision into its standard sections.

    Returns dict with:
      - header: Case number, date, court chamber
      - facts: აღწერილობითი ნაწილი (what happened - this goes to AI)
      - reasoning: სამოტივაციო ნაწილი (court's legal analysis)
      - resolution: Final ruling (ground truth verdict)
    """
    sections = {"header": "", "facts": "", "reasoning": "", "resolution": ""}

    # Find section boundaries
    facts_match = FACTS_START.search(text)
    reasoning_match = REASONING_START.search(text)
    resolution_match = RESOLUTION_START.search(text)
    if not resolution_match:
        resolution_match = RESOLUTION_ALT.search(text)

    # Extract header (everything before facts)
    if facts_match:
        sections["header"] = text[:facts_match.start()].strip()
    else:
        sections["header"] = text[:500].strip()

    # Extract facts section
    if facts_match and reasoning_match:
        sections["facts"] = text[facts_match.start():reasoning_match.start()].strip()
    elif facts_match and resolution_match:
        sections["facts"] = text[facts_match.start():resolution_match.start()].strip()
    elif facts_match:
        # No clear end marker — take first 60% of text
        end = int(len(text) * 0.6)
        sections["facts"] = text[facts_match.start():end].strip()

    # Extract reasoning
    if reasoning_match and resolution_match:
        sections["reasoning"] = text[reasoning_match.start():resolution_match.start()].strip()
    elif reasoning_match:
        sections["reasoning"] = text[reasoning_match.start():].strip()

    # Extract resolution
    if resolution_match:
        sections["resolution"] = text[resolution_match.start():].strip()

    return sections


def extract_verdict(resolution: str) -> str:
    """Extract the verdict from the resolution section."""
    for pattern, label in VERDICT_PATTERNS:
        if pattern.search(resolution):
            return label
    return ""


def extract_case(filepath: Path, category: str) -> dict | None:
    """Extract a structured test case from a processed court decision file."""
    text = filepath.read_text(encoding="utf-8", errors="replace")

    if len(text) < 500:
        return None

    # Split into sections
    sections = split_case_sections(text)

    if not sections["facts"]:
        return None

    # --- Metadata from header ---
    header = sections["header"]
    num_match = CASE_NUM.search(header)
    case_number = num_match.group(1) if num_match else filepath.stem

    date_match = DATE_PATTERN.search(header)
    case_date = None
    case_year = None
    if date_match:
        day, month_name, year = date_match.group(1), date_match.group(2), date_match.group(3)
        month = MONTH_MAP.get(month_name, 0)
        case_date = f"{year}-{month:02d}-{int(day):02d}"
        case_year = int(year)

    # Subject
    subject = ""
    subj_match = SUBJECT_PATTERN.search(text[:2000])
    if subj_match:
        subject = subj_match.group(1).strip()[:300]

    # Articles
    articles = sorted(set(ARTICLE_PATTERN.findall(text)), key=lambda x: int(x))

    # Verdict from resolution
    verdict = extract_verdict(sections.get("resolution", ""))

    # --- Quality check ---
    # Must have: facts section, and ideally a verdict
    if len(sections["facts"]) < 200:
        return None

    return {
        "case_id": f"{category[:4].upper()}-{case_number}",
        "case_number": case_number,
        "category": category,
        "date": case_date,
        "year": case_year,
        "court": "საქართველოს უზენაესი სასამართლო",
        "subject": subject,

        # THE KEY FIELDS for evaluation:
        "situation": sections["header"] + "\n\n" + sections["facts"],
        "court_reasoning": sections["reasoning"],
        "court_resolution": sections["resolution"],
        "verdict": verdict,
        "articles_applied": articles[:15],

        # Metadata
        "source_file": filepath.name,
        "facts_length": len(sections["facts"]),
        "total_length": len(text),
    }


def score_case(case: dict) -> int:
    """Score how good this case is for evaluation."""
    score = 0
    if case.get("verdict"):
        score += 40                        # Has clear verdict — critical
    if case.get("court_reasoning"):
        score += 20                        # Has reasoning section
    if case.get("articles_applied"):
        score += min(len(case["articles_applied"]) * 3, 15)
    if case.get("subject"):
        score += 10                        # Has subject description
    if case.get("year") and case["year"] >= 2023:
        score += 10                        # Recent case
    if 3000 <= case.get("facts_length", 0) <= 30000:
        score += 10                        # Good facts length
    elif case.get("facts_length", 0) > 30000:
        score += 5
    return score


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract eval test cases from Georgian court decisions")
    parser.add_argument("--only", choices=["criminal", "civil", "administrative", "constitutional"])
    parser.add_argument("--preview", type=str, help="Preview one file")
    parser.add_argument("--top", type=int, default=50, help="Number of cases (default: 50)")
    parser.add_argument("--min-score", type=int, default=40, help="Minimum quality score")
    args = parser.parse_args()

    print("=" * 60)
    print("🏛️  Test Case Extractor")
    print("=" * 60)

    # --- Single file preview ---
    if args.preview:
        fp = Path(args.preview)
        cat = next((c for c in ["criminal", "civil", "administrative", "constitutional"] if c in str(fp)), "unknown")
        case = extract_case(fp, cat)
        if case:
            preview = {k: (v[:300] + "..." if isinstance(v, str) and len(v) > 300 else v) for k, v in case.items()}
            preview["quality_score"] = score_case(case)
            print(json.dumps(preview, indent=2, ensure_ascii=False))
        else:
            print("⚠️  Could not extract case from this file")
        return

    # --- Batch extraction ---
    all_cases = []
    categories = ["criminal", "civil", "administrative"]
    if args.only:
        categories = [args.only] if args.only != "constitutional" else []

    for category in categories:
        cat_dir = PROCESSED_DIR / "supreme_court" / category
        if not cat_dir.exists():
            continue
        files = sorted(cat_dir.glob("*.txt"))
        print(f"\n📁 {category.upper()} — {len(files)} files")
        extracted = 0
        for fp in files:
            case = extract_case(fp, category)
            if case:
                case["quality_score"] = score_case(case)
                all_cases.append(case)
                extracted += 1
        print(f"   ✅ Extracted: {extracted}")

    # Constitutional
    if not args.only or args.only == "constitutional":
        cc_dir = PROCESSED_DIR / "constitutional_court"
        if cc_dir.exists():
            files = sorted(cc_dir.glob("*.txt"))
            print(f"\n📁 CONSTITUTIONAL — {len(files)} files")
            for fp in files:
                case = extract_case(fp, "constitutional")
                if case:
                    case["quality_score"] = score_case(case)
                    all_cases.append(case)

    # Filter and rank
    qualified = [c for c in all_cases if c["quality_score"] >= args.min_score]
    qualified.sort(key=lambda c: c["quality_score"], reverse=True)

    # Take top N with category diversity
    selected = qualified[:args.top]

    # Stats
    by_cat = {}
    by_verdict = {}
    for c in selected:
        by_cat[c["category"]] = by_cat.get(c["category"], 0) + 1
        v = c.get("verdict", "unknown") or "unknown"
        by_verdict[v] = by_verdict.get(v, 0) + 1

    # Save
    output = {
        "generated_at": datetime.now().isoformat(),
        "purpose": "Evaluate AI legal assistant quality by comparing its analysis against real Supreme Court rulings",
        "methodology": (
            "For each case: (1) Send 'situation' text to AI as if a user describing their legal problem, "
            "(2) AI produces legal assessment and recommended strategy, "
            "(3) Compare AI response with 'court_reasoning' and 'verdict' for accuracy"
        ),
        "total_cases": len(selected),
        "by_category": by_cat,
        "by_verdict": by_verdict,
        "cases": selected,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n{'='*60}")
    print(f"✅ {len(selected)} test cases → {OUTPUT_FILE}")
    print(f"{'='*60}")
    print(f"\n  📊 By category:")
    for cat, n in sorted(by_cat.items()):
        print(f"      {cat:20s}: {n}")
    print(f"\n  ⚖️  By verdict:")
    for v, n in sorted(by_verdict.items(), key=lambda x: -x[1]):
        print(f"      {v:40s}: {n}")
    print(f"\n  📈 Score range: {selected[-1]['quality_score']}–{selected[0]['quality_score']}")

    # Show samples
    print(f"\n  📝 Sample cases:")
    for c in selected[:5]:
        print(f"    [{c['category']:13s}] {c['case_id']:25s} | {c['verdict'][:35]:35s} | facts={c['facts_length']:,} chars")


if __name__ == "__main__":
    main()
