#!/usr/bin/env python3
"""
Download raw Georgian court decision PDFs and pages.

Sources:
  1. Supreme Court quarterly PDF collections (criminal, administrative)
     and monthly PDF collections (civil)
  2. Constitutional Court judicial acts (individual HTML pages)

All URLs scraped from live supremecourt.ge and constcourt.ge pages.

Output structure:
  raw/
  ├── supreme_court/
  │   ├── criminal/    ← quarterly PDFs (sisxli)
  │   ├── civil/       ← monthly PDFs (samoqalaqo/samoq)
  │   └── administrative/ ← quarterly PDFs (administraciuli)
  ├── constitutional_court/
  │   ├── case_XXXX.md ← individual case text
  │   └── listing_page_XX.html
  └── download_manifest.json
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
# Supreme Court PDF URLs (verified from live pages)
# ─────────────────────────────────────────────

SUPREME_COURT_PDFS = {
    "criminal": {
        # 2025 — quarterly
        "sisxli-01-03-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-01-03-2025.pdf",
        "sisxli-04-06-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-04-06-2025.pdf",
        "sisxli-07-09-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-07-09-2025.pdf",
        "sisxli-10-12-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-10-12-2025.pdf",
        # 2024 — quarterly
        "sisxli-01-03-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-01-03-2024.pdf",
        "sisxli-04-06-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-04-06-2024.pdf",
        "sisxli-07-09-2024": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/sisxli-7-9-2024.pdf",
        "sisxli-10-12-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/sisxli/sisxli-10-12-24.pdf",
        # 2023 — quarterly
        "sisxli-01-03-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/sisxli-1-3_2023.pdf",
        "sisxli-04-06-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/sisxli-4-6-2023.pdf",
        "sisxli-07-09-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/sisxli-7-9-2023.pdf",
        "sisxli-10-12-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/sisxli-10-12-2023.pdf",
    },
    "civil": {
        # 2026 — monthly
        "samoq-01-2026": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-01-2026.pdf",
        "samoq-02-2026": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-02-2026.pdf",
        "samoq-03-2026": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-03-2026.pdf",
        # 2025 — monthly (all 12)
        "samoq-01-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-1-2025.pdf",
        "samoq-02-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-02-2025.pdf",
        "samoq-03-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-03-2025.pdf",
        "samoq-04-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-04-2025.pdf",
        "samoq-05-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-05-2025.pdf",
        "samoq-06-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-06-2025.pdf",
        "samoq-07-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-07-2025.pdf",
        "samoq-08-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-08-2025.pdf",
        "samoq-09-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-09-2025.pdf",
        "samoq-10-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-10-2025.pdf",
        "samoq-11-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-11-2025.pdf",
        "samoq-12-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-12-2025.pdf",
        # 2024 — monthly (all 12)
        "samoq-01-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-01-2024.pdf",
        "samoq-02-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-02-2024.pdf",
        "samoq-03-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-03-2024.pdf",
        "samoq-04-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-04-2024.pdf",
        "samoq-05-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-05-2024.pdf",
        "samoq-06-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-06-2024.pdf",
        "samoq-07-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-07-2024.pdf",
        "samoq-08-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-08-2024.pdf",
        "samoq-09-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-09-2024.pdf",
        "samoq-10-2024": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/samoq-10-2024.pdf",
        "samoq-11-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-11-2024.pdf",
        "samoq-12-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/samoq/samoq-12-2024.pdf",
    },
    "administrative": {
        # Verified from live page: supremecourt.ge/decisions/administratsiuli-samartlis-saqmeebze
        # Admin uses MONTHLY PDFs at .../admin/admin-{MM}-{YYYY}.pdf
        # Some URLs have quirky formatting (spaces, typos) — preserved exactly as on page.
        # 2026 — monthly
        "admin-01-2026": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-01-2026.pdf",
        "admin-02-2026": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-02-2026.pdf",
        "admin-03-2026": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-03-2026.pdf",
        "admin-04-2026": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-04-2026.pdf",
        # 2025 — monthly (all 12)
        "admin-01-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-01-2025.pdf",
        "admin-02-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-02-2025.pdf",
        "admin-03-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-03-2025.pdf",
        "admin-04-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-04-2025.pdf",
        "admin-05-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-05-2025.pdf",
        "admin-06-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-06-2025.pdf",
        "admin-07-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-07-2025.pdf",
        "admin-08-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-08-2025.pdf",
        "admin-09-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-091-2025.pdf",
        "admin-10-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-10-%202025.pdf",
        "admin-11-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin%2011-2025.pdf",
        "admin-12-2025": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-12-2025.pdf",
        # 2024 — monthly (all 12)
        "admin-01-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-01-2024.pdf",
        "admin-02-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-02-2024.pdf",
        "admin-03-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-03-2024.pdf",
        "admin-04-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-04-2024.pdf",
        "admin-05-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-05-2024.pdf",
        "admin-06-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-06-2024.pdf",
        "admin-07-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-07-2024.pdf",
        "admin-08-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-08-2024.pdf",
        "admin-09-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-09-2024.pdf",
        "admin-10-2024": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-10-2024.pdf",
        "admin-11-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-11-2024.pdf",
        "admin-12-2024": "https://www.supremecourt.ge/uploads/files/1/gamomtsemloba/collection/admin/admin-12-2024.pdf",
        # 2023 — monthly (all 12, different base path)
        "admin-01-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-01-2023.pdf",
        "admin-02-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-02-2023.pdf",
        "admin-03-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-03-2023.pdf",
        "admin-04-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-04-2023.pdf",
        "admin-05-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-05-2023.pdf",
        "admin-06-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-06-2023.pdf",
        "admin-07-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-07-2023.pdf",
        "admin-08-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-08-2023.pdf",
        "admin-09-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-09-2023.pdf",
        "admin-10-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-10-2023.pdf",
        "admin-11-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-11-2023.pdf",
        "admin-12-2023": "https://www.supremecourt.ge/uploads/files/1/gamotsemebi_des/admin-12-2023.pdf",
    },
}

# Constitutional Court cases to download individually
# These are IDs from constcourt.ge/ka/judicial-acts?legal=XXXX
CONSTCOURT_CASE_IDS = [
    # 2026 decisions (verified from listing page)
    19616,  # ბუდუ შეყილაძე vs. პარლამენტი (pension age equality) — №2/3/1609
    19615,  # ვიტალი შურაგინი vs. პარლამენტი — №1/2/1934
    19614,  # Political parties ban case — №1/10/1912
    19617,  # სახალხო დამცველი vs. პარლამენტი — №1/9/1897
    19618,  # სახალხო დამცველი vs. პარლამენტი — №1/7/1485
    19613,  # ომეგა მოტორ ჯგუფი vs. პარლამენტი — №1/8/1733
    19845,  # თემურ აბაშიძე vs. პარლამენტი — N1961
    19847,  # ქართველიშვილი vs. პარლამენტი — N1962
    19823,  # ილიას უნივერსიტეტი vs. პარლამენტი — N1960
]

CONSTCOURT_LISTING_PAGES = 5  # first 5 pages for discovery


# ─────────────────────────────────────────────
# Download helpers
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
# Main download logic
# ─────────────────────────────────────────────

def download_supreme_court_pdfs(manifest: list, only_category=None, only_year=None):
    """Download Supreme Court PDF collections."""
    categories = SUPREME_COURT_PDFS
    if only_category:
        categories = {only_category: SUPREME_COURT_PDFS[only_category]}

    for category, pdfs in categories.items():
        print(f"\n📁 Supreme Court — {category.upper()}")
        cat_dir = BASE_DIR / "supreme_court" / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        for name, url in pdfs.items():
            if only_year and str(only_year) not in name:
                continue
            dest = cat_dir / f"{name}.pdf"
            result = download_file(url, dest)
            result["source"] = "supreme_court"
            result["category"] = category
            result["name"] = name
            manifest.append(result)
            time.sleep(0.5)


def download_constitutional_court_cases(manifest: list):
    """Download individual Constitutional Court case pages."""
    print(f"\n📁 Constitutional Court — individual cases ({len(CONSTCOURT_CASE_IDS)} cases)")
    cc_dir = BASE_DIR / "constitutional_court"
    cc_dir.mkdir(parents=True, exist_ok=True)

    for case_id in CONSTCOURT_CASE_IDS:
        url = f"https://constcourt.ge/ka/judicial-acts?legal={case_id}"
        dest = cc_dir / f"case_{case_id}.html"
        result = download_file(url, dest)
        result["source"] = "constitutional_court"
        result["category"] = "constitutional"
        result["name"] = f"case_{case_id}"
        manifest.append(result)
        time.sleep(1)


def download_constitutional_court_listings(manifest: list):
    """Download Constitutional Court listing pages for case discovery."""
    print(f"\n📁 Constitutional Court — listing pages (1-{CONSTCOURT_LISTING_PAGES})")
    cc_dir = BASE_DIR / "constitutional_court" / "listings"
    cc_dir.mkdir(parents=True, exist_ok=True)

    for page in range(1, CONSTCOURT_LISTING_PAGES + 1):
        url = f"https://constcourt.ge/ka/judicial-acts?page={page}"
        dest = cc_dir / f"listing_page_{page:02d}.html"
        result = download_file(url, dest)
        result["source"] = "constitutional_court"
        result["category"] = "constitutional_listing"
        result["name"] = f"listing_page_{page:02d}"
        manifest.append(result)
        time.sleep(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download Georgian court case data")
    parser.add_argument("--only", choices=["criminal", "civil", "administrative", "constitutional"],
                        help="Download only a specific category")
    parser.add_argument("--year", type=int, help="Download only a specific year (for Supreme Court)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be downloaded")
    parser.add_argument("--no-listings", action="store_true", help="Skip CC listing pages")
    args = parser.parse_args()

    print("=" * 60)
    print("🏛️  Georgian Court Case Downloader")
    print("=" * 60)
    print(f"Output: {BASE_DIR}")
    print(f"Time: {datetime.now().isoformat()}")

    if args.dry_run:
        print("\n🔍 DRY RUN — listing files to download:\n")
        total = 0
        for category, pdfs in SUPREME_COURT_PDFS.items():
            if args.only and args.only not in (category, "constitutional"):
                continue
            if args.only == "constitutional":
                continue
            for name, url in pdfs.items():
                if args.year and str(args.year) not in name:
                    continue
                print(f"  [{category:15s}] {name}.pdf")
                total += 1
        if not args.only or args.only == "constitutional":
            for cid in CONSTCOURT_CASE_IDS:
                print(f"  [constitutional  ] case_{cid}")
                total += 1
            if not args.no_listings:
                for p in range(1, CONSTCOURT_LISTING_PAGES + 1):
                    print(f"  [const_listing   ] listing_page_{p:02d}")
                    total += 1
        print(f"\nTotal: {total} files to download")
        return

    manifest = []

    # Supreme Court PDFs
    if not args.only or args.only in ("criminal", "civil", "administrative"):
        download_supreme_court_pdfs(manifest, only_category=args.only, only_year=args.year)

    # Constitutional Court individual cases
    if not args.only or args.only == "constitutional":
        download_constitutional_court_cases(manifest)

    # Constitutional Court listing pages
    if (not args.only or args.only == "constitutional") and not args.no_listings:
        download_constitutional_court_listings(manifest)

    # Save manifest
    manifest_path = BASE_DIR / "download_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
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
