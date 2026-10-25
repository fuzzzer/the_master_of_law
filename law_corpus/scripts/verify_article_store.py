#!/usr/bin/env python3
"""
Verify an article store (SQLite + FTS5) against the matsne pages it was built from.

Checks, per code:
  - provenance: version date, publication number, versioned URL, retrieval time
  - counts: articles in the store vs article headings found on the matsne page
    (counted independently of the parser, from the page text)
  - integrity: one row in force per article number, no empty live article,
    superscript numbers kept apart (126¹ ≠ 1261), FTS index complete
  - faithfulness: every stored line appears word for word in the page text
  - spot checks: the articles the 2026-10-24 compliance run found broken

Exit code 0 when everything passes, 1 otherwise. Writes a JSON report with
``--json``. Needs only the standard library plus beautifulsoup4/lxml (for
``--raw-dir``).

Usage:
    python scripts/verify_article_store.py --store data/georgian_laws/article_store.db \\
        --raw-dir data/georgian_laws/raw/html [--json report.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

_SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"

# Articles the compliance run found broken, with words matsne prints in them.
SPOT_CHECKS: list[dict[str, str]] = [
    {"code": "civil_procedure_code", "article": "369", "contains": "სააპელაციო საჩივრის შეტანის ვადაა 14 დღე",
     "why": "appeal deadline (part 1) was missing"},
    {"code": "admin_offences_code", "article": "272", "contains": "ზემდგომ ორგანოში (ზემდგომ თანამდებობის პირთან)",
     "why": "was cut short and filed under the wrong chapter"},
    {"code": "criminal_code", "article": "381", "contains": "სისხლის სამართლის საერთაშორისო სასამართლოს",
     "why": "was cut short (note missing)"},
    {"code": "criminal_code", "article": "126-1", "contains": "ოჯახის ერთი წევრის მიერ ოჯახის სხვა წევრის მიმართ ძალადობა",
     "why": "superscript article 126¹ was stored as 1261"},
    {"code": "civil_code", "article": "49-1", "contains": "ერთობლივი საინვესტიციო ფონდის",
     "why": "49¹ was stored as 491 and shadowed the real article 491"},
    {"code": "civil_code", "article": "491", "contains": "მყიდველს შეუძლია ნივთის ნაკლის გამო",
     "why": "real article 491 was hidden behind 49¹"},
    {"code": "labour_code", "article": "48", "contains": "30 კალენდარული დღის",
     "why": "dismissal reasons deadline (regression guard)"},
]

_HEADING_RE = re.compile(r"^(\[?)\s*მ\s*უხლის?\s*(\d+)\s*([" + _SUP + r"]*)\s*(?:[.\-–—]|\()")


def _page_text_lines(html_path: Path) -> list[str]:
    """Page text in reading order, one line per block, as the parser normalises it."""
    from bs4 import BeautifulSoup

    from pipeline.parser.html_parser import element_text

    soup = BeautifulSoup(html_path.read_text("utf-8", errors="replace"), "lxml")
    root = soup.find(id="maindoc") or soup
    blocks = root.find_all(["p", "table"]) if root.find("p") else [root]
    lines: list[str] = []
    for block in blocks:
        if block.name == "table" and block.find("p"):
            continue  # its paragraphs are visited on their own
        text = element_text(block)
        if text:
            lines.append(text)
    return lines


def _headings_on_page(lines: list[str]) -> tuple[set[str], set[str]]:
    """Article numbers (lookup form) of current and future (bracketed) headings."""
    current: set[str] = set()
    future: set[str] = set()
    sup_digits = str.maketrans(_SUP, "0123456789")
    for line in lines:
        m = _HEADING_RE.match(line)
        if not m or len(line) > 600:
            continue
        number = m.group(2) + (f"-{m.group(3).translate(sup_digits)}" if m.group(3) else "")
        (future if m.group(1) else current).add(number)
    return current, future


def verify(store: Path, raw_dir: Path | None) -> dict:
    conn = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    failures: list[str] = []
    report: dict = {"store": str(store), "codes": {}, "spot_checks": [], "failures": failures}

    report["schema_version"] = conn.execute("PRAGMA user_version").fetchone()[0]
    columns = {r[1] for r in conn.execute("PRAGMA table_info(articles)")}
    for col in ("official_url", "version_date", "in_force", "matsne_anchor"):
        if col not in columns:
            failures.append(f"articles table lacks column {col}")

    fts = conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    report["articles_total"] = total
    if fts != total:
        failures.append(f"FTS index has {fts} rows for {total} articles")

    for code in conn.execute("SELECT * FROM codes ORDER BY document_id"):
        doc = code["document_id"]
        rows = conn.execute("SELECT * FROM articles WHERE document_id = ?", (doc,)).fetchall()
        live = [r for r in rows if r["in_force"]]
        info = {
            "code_name": code["code_name"],
            "source_url": code["source_url"],
            "version_date": code["version_date"],
            "publication_id": code["publication_id"],
            "version_url": code["version_url"],
            "retrieved_at": code["retrieved_at"],
            "articles": len(rows),
            "in_force_rows": len(live),
            "future_wordings": len(rows) - len(live),
            "repealed_placeholders": sum(1 for r in rows if r["is_repealed"]),
        }
        for field in ("version_date", "publication_id", "version_url", "retrieved_at"):
            if not code[field]:
                failures.append(f"{doc}: no {field}")

        norms = [r["article_norm"] for r in live]
        duplicates = sorted({n for n in norms if norms.count(n) > 1})
        empty = [r["article_number"] for r in live if not r["content_ka"].strip() and not r["is_repealed"]]
        flattened = [r["article_number"] for r in rows
                     if any(c in r["article_number"] for c in _SUP) and "-" not in r["article_norm"]]
        no_link = [r["article_number"] for r in rows if not r["official_url"]]
        info.update({"duplicate_numbers": duplicates, "empty_articles": empty,
                     "flattened_superscripts": flattened, "without_official_link": len(no_link)})
        for label, bad in (("duplicate article numbers in force", duplicates),
                           ("empty articles", empty), ("flattened superscript numbers", flattened)):
            if bad:
                failures.append(f"{doc}: {label}: {bad[:10]}")

        html = raw_dir / f"{doc}.html" if raw_dir else None
        if html and html.exists():
            lines = _page_text_lines(html)
            page_text = "\n".join(lines)
            current, future = _headings_on_page(lines)
            stored_current = {r["article_norm"] for r in live}
            stored_future = {r["article_norm"] for r in rows if not r["in_force"]}
            info["headings_on_matsne"] = len(current)
            info["future_headings_on_matsne"] = len(future)
            info["missing_from_store"] = sorted(current - stored_current)
            info["not_on_matsne"] = sorted(stored_current - current)
            info["future_missing_from_store"] = sorted(future - stored_future - stored_current)
            if info["missing_from_store"]:
                failures.append(f"{doc}: {len(info['missing_from_store'])} matsne articles missing: "
                                f"{info['missing_from_store'][:10]}")
            if info["not_on_matsne"]:
                failures.append(f"{doc}: stored articles with no matsne heading: {info['not_on_matsne'][:10]}")
            unmatched = [(r["article_number"], line[:80]) for r in rows
                         for line in r["content_ka"].split("\n") if line and line not in page_text]
            info["lines_not_word_for_word"] = len(unmatched)
            info["lines_not_word_for_word_examples"] = unmatched[:5]
            if unmatched:
                failures.append(f"{doc}: {len(unmatched)} stored lines differ from the matsne text")
        report["codes"][doc] = info

    for check in SPOT_CHECKS:
        row = conn.execute(
            "SELECT * FROM articles WHERE document_id = ? AND article_norm = ? "
            "ORDER BY in_force DESC LIMIT 1",
            (check["code"], check["article"]),
        ).fetchone()
        ok = row is not None and check["contains"] in row["content_ka"]
        report["spot_checks"].append({
            **check,
            "ok": ok,
            "article_number": row["article_number"] if row else None,
            "official_url": row["official_url"] if row else None,
            "version_date": row["version_date"] if row else None,
            "text": row["content_ka"] if row else None,
        })
        if not ok:
            failures.append(f"spot check {check['code']} {check['article']}: {check['why']}")

    conn.close()
    report["passed"] = not failures
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, help="matsne HTML pages the store was built from")
    ap.add_argument("--json", type=Path, help="write the full report here")
    args = ap.parse_args()

    report = verify(args.store, args.raw_dir)
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Store {args.store} (schema version {report['schema_version']}), {report['articles_total']} articles")
    for doc, info in report["codes"].items():
        on_page = info.get("headings_on_matsne", "?")
        print(f"  {doc:26} {info['in_force_rows']:5} in force (matsne headings: {on_page}), "
              f"{info['future_wordings']} future, version {info['version_date']}")
    for check in report["spot_checks"]:
        print(f"  {'OK  ' if check['ok'] else 'FAIL'} {check['code']} {check['article']}: {check['why']}")
    if report["failures"]:
        print(f"FAILED ({len(report['failures'])}):")
        for failure in report["failures"]:
            print(f"  - {failure}")
        sys.exit(1)
    print("PASSED")


if __name__ == "__main__":
    main()
