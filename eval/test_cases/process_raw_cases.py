#!/usr/bin/env python3
"""
Process raw court case files into individual structured case files.

This script:
  1. Reads Supreme Court PDFs (criminal, civil, administrative)
  2. Splits each PDF into individual case texts using boundary patterns
  3. Reads Constitutional Court HTML files and extracts case content
  4. Saves each case as an individual text file in processed/
  5. Generates a processing manifest with statistics

Input:  eval/test_cases/raw/
Output: eval/test_cases/processed/
        eval/test_cases/processing_manifest.json

Dependencies: pdfplumber (pip install pdfplumber)
"""

import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

# ─────────────────────────────────────────────
# HTML text extraction
# ─────────────────────────────────────────────

class HTMLTextExtractor(HTMLParser):
    """Extract clean text from HTML, stripping tags."""
    def __init__(self):
        super().__init__()
        self.result = []
        self._skip = False
        self._skip_tags = {"script", "style", "head", "nav", "footer"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False
        if tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self.result.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.result.append(data)

    def get_text(self):
        return "".join(self.result)


def html_to_text(html: str) -> str:
    """Convert HTML to clean text."""
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    text = extractor.get_text()
    # Collapse excessive whitespace but preserve paragraph breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


# ─────────────────────────────────────────────
# Supreme Court PDF processing
# ─────────────────────────────────────────────

# Pattern: "ganaCeni saqarTvelos saxeliT" or "ganCineba saqarTvelos saxeliT"
# marks the start of each new case decision
CASE_START_PATTERN = re.compile(
    r'(?:ganaCeni|ganCineba|dadgenileba)\s+'
    r'saqarTvelos\s+saxeliT',
    re.IGNORECASE
)

# Case number pattern: #943ap-24 or #as-287-2021 etc.
CASE_NUMBER_PATTERN = re.compile(
    r'#([\w\-]+(?:ap|as|bs)\-\d+[\w\-]*)',
    re.IGNORECASE
)

# Broader case number - any # followed by alphanum-dash
CASE_NUMBER_BROAD = re.compile(r'#([\w][\w\-]+\d+)')

# Date pattern: "24 Tebervali, 2025 w."
DATE_PATTERN = re.compile(
    r'(\d{1,2})\s+'
    r'(ianvari|Tebervali|marti|aprili|maisi|ivnisi|'
    r'ivlisi|agvisto|seqtemberi|oqtomberi|noemberi|dekemberi)'
    r',?\s*(\d{4})\s*w\.',
    re.IGNORECASE
)

MONTH_MAP = {
    "ianvari": 1, "Tebervali": 2, "marti": 3, "aprili": 4,
    "maisi": 5, "ivnisi": 6, "ivlisi": 7, "agvisto": 8,
    "seqtemberi": 9, "oqtomberi": 10, "noemberi": 11, "dekemberi": 12,
}

# Article reference patterns: ssk-is XXX-e muxlis (Criminal Code article)
ARTICLE_PATTERN = re.compile(
    r'(?:ssk|smk|ssk|sskk|sapk|sakodk|ask)\-is\s+'
    r'(?:me\-)?(\d+[\w]*)\-?\w*\s+muxl',
    re.IGNORECASE
)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract full text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
        sys.exit(1)

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"[PAGE_{i+1}]\n{page_text}")

    return "\n\n".join(text_parts)


