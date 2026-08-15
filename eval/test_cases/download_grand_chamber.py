#!/usr/bin/env python3
"""
Download Grand Chamber PDFs + missing Supreme Court PDFs (2022, Civil 2023).

Grand Chamber sources (scraped from supremecourt.ge):
  - Criminal decisions (16 PDFs, 2001-2013)
  - Civil decisions (15 PDFs, 2001-2017)
  - Administrative decisions (17 PDFs, 2002-2009)
  - Norm interpretations (1 PDF — the binding legal dictionary)

Missing Supreme Court PDFs:
  - Criminal 2022 (4 quarterly PDFs from old.supremecourt.ge)
  - Civil 2022 (12 monthly PDFs from old.supremecourt.ge)
  - Civil 2023 (12 monthly PDFs from supremecourt.ge)
  - Admin 2022 (discover from supremecourt.ge page)

Output structure:
  raw/supreme_court/grand_chamber/
    ├── criminal/
    ├── civil/
    ├── administrative/
    └── norm_interpretations/
  raw/supreme_court/criminal/     (2022 additions)
  raw/supreme_court/civil/        (2022-2023 additions)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent / "raw"


# ─────────────────────────────────────────────
# Grand Chamber PDF URLs (scraped from live pages 2026-05-07)
# ─────────────────────────────────────────────

GRAND_CHAMBER_PDFS = {
    "criminal": {
        # 16 decisions (2001-2013)
        "gc-crim-227ap-13": "https://www.supremecourt.ge/files/upload-file/pdf/25tebervali-didi-palata.pdf",
        "gc-crim-236ap-12": "https://www.supremecourt.ge/files/upload-file/pdf/kalaze-robizon-ganacheni.pdf",
        "gc-crim-1024ap-07": "https://www.supremecourt.ge/files/upload-file/pdf/2007saqme-1042ap.pdf",
        "gc-crim-202kol-06": "https://www.supremecourt.ge/files/upload-file/pdf/2006-202kol.pdf",
        "gc-crim-30kol-05": "https://www.supremecourt.ge/files/upload-file/pdf/2005-30kol.pdf",
        "gc-crim-224ap-05": "https://www.supremecourt.ge/files/upload-file/pdf/2005-224-ap.pdf",
        "gc-crim-9ap-04": "https://www.supremecourt.ge/files/upload-file/pdf/2004-9-ap.pdf",
        "gc-crim-107kol-04": "https://www.supremecourt.ge/files/upload-file/pdf/2004-107-kol.pdf",
        "gc-crim-54kol-03": "https://www.supremecourt.ge/files/upload-file/pdf/2003-54-kol.pdf",
        "gc-crim-201ap-222saz-03": "https://www.supremecourt.ge/files/upload-file/pdf/2003-201-ap-222-saz.pdf",
        "gc-crim-168ap-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-168-ap.pdf",
        "gc-crim-40kol-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-40.pdf",
        "gc-crim-62kol-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-62.pdf",
        "gc-crim-86kol-01": "https://www.supremecourt.ge/files/upload-file/pdf/2001-86-kol.pdf",
        "gc-crim-71kol-01": "https://www.supremecourt.ge/files/upload-file/pdf/2001-71-kol.pdf",
        "gc-crim-66kol-01": "https://www.supremecourt.ge/files/upload-file/pdf/2001-66-kol.pdf",
    },
    "civil": {
        # 15 decisions (2001-2017)
        "gc-civil-664-635-2016": "https://www.supremecourt.ge/files/upload-file/pdf/didi-palata-02.03.2017.pdf",
        "gc-civil-121-117-2016": "https://www.supremecourt.ge/files/upload-file/pdf/didi-palata-17.03.16.pdf",
        "gc-civil-1161-1106-2014": "https://www.supremecourt.ge/files/upload-file/pdf/news-+-30.12.2014.pdf",
        "gc-civil-81-779-03a": "https://www.supremecourt.ge/files/upload-file/pdf/2004-81-779.pdf",
        "gc-civil-81-779-03b": "https://www.supremecourt.ge/files/upload-file/pdf/2004-81-779-1.pdf",
        "gc-civil-3k-1090-03": "https://www.supremecourt.ge/files/upload-file/pdf/2003-3k-1090-03.pdf",
        "gc-civil-3k-1049-02": "https://www.supremecourt.ge/files/upload-file/pdf/2003-3k-1049-02.pdf",
        "gc-civil-3k-115-03": "https://www.supremecourt.ge/files/upload-file/pdf/2003-3k-115-03.pdf",
        "gc-civil-3k-1325-02": "https://www.supremecourt.ge/files/upload-file/pdf/2003-3k-1325-02.pdf",
        "gc-civil-3k-932-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3k-932-02.pdf",
        "gc-civil-3k-624-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3k-624-02.pdf",
        "gc-civil-3k-678-01": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3k-678.pdf",
        "gc-civil-3k-441-04": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3k-441.pdf",
        "gc-civil-3k-35-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3k-35.pdf",
        "gc-civil-3k-458-01": "https://www.supremecourt.ge/files/upload-file/pdf/2001-3k-458-01.pdf",
    },
    "administrative": {
        # 17 decisions (2002-2009)
        "gc-admin-1537-1494-08": "https://www.supremecourt.ge/files/upload-file/pdf/28-07-2009.pdf",
        "gc-admin-132-123-07a": "https://www.supremecourt.ge/files/upload-file/pdf/gabunia-2007.pdf",
        "gc-admin-132-123-07b": "https://www.supremecourt.ge/files/upload-file/pdf/12-11-2007-ganmarteba.pdf",
        "gc-admin-335-317-07": "https://www.supremecourt.ge/files/upload-file/pdf/bs-335-317-k-07.pdf",
        "gc-admin-847-403-05a": "https://www.supremecourt.ge/files/upload-file/pdf/19-04-2006.pdf",
        "gc-admin-847-403-05b": "https://www.supremecourt.ge/files/upload-file/pdf/sagadasaxadodep-403.pdf",
        "gc-admin-1230-805-05a": "https://www.supremecourt.ge/files/upload-file/pdf/bs-1230-805k-05.pdf",
        "gc-admin-817-403-05": "https://www.supremecourt.ge/files/upload-file/pdf/bs-817-403k-ks-05.pdf",
        "gc-admin-1043-625-05": "https://www.supremecourt.ge/files/upload-file/pdf/bs-1043-625k-05.pdf",
        "gc-admin-1081-661-05": "https://www.supremecourt.ge/files/upload-file/pdf/bs-1081-661k-05.pdf",
        "gc-admin-1230-805-05b": "https://www.supremecourt.ge/files/upload-file/pdf/31-10-2005.pdf",
        "gc-admin-713-300-05": "https://www.supremecourt.ge/files/upload-file/pdf/7-10-2005.pdf",
        "gc-admin-106-144k-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3g-106-144.pdf",
        "gc-admin-23g-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3g-23-02.pdf",
        "gc-admin-203k-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3g-203-K-02.pdf",
        "gc-admin-193k-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3g-193-K-02.pdf",
        "gc-admin-204k-02": "https://www.supremecourt.ge/files/upload-file/pdf/2002-3g-204-k-02.pdf",
    },
    "norm_interpretations": {
        # The most valuable document — compiled binding interpretations
        "gc-norm-interpretations": "https://www.supremecourt.ge/files/upload-file/pdf/ganmarteba-d.pdf",
    },
}


# ─────────────────────────────────────────────
# Missing Supreme Court PDFs (2022 + Civil 2023)
# ─────────────────────────────────────────────

MISSING_SC_PDFS = {
    "criminal": {
        # Criminal 2022 — quarterly from old.supremecourt.ge
        "sisxli-01-03-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-1-3.pdf",
        "sisxli-04-06-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-4-6.pdf",
        "sisxli-07-09-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-7-9.pdf",
        "sisxli-10-12-2022": "http://old.supremecourt.ge/files/upload-file/pdf/2022w-sisxli-krebuli-10-12.pdf",
    },
    "civil_2022": {
        # Civil 2022 — monthly from old.supremecourt.ge
        **{
            f"samoqalaqo-{n:02d}-2022": f"http://old.supremecourt.ge/files/upload-file/pdf/2022w-samoqalaqo-krebuli{n}.pdf"
            for n in range(1, 13)
        },
    },
    "civil_2023": {
        # Civil 2023 — monthly from supremecourt.ge
        **{
            f"samoq-{n:02d}-2023": f"https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/samoq-{n:02d}-2023.pdf"
            for n in range(1, 13)
        },
    },
}


# ─────────────────────────────────────────────
# Download helper (reuses pattern from download_cases.py)
# ─────────────────────────────────────────────

def download_file(url: str, dest: Path, retries: int = 3) -> dict:
    """Download a file with retries. Returns status dict."""
    result = {
        "url": url,
        "dest": str(dest),
        "status": "unknown",
        "size_bytes": 0,
        "error": None,
    }

    if dest.exists() and dest.stat().st_size > 0:
        result["status"] = "skipped_exists"
        result["size_bytes"] = dest.stat().st_size
        print(f"  ⏭️  Already exists: {dest.name} ({dest.stat().st_size:,} bytes)")
        return result

    dest.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) FuzzzyLaw-Eval/1.0",
                "Accept": "*/*",
            })
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                dest.write_bytes(data)
                result["status"] = "downloaded"
                result["size_bytes"] = len(data)
                print(f"  ✅ Downloaded: {dest.name} ({len(data):,} bytes)")
                return result
        except urllib.error.HTTPError as e:
            result["error"] = f"HTTP {e.code}: {e.reason}"
            if e.code == 404:
                result["status"] = "not_found"
                print(f"  ❌ 404 Not Found: {dest.name}")
                return result
            if e.code == 403:
                result["status"] = "forbidden"
                print(f"  🔒 403 Forbidden: {dest.name}")
                return result
            print(f"  ⚠️  HTTP {e.code} on attempt {attempt+1}/{retries}: {dest.name}")
        except Exception as e:
            result["error"] = str(e)
            print(f"  ⚠️  Error on attempt {attempt+1}/{retries}: {e}")

        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))

    result["status"] = "failed"
    print(f"  ❌ Failed after {retries} attempts: {dest.name}")
    return result


# ─────────────────────────────────────────────
# Download functions
# ─────────────────────────────────────────────

def download_grand_chamber(manifest: list, only_category: str = None):
    """Download Grand Chamber PDFs."""
    categories = GRAND_CHAMBER_PDFS
    if only_category:
        categories = {only_category: GRAND_CHAMBER_PDFS[only_category]}

    for category, pdfs in categories.items():
        print(f"\n📁 Grand Chamber — {category.upper()} ({len(pdfs)} PDFs)")
        cat_dir = BASE_DIR / "supreme_court" / "grand_chamber" / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        for name, url in pdfs.items():
            dest = cat_dir / f"{name}.pdf"
            result = download_file(url, dest)
            result["source"] = "grand_chamber"
            result["category"] = category
            result["name"] = name
            manifest.append(result)
            time.sleep(0.5)


def download_missing_sc(manifest: list):
    """Download missing Supreme Court PDFs (2022 criminal/civil, 2023 civil)."""
    for category_key, pdfs in MISSING_SC_PDFS.items():
        # Map category key to output directory
        if category_key == "criminal":
            out_dir = BASE_DIR / "supreme_court" / "criminal"
            display = "Criminal 2022"
        elif category_key == "civil_2022":
            out_dir = BASE_DIR / "supreme_court" / "civil"
            display = "Civil 2022"
        elif category_key == "civil_2023":
            out_dir = BASE_DIR / "supreme_court" / "civil"
            display = "Civil 2023"
        else:
            out_dir = BASE_DIR / "supreme_court" / category_key
            display = category_key

        print(f"\n📁 Supreme Court — {display} ({len(pdfs)} PDFs)")
        out_dir.mkdir(parents=True, exist_ok=True)

        for name, url in pdfs.items():
            dest = out_dir / f"{name}.pdf"
            result = download_file(url, dest)
            result["source"] = "supreme_court"
            result["category"] = category_key
            result["name"] = name
            manifest.append(result)
            time.sleep(0.5)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Download Grand Chamber + missing Supreme Court PDFs"
    )
    parser.add_argument(
        "--only", choices=["grand-chamber", "missing-sc", "all"],
        default="all",
        help="What to download (default: all)"
    )
    parser.add_argument(
        "--gc-category",
        choices=["criminal", "civil", "administrative", "norm_interpretations"],
        help="Download only a specific Grand Chamber category"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would be downloaded")
    args = parser.parse_args()

    print("=" * 60)
    print("🏛️  Grand Chamber & Missing SC PDF Downloader")
    print("=" * 60)
    print(f"Output: {BASE_DIR}")
    print(f"Time: {datetime.now().isoformat()}")

    if args.dry_run:
        print("\n🔍 DRY RUN — listing files to download:\n")
        total = 0
        if args.only in ("grand-chamber", "all"):
            for category, pdfs in GRAND_CHAMBER_PDFS.items():
                if args.gc_category and category != args.gc_category:
                    continue
                for name in pdfs:
                    print(f"  [gc/{category:20s}] {name}.pdf")
                    total += 1
        if args.only in ("missing-sc", "all"):
            for category, pdfs in MISSING_SC_PDFS.items():
                for name in pdfs:
                    print(f"  [sc/{category:20s}] {name}.pdf")
                    total += 1
        print(f"\nTotal: {total} files to download")
        return

    manifest = []

    if args.only in ("grand-chamber", "all"):
        download_grand_chamber(manifest, only_category=args.gc_category)

    if args.only in ("missing-sc", "all"):
        download_missing_sc(manifest)

    # Save manifest
    manifest_path = BASE_DIR / "grand_chamber_download_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "downloaded_at": datetime.now().isoformat(),
            "total_files": len(manifest),
            "downloaded": sum(1 for m in manifest if m["status"] == "downloaded"),
            "skipped": sum(1 for m in manifest if m["status"] == "skipped_exists"),
            "failed": sum(1 for m in manifest if m["status"] in ("failed", "not_found", "forbidden")),
            "total_bytes": sum(m["size_bytes"] for m in manifest),
            "files": manifest,
        }, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Download Summary")
    print("=" * 60)
    downloaded = sum(1 for m in manifest if m["status"] == "downloaded")
    skipped = sum(1 for m in manifest if m["status"] == "skipped_exists")
    failed = sum(1 for m in manifest if m["status"] in ("failed", "not_found", "forbidden"))
    total_bytes = sum(m["size_bytes"] for m in manifest)
    print(f"  ✅ Downloaded: {downloaded}")
    print(f"  ⏭️  Skipped (exists): {skipped}")
    print(f"  ❌ Failed/404/403: {failed}")
    print(f"  📦 Total size: {total_bytes / 1024 / 1024:.1f} MB")
    print(f"  📄 Manifest: {manifest_path}")

    if failed > 0:
        print(f"\n⚠️  Failed downloads:")
        for m in manifest:
            if m["status"] in ("failed", "not_found", "forbidden"):
                print(f"    {m['name']}: {m.get('error', m['status'])}")


if __name__ == "__main__":
    main()
