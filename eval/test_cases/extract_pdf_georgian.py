#!/usr/bin/env python3
"""
Font-aware Georgian PDF extractor.

The Supreme Court PDFs use HKolkhety fonts that map Georgian glyphs
to Latin character codes (AkadTrans encoding). This extractor detects
the font per text span and applies conversion ONLY to HKolkhety spans,
leaving Times New Roman (English) and Baltica (Russian) text untouched.

Font mapping discovered from the PDFs:
  HKolkhety / HKolkhetyMtav → Georgian text in AkadTrans encoding → CONVERT
  Times New Roman            → Real English text → KEEP AS-IS
  Baltica TD                 → Russian text → KEEP AS-IS

Usage:
  # Extract a single PDF
  python3 extract_pdf_georgian.py path/to/file.pdf

  # Extract all PDFs in raw/ directory
  python3 extract_pdf_georgian.py --all

  # Preview without writing
  python3 extract_pdf_georgian.py --preview path/to/file.pdf

  # Output to specific directory
  python3 extract_pdf_georgian.py --all --output-dir eval/test_cases/georgian/
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF required. Install with: pip install PyMuPDF")
    sys.exit(1)

BASE_DIR = Path(__file__).parent

# ─────────────────────────────────────────────
# AkadTrans → Mkhedruli mapping
# ─────────────────────────────────────────────
AKADTRANS_TO_GEORGIAN = {
    'a': 'ა', 'b': 'ბ', 'g': 'გ', 'd': 'დ', 'e': 'ე',
    'v': 'ვ', 'z': 'ზ', 'i': 'ი', 'k': 'კ', 'l': 'ლ',
    'm': 'მ', 'n': 'ნ', 'o': 'ო', 'p': 'პ', 'r': 'რ',
    's': 'ს', 't': 'ტ', 'u': 'უ', 'f': 'ფ', 'q': 'ქ',
    'x': 'ხ', 'j': 'ჯ', 'h': 'ჰ', 'w': 'წ', 'y': 'ყ',
    'c': 'ც',
    # Uppercase Latin → specific Georgian letters
    'T': 'თ', 'J': 'ჟ', 'R': 'ღ', 'S': 'შ', 'C': 'ჩ',
    'Z': 'ძ', 'W': 'ჭ',
    # M is used in HKolkhety but not as a Georgian letter —
    # it appears in contexts like page numbers. Keep as-is unless
    # we find a clear mapping.
}

# Font name patterns for Georgian AkadTrans fonts
GEORGIAN_FONT_PATTERNS = [
    'HKolkhety',
    'HKolkhetyMtav',
    'Kolkhety',
    'AcadNusx',
    'Acadnusx',
    'LitNusx',
    'Sylfaen',  # Sometimes used with AkadTrans encoding
]

# Font name patterns for real Latin/English fonts — never convert
LATIN_FONT_PATTERNS = [
    'Times',
    'Arial',
    'Helvetica',
    'Courier',
    'Calibri',
    'Cambria',
]

# Font name patterns for Russian fonts — keep as-is
RUSSIAN_FONT_PATTERNS = [
    'Baltica',
]


def is_georgian_font(font_name: str) -> bool:
    """Check if a font name indicates a Georgian AkadTrans font."""
    for pattern in GEORGIAN_FONT_PATTERNS:
        if pattern.lower() in font_name.lower():
            return True
    # CIDFont+F names: check if NOT a known Latin/Russian font
    # This is a fallback — we prefer explicit matching
    return False


def is_known_latin_font(font_name: str) -> bool:
    """Check if a font is a known Latin/English font."""
    for pattern in LATIN_FONT_PATTERNS:
        if pattern.lower() in font_name.lower():
            return True
    return False


def is_known_russian_font(font_name: str) -> bool:
    """Check if a font is a known Russian font."""
    for pattern in RUSSIAN_FONT_PATTERNS:
        if pattern.lower() in font_name.lower():
            return True
    return False


def convert_akadtrans(text: str) -> str:
    """Convert AkadTrans Latin text to Georgian Mkhedruli Unicode."""
    result = []
    for ch in text:
        if ch in AKADTRANS_TO_GEORGIAN:
            result.append(AKADTRANS_TO_GEORGIAN[ch])
        else:
            result.append(ch)
    return ''.join(result)


def build_font_map(doc) -> dict:
    """
    Build a mapping of CIDFont names → real font names by scanning all pages.
    Returns dict like {'CIDFont+F1': 'HKolkhety', 'CIDFont+F2': 'Times New Roman'}
    """
    from fontTools.ttLib import TTFont
    import io

    font_map = {}  # cid_name → real_name

    seen_xrefs = set()
    for page_num in range(len(doc)):
        for font_info in doc[page_num].get_fonts(full=True):
            xref = font_info[0]
            cid_name = font_info[3]

            if xref in seen_xrefs or cid_name in font_map:
                continue
            seen_xrefs.add(xref)

            try:
                font_data = doc.extract_font(xref)
                ttf_bytes = font_data[3]
                if not ttf_bytes:
                    continue

                font = TTFont(io.BytesIO(ttf_bytes))
                real_name = ''
                for record in font['name'].names:
                    if record.nameID == 4:  # Full font name
                        real_name = record.toStr()
                        break
                font.close()

                if real_name:
                    font_map[cid_name] = real_name

            except Exception:
                pass

    return font_map


def extract_page_text(page, font_map: dict) -> str:
    """
    Extract text from a single page, converting AkadTrans spans
    to Georgian based on font detection.
    """
    blocks = page.get_text('dict')['blocks']
    page_lines = []

    for block in blocks:
        if 'lines' not in block:
            continue

        for line in block['lines']:
            line_text = []
            for span in line['spans']:
                cid_font = span['font']
                text = span['text']

                # Look up real font name
                real_font = font_map.get(cid_font, cid_font)

                if is_georgian_font(real_font):
                    # This is AkadTrans Georgian — convert it
                    converted = convert_akadtrans(text)
                    line_text.append(converted)
                elif is_known_latin_font(real_font):
                    # Real English text — keep as-is
                    line_text.append(text)
                elif is_known_russian_font(real_font):
                    # Russian text — keep as-is (or skip)
                    line_text.append(text)
                else:
                    # Unknown font — try to detect by content
                    # If it contains Georgian Unicode already, keep it
                    has_georgian = any('\u10A0' <= c <= '\u10FF' for c in text)
                    if has_georgian:
                        line_text.append(text)
                    else:
                        # Default: try AkadTrans conversion for unknown fonts
                        # (most CIDFont+ names in these PDFs are Georgian)
                        converted = convert_akadtrans(text)
                        line_text.append(converted)

            combined = ''.join(line_text).rstrip()
            if combined:
                page_lines.append(combined)

    return '\n'.join(page_lines)


def extract_pdf(pdf_path: Path, font_map: dict = None) -> str:
    """Extract entire PDF with font-aware Georgian conversion."""
    doc = fitz.open(str(pdf_path))

    # Build font map if not provided
    if font_map is None:
        try:
            font_map = build_font_map(doc)
        except ImportError:
            print("  ⚠️  fontTools not available, falling back to CIDFont names")
            font_map = {}

    all_pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = extract_page_text(page, font_map)
        if text.strip():
            all_pages.append(text)
            all_pages.append(f'\n[PAGE_{page_num + 1}]\n')

    doc.close()
    return '\n'.join(all_pages)


def split_cases_from_text(text: str, source_pdf: str) -> list:
    """
    Split a multi-case PDF bulletin into individual case texts.
    Cases typically start with 'განაჩენი' or 'განჩინება' followed by
    'საქართველოს სახელით'.
    """
    # Pattern for case start: "განაჩენი" or "განჩინება" at line start
    case_start = re.compile(
        r'^(განაჩენი|განჩინება)\s*$',
        re.MULTILINE
    )

    matches = list(case_start.finditer(text))
    if not matches:
        return [{'text': text, 'case_id': None, 'source': source_pdf}]

    cases = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        case_text = text[start:end].strip()

        # Try to extract case number
        case_num_match = re.search(r'#([\w\-]+)', case_text[:300])
        case_id = case_num_match.group(1) if case_num_match else f'case_{i+1}'

        cases.append({
            'text': case_text,
            'case_id': case_id,
            'source': source_pdf,
        })

    return cases


def process_pdf(pdf_path: Path, output_dir: Path, preview: bool = False) -> dict:
    """Process a single PDF file."""
    font_map = None
    doc = fitz.open(str(pdf_path))
    try:
        font_map = build_font_map(doc)
    except ImportError:
        font_map = {}
    doc.close()

    text = extract_pdf(pdf_path, font_map)

    # Count quality metrics
    geo_chars = sum(1 for c in text if '\u10A0' <= c <= '\u10FF')
    lat_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total_chars = len(text)

    stats = {
        'file': pdf_path.name,
        'total_chars': total_chars,
        'georgian_chars': geo_chars,
        'latin_chars': lat_chars,
        'geo_ratio': geo_chars / max(1, geo_chars + lat_chars),
        'fonts': font_map,
    }

    if preview:
        print(f"\n{'='*60}")
        print(f"📄 {pdf_path.name}")
        print(f"{'='*60}")
        print(f"Fonts: {font_map}")
        print(f"Georgian: {geo_chars:,} | Latin: {lat_chars:,} | Ratio: {stats['geo_ratio']:.1%}")
        print(f"\nFirst 800 chars:")
        print(text[:800])
        return stats

    # Split into individual cases
    cases = split_cases_from_text(text, pdf_path.name)

    for case in cases:
        case_id = case['case_id']
        if case_id:
            output_file = output_dir / f"{case_id}.txt"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(case['text'], encoding='utf-8')

    stats['cases_extracted'] = len(cases)
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Font-aware Georgian PDF extractor for Supreme Court bulletins"
    )
    parser.add_argument("files", nargs="*", help="PDF files to extract")
    parser.add_argument("--all", action="store_true", help="Extract all PDFs in raw/")
    parser.add_argument("--preview", action="store_true", help="Preview without writing")
    parser.add_argument(
        "--output-dir", type=str,
        default=str(BASE_DIR / "processed_v2"),
        help="Output directory (default: processed_v2/)"
    )
    args = parser.parse_args()

    if not args.all and not args.files:
        parser.print_help()
        sys.exit(1)

    pdf_files = []
    if args.all:
        raw_dir = BASE_DIR / "raw"
        pdf_files = sorted(raw_dir.rglob("*.pdf"))
        print(f"Found {len(pdf_files)} PDFs")
    else:
        pdf_files = [Path(f) for f in args.files]

    total_stats = {'geo': 0, 'lat': 0, 'cases': 0, 'files': 0}

    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"  ⚠️  Not found: {pdf_path}")
            continue

        # Determine output subdirectory based on input path
        # raw/supreme_court/criminal/file.pdf → processed_v2/supreme_court/criminal/
        try:
            rel = pdf_path.relative_to(BASE_DIR / "raw")
            out_dir = Path(args.output_dir) / rel.parent
        except ValueError:
            out_dir = Path(args.output_dir)

        try:
            stats = process_pdf(pdf_path, out_dir, preview=args.preview)
            total_stats['geo'] += stats['georgian_chars']
            total_stats['lat'] += stats['latin_chars']
            total_stats['cases'] += stats.get('cases_extracted', 0)
            total_stats['files'] += 1

            ratio = stats['geo_ratio']
            indicator = '🟢' if ratio > 0.9 else '🟡' if ratio > 0.7 else '🔴'
            if not args.preview:
                print(
                    f"  {indicator} {pdf_path.name}: "
                    f"{stats['georgian_chars']:,} geo / {stats['latin_chars']:,} lat "
                    f"({ratio:.0%}) → {stats.get('cases_extracted', '?')} cases"
                )
        except Exception as e:
            print(f"  ❌ {pdf_path.name}: {e}")

    if not args.preview:
        total_ratio = total_stats['geo'] / max(1, total_stats['geo'] + total_stats['lat'])
        print(f"\n{'='*60}")
        print(f"📊 Total: {total_stats['files']} PDFs → {total_stats['cases']} cases")
        print(f"   Georgian: {total_stats['geo']:,} | Latin: {total_stats['lat']:,} | Ratio: {total_ratio:.1%}")


if __name__ == "__main__":
    main()