def split_pdf_into_cases(full_text: str, source_file: str) -> list[dict]:
    """
    Split extracted PDF text into individual case decisions.
    Returns list of case dicts with raw text and metadata.
    """
    # Find all case start positions
    starts = []
    for match in CASE_START_PATTERN.finditer(full_text):
        starts.append(match.start())

    if not starts:
        print(f"  ⚠️  No case boundaries found in {source_file}")
        return []

    cases = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(full_text)
        case_text = full_text[start:end].strip()

        # Extract case number
        case_num_match = CASE_NUMBER_PATTERN.search(case_text[:500])
        if not case_num_match:
            case_num_match = CASE_NUMBER_BROAD.search(case_text[:500])

        case_number = case_num_match.group(1) if case_num_match else f"unknown_{i+1}"

        # Extract date
        date_match = DATE_PATTERN.search(case_text[:500])
        case_date = None
        if date_match:
            day = int(date_match.group(1))
            month = MONTH_MAP.get(date_match.group(2), 0)
            year = int(date_match.group(3))
            case_date = f"{year}-{month:02d}-{day:02d}"

        # Extract article references
        articles = list(set(ARTICLE_PATTERN.findall(case_text)))

        # Determine decision type from header
        decision_type = "ganaCeni"  # verdict (default)
        if case_text.lower().startswith("gancineba"):
            decision_type = "ganCineba"  # ruling
        elif case_text.lower().startswith("dadgenileba"):
            decision_type = "dadgenileba"  # decree

        cases.append({
            "case_number": case_number,
            "decision_type": decision_type,
            "date": case_date,
            "articles_referenced": sorted(articles),
            "text_length": len(case_text),
            "page_count_approx": case_text.count("[PAGE_") + 1,
            "source_file": source_file,
            "text": case_text,
        })

    return cases


def process_supreme_court_pdfs(manifest: list) -> list[dict]:
    """Process all Supreme Court PDF files."""
    all_cases = []
    sc_dir = RAW_DIR / "supreme_court"

    for category in ["criminal", "civil", "administrative"]:
        cat_dir = sc_dir / category
        if not cat_dir.exists():
            print(f"  ⚠️  Directory not found: {cat_dir}")
            continue

        pdf_files = sorted(cat_dir.glob("*.pdf"))
        if not pdf_files:
            print(f"  ⚠️  No PDFs in {cat_dir}")
            continue

        print(f"\n📁 Processing Supreme Court — {category.upper()} ({len(pdf_files)} files)")

        for pdf_path in pdf_files:
            print(f"  📄 {pdf_path.name}...", end=" ", flush=True)

            full_text = extract_text_from_pdf(pdf_path)
            cases = split_pdf_into_cases(full_text, pdf_path.name)

            # Save individual cases
            out_dir = PROCESSED_DIR / "supreme_court" / category
            out_dir.mkdir(parents=True, exist_ok=True)

            for case in cases:
                # Create clean filename
                safe_num = re.sub(r'[^\w\-]', '_', case["case_number"])
                filename = f"{safe_num}.txt"
                out_path = out_dir / filename

                # Write case text
                out_path.write_text(case["text"], encoding="utf-8")

                # Add to manifest (without full text)
                case_meta = {k: v for k, v in case.items() if k != "text"}
                case_meta["output_file"] = str(out_path.relative_to(BASE_DIR))
                case_meta["category"] = category
                case_meta["source"] = "supreme_court"
                manifest.append(case_meta)

            all_cases.extend(cases)
            print(f"→ {len(cases)} cases extracted")

    return all_cases


# ─────────────────────────────────────────────
# Constitutional Court HTML processing
# ─────────────────────────────────────────────

# Georgian text patterns for CC cases
CC_CASE_NUMBER = re.compile(r'[N№]\s*(\d+/\d+/\d+)')
CC_OUTCOME_PATTERNS = [
    (re.compile(r'არ\s+დაკმაყოფილდეს?', re.IGNORECASE), "არ დაკმაყოფილდა"),
    (re.compile(r'დაკმაყოფილდეს?\s+ნაწილობრივ', re.IGNORECASE), "ნაწილობრივ დაკმაყოფილდა"),
    (re.compile(r'დაკმაყოფილდეს?\b', re.IGNORECASE), "დაკმაყოფილდა"),
    (re.compile(r'არაკონსტიტუციურ(?:ად)?\s+იქნეს?\s+ცნობილ', re.IGNORECASE), "არაკონსტიტუციურად ცნობილი"),
    (re.compile(r'არ\s+(?:იქნა|იქნეს)\s+მიღებული\s+არსებითად', re.IGNORECASE), "არ იქნა მიღებული არსებითად განსახილველად"),
    (re.compile(r'შეწყდეს?\s+საქმე', re.IGNORECASE), "საქმე შეწყდა"),
]

