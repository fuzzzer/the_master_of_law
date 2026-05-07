#!/usr/bin/env python3
"""
Convert AkadTrans (Latin-transliterated Georgian) to proper Mkhedruli Unicode.

The Supreme Court PDFs use the standard Georgian academic transliteration
where Georgian letters are encoded as Latin characters. This script converts
them back to proper Georgian Unicode (ქართული).

Transliteration table (AkadTrans → Mkhedruli):
  a→ა b→ბ g→გ d→დ e→ე v→ვ z→ზ T→თ i→ი k→კ l→ლ m→მ
  n→ნ o→ო p→პ J→ჟ r→რ s→ს t→ტ u→უ f→ფ q→ქ R→ღ y→ყ
  S→შ C→ჩ c→ც Z→ძ w→წ W→ჭ x→ხ j→ჯ h→ჰ

Usage:
  # Convert a single file
  python3 convert_to_georgian.py eval/test_cases/processed/supreme_court/criminal/7ap-25.txt

  # Convert all processed files in-place
  python3 convert_to_georgian.py --all

  # Preview conversion (don't write)
  python3 convert_to_georgian.py --preview eval/test_cases/processed/supreme_court/criminal/7ap-25.txt

  # Convert to separate output directory
  python3 convert_to_georgian.py --all --output-dir eval/test_cases/georgian/
"""

import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─────────────────────────────────────────────
# AkadTrans → Mkhedruli mapping
# ─────────────────────────────────────────────
# Case-sensitive: uppercase Latin letters map to specific Georgian letters
# that don't have a lowercase Latin equivalent.

TRANS_TABLE = {
    # Lowercase Latin → Georgian
    'a': 'ა', 'b': 'ბ', 'g': 'გ', 'd': 'დ', 'e': 'ე',
    'v': 'ვ', 'z': 'ზ', 'i': 'ი', 'k': 'კ', 'l': 'ლ',
    'm': 'მ', 'n': 'ნ', 'o': 'ო', 'p': 'პ', 'r': 'რ',
    's': 'ს', 't': 'ტ', 'u': 'უ', 'f': 'ფ', 'q': 'ქ',
    'x': 'ხ', 'j': 'ჯ', 'h': 'ჰ', 'w': 'წ', 'y': 'ყ',
    'c': 'ც',
    # Uppercase Latin → Georgian (these represent different Georgian letters)
    'T': 'თ', 'J': 'ჟ', 'R': 'ღ', 'S': 'შ', 'C': 'ჩ',
    'Z': 'ძ', 'W': 'ჭ',
}

# Characters that should NOT be converted (numbers, punctuation, etc.)
PRESERVE_CHARS = set('0123456789.,;:!?-–—()[]{}"\'/\\@#$%^&*+=<>|~`_ \t\n\r')

# Patterns that should be preserved as-is (URLs, emails, page markers)
PRESERVE_PATTERNS = [
    re.compile(r'\[PAGE_\d+\]'),               # Page markers
    re.compile(r'https?://\S+'),                # URLs
    re.compile(r'\S+@\S+\.\S+'),               # Emails
    re.compile(r'#[\w\-]+'),                    # Case numbers like #943ap-24
    re.compile(r'N?№\d+/\d+/\d+'),             # Constitutional case numbers
    re.compile(r'\b\d{4}\s*w\.'),               # Year markers "2025 w."
    re.compile(r'`[^`]+`'),                     # Backtick-quoted terms
    re.compile(r'ACL|GPS|DNA|SMS|SIM|ATM|TV'),  # Common abbreviations
]


def convert_text(text: str) -> str:
    """
    Convert AkadTrans Latin text to Georgian Mkhedruli Unicode.

    Strategy:
    1. Find and protect regions that shouldn't be converted (URLs, numbers, markers)
    2. Convert each Latin character using the transliteration table
    3. Leave already-Georgian text, numbers, and punctuation untouched
    """
    # First, find all regions to preserve
    protected = []
    for pattern in PRESERVE_PATTERNS:
        for match in pattern.finditer(text):
            protected.append((match.start(), match.end()))

    # Sort and merge overlapping regions
    protected.sort()
    merged = []
    for start, end in protected:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Build result character by character
    result = []
    i = 0
    while i < len(text):
        # Check if we're in a protected region
        in_protected = False
        for pstart, pend in merged:
            if pstart <= i < pend:
                result.append(text[i])
                i += 1
                in_protected = True
                break
        if in_protected:
            continue

        ch = text[i]

        # Already Georgian Unicode? Keep as-is
        if '\u10A0' <= ch <= '\u10FF' or '\u2D00' <= ch <= '\u2D2F':
            result.append(ch)
        # In our transliteration table? Convert
        elif ch in TRANS_TABLE:
            result.append(TRANS_TABLE[ch])
        # Everything else (numbers, punct, etc.) stays
        else:
            result.append(ch)

        i += 1

    return ''.join(result)


def convert_file(filepath: Path, output_path: Path = None, preview: bool = False) -> dict:
    """Convert a single file. Returns stats dict."""
    text = filepath.read_text(encoding='utf-8', errors='replace')
    converted = convert_text(text)

    # Count conversions
    latin_count = sum(1 for c in text if c in TRANS_TABLE)
    geo_count = sum(1 for c in converted if '\u10A0' <= c <= '\u10FF')

    stats = {
        "file": str(filepath),
        "original_size": len(text),
        "converted_size": len(converted),
        "latin_chars_converted": latin_count,
        "georgian_chars_in_output": geo_count,
    }

    if preview:
        print(f"\n{'='*60}")
        print(f"📄 {filepath.name}")
        print(f"{'='*60}")
        print(f"Original (first 500 chars):")
        print(text[:500])
        print(f"\n{'─'*60}")
        print(f"Converted (first 500 chars):")
        print(converted[:500])
        print(f"\nStats: {latin_count} Latin chars → Georgian")
    else:
        dest = output_path or filepath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(converted, encoding='utf-8')

    return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert AkadTrans to Georgian Unicode")
    parser.add_argument("files", nargs="*", help="Specific files to convert")
    parser.add_argument("--all", action="store_true", help="Convert all processed files")
    parser.add_argument("--preview", action="store_true", help="Preview without writing")
    parser.add_argument("--output-dir", type=str, help="Write to separate output directory")
    args = parser.parse_args()

    if not args.all and not args.files:
        parser.print_help()
        sys.exit(1)

    files_to_convert = []

    if args.all:
        processed_dir = BASE_DIR / "processed"
        files_to_convert = sorted(processed_dir.rglob("*.txt"))
        print(f"Found {len(files_to_convert)} files to convert")
    else:
        files_to_convert = [Path(f) for f in args.files]

    total_converted = 0
    for filepath in files_to_convert:
        if not filepath.exists():
            print(f"  ⚠️  Not found: {filepath}")
            continue

        output_path = None
        if args.output_dir:
            rel = filepath.relative_to(BASE_DIR / "processed")
            output_path = Path(args.output_dir) / rel

        stats = convert_file(filepath, output_path=output_path, preview=args.preview)
        total_converted += stats["latin_chars_converted"]

        if not args.preview:
            print(f"  ✅ {filepath.name}: {stats['latin_chars_converted']:,} chars converted")

    if not args.preview:
        print(f"\n📊 Total: {len(files_to_convert)} files, {total_converted:,} Latin chars → Georgian")


if __name__ == "__main__":
    main()