CC_RESOLUTION_MARKER = "სარეზოლუციო ნაწილი"
CC_TITLE_PATTERN = re.compile(
    r'([\u10A0-\u10FF][\u10A0-\u10FF\s\.,\-„"]+)\s+'
    r'საქართველოს\s+(?:პარლამენტის|მთავრობის|პრეზიდენტის)\s+წინააღმდეგ',
    re.IGNORECASE
)


def process_constitutional_court_html(manifest: list) -> list[dict]:
    """Process Constitutional Court HTML case files."""
    cc_dir = RAW_DIR / "constitutional_court"
    html_files = sorted(cc_dir.glob("case_*.html"))

    if not html_files:
        print("  ⚠️  No Constitutional Court HTML files found")
        return []

    print(f"\n📁 Processing Constitutional Court ({len(html_files)} cases)")

    all_cases = []
    out_dir = PROCESSED_DIR / "constitutional_court"
    out_dir.mkdir(parents=True, exist_ok=True)

    for html_path in html_files:
        print(f"  📄 {html_path.name}...", end=" ", flush=True)

        html_content = html_path.read_text(encoding="utf-8", errors="replace")
        clean_text = html_to_text(html_content)

        # Extract case number (Georgian format N2/3/1609)
        case_nums = CC_CASE_NUMBER.findall(html_content)
        case_number = case_nums[0] if case_nums else html_path.stem

        # Extract title (parties)
        title_match = CC_TITLE_PATTERN.search(clean_text)
        title = title_match.group(0).strip() if title_match else ""

        # Extract resolution/outcome
        outcome = "unknown"
        resolution_text = ""
        res_idx = clean_text.find(CC_RESOLUTION_MARKER)
        if res_idx > -1:
            resolution_text = clean_text[res_idx:res_idx + 2000]
            for pattern, label in CC_OUTCOME_PATTERNS:
                if pattern.search(resolution_text):
                    outcome = label
                    break

        # Extract referenced constitutional articles
        const_articles = re.findall(
            r'(?:მე-)?(\d+)[\-ე]*\s+მუხლ',
            clean_text
        )
        const_articles = sorted(set(const_articles))

        # Save processed text
        safe_num = re.sub(r'[/\s]', '_', case_number)
        filename = f"cc_{safe_num}.txt"
        out_path = out_dir / filename
        out_path.write_text(clean_text, encoding="utf-8")

        case_meta = {
            "case_number": case_number,
            "title": title[:200],
            "decision_type": "constitutional",
            "outcome": outcome,
            "resolution_text": resolution_text[:500],
            "articles_referenced": const_articles[:20],
            "text_length": len(clean_text),
            "source_file": html_path.name,
            "output_file": str(out_path.relative_to(BASE_DIR)),
            "category": "constitutional",
            "source": "constitutional_court",
        }
        manifest.append(case_meta)
        all_cases.append(case_meta)

        print(f"→ {case_number} | {outcome}")

    return all_cases


# ─────────────────────────────────────────────
# Verification
# ─────────────────────────────────────────────

def verify_processed_cases(manifest: list):
    """Run basic verification checks on processed cases."""
    print("\n" + "=" * 60)
    print("🔍 Verification Report")
    print("=" * 60)

    total = len(manifest)
    by_category = {}
    by_source = {}
    issues = []

    for case in manifest:
        cat = case.get("category", "unknown")
        src = case.get("source", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_source[src] = by_source.get(src, 0) + 1

        # Check output file exists and has content
        out_file = BASE_DIR / case.get("output_file", "")
        if not out_file.exists():
            issues.append(f"Missing output: {case['output_file']}")
        elif out_file.stat().st_size < 100:
            issues.append(f"Too small ({out_file.stat().st_size}b): {case['output_file']}")

        # Check case number is not 'unknown'
        if "unknown" in case.get("case_number", "unknown"):
            issues.append(f"No case number: {case.get('source_file', '?')}")

        # Check text length is reasonable
        text_len = case.get("text_length", 0)
        if text_len < 500:
            issues.append(f"Very short text ({text_len} chars): {case.get('case_number', '?')}")

    print(f"\n📊 Totals:")
    print(f"  Total cases extracted: {total}")
    for cat, count in sorted(by_category.items()):
        print(f"  {cat:20s}: {count}")

    print(f"\n📂 By source:")
    for src, count in sorted(by_source.items()):
        print(f"  {src:20s}: {count}")

    if issues:
        print(f"\n⚠️  Issues found ({len(issues)}):")
        for issue in issues[:20]:
            print(f"  - {issue}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")
    else:
        print(f"\n✅ No issues found!")

    # Show sample cases for each category
    print(f"\n📝 Sample cases (first 3 per category):")
    shown = {}
    for case in manifest:
        cat = case.get("category", "unknown")
        if shown.get(cat, 0) >= 3:
            continue
        shown[cat] = shown.get(cat, 0) + 1
        num = case.get("case_number", "?")
        date = case.get("date", "?")
        arts = case.get("articles_referenced", [])[:5]
        outcome = case.get("outcome", "")
        txt_len = case.get("text_length", 0)
        print(f"  [{cat:15s}] #{num:20s} | date={date} | {txt_len:,} chars | articles={arts}")
        if outcome:
            print(f"  {'':15s}  outcome: {outcome}")

    return len(issues)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process raw Georgian court case files")
    parser.add_argument("--only", choices=["criminal", "civil", "administrative", "constitutional"],
                        help="Process only a specific category")
    parser.add_argument("--verify-only", action="store_true",
                        help="Only verify existing processed files")
    parser.add_argument("--limit", type=int, help="Limit PDFs processed per category (for testing)")
    args = parser.parse_args()

    print("=" * 60)
    print("🏛️  Georgian Court Case Processor")
    print("=" * 60)
    print(f"Input:  {RAW_DIR}")
    print(f"Output: {PROCESSED_DIR}")
    print(f"Time:   {datetime.now().isoformat()}")

    # Check for existing manifest if verify-only
    manifest_path = BASE_DIR / "processing_manifest.json"
    if args.verify_only:
        if not manifest_path.exists():
            print("ERROR: No processing_manifest.json found. Run processing first.")
            sys.exit(1)
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        verify_processed_cases(data["cases"])
        return

    manifest = []

    # Process Supreme Court PDFs
    if not args.only or args.only in ("criminal", "civil", "administrative"):
        process_supreme_court_pdfs(manifest)

    # Process Constitutional Court HTML
    if not args.only or args.only == "constitutional":
        process_constitutional_court_html(manifest)

    # Save manifest
    manifest_data = {
        "processed_at": datetime.now().isoformat(),
        "total_cases": len(manifest),
        "by_category": {},
        "cases": manifest,
    }
    for case in manifest:
        cat = case.get("category", "unknown")
        manifest_data["by_category"][cat] = manifest_data["by_category"].get(cat, 0) + 1

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Manifest: {manifest_path}")

    # Verify
    issue_count = verify_processed_cases(manifest)

    # Final summary
    print("\n" + "=" * 60)
    print("✅ Processing Complete" if issue_count == 0 else f"⚠️  Processing Complete ({issue_count} issues)")
    print("=" * 60)
    print(f"  Total cases: {len(manifest)}")
    print(f"  Output dir:  {PROCESSED_DIR}")
    print(f"  Manifest:    {manifest_path}")
    print(f"\nNext step: python3 eval/test_cases/extract_metadata.py")


if __name__ == "__main__":
    main()
