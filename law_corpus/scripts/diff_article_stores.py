#!/usr/bin/env python3
"""
Compare two article stores: what a rebuild adds, fixes, removes and renumbers.

Articles are matched by (document_id, article number). Older stores flattened
superscript numbers ("126¹" stored as "1261"); a pair whose old key equals the
new key without its dash and whose title matches is reported as renumbered,
not as one removal plus one addition.

Usage:
    python scripts/diff_article_stores.py OLD.db NEW.db [--json diff.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

# Chunk footer that older stores (rebuilt from vector chunks) carry in their text.
DISCLAIMER = "ეს მასალა მხოლოდ საინფორმაციო მიზნებისთვისაა. ოფიციალური ტექსტისთვის იხილეთ matsne.gov.ge"
_FLATTEN = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def _comparable(text: str) -> str:
    """Text without the chunk footer and without overlap fragments.

    Stores rebuilt by joining overlapping vector chunks repeat the tail of one
    chunk at the start of the next; such a line is contained in another line
    and is dropped so it is not counted as a wording difference.
    """
    lines = [line.strip() for line in text.replace(DISCLAIMER, "").split("\n") if line.strip()]
    kept = [line for i, line in enumerate(lines)
            if not any(i != j and line in other and len(other) > len(line) for j, other in enumerate(lines))]
    return re.sub(r"\s+", " ", " ".join(kept)).strip()


def _load(path: Path) -> dict[tuple[str, str], dict]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    columns = {r[1] for r in conn.execute("PRAGMA table_info(articles)")}
    where = "WHERE in_force = 1" if "in_force" in columns else ""
    rows: dict[tuple[str, str], dict] = {}
    for r in conn.execute(f"SELECT * FROM articles {where} ORDER BY LENGTH(article_id)"):
        rows.setdefault((r["document_id"], r["article_norm"]), dict(r))
    conn.close()
    return rows


def _same_title(a: dict, b: dict) -> bool:
    return (a.get("article_title") or "").strip() == (b.get("article_title") or "").strip()


def _kind_of_fix(before: str, after: str) -> str:
    """Rough class of a text change, for the summary."""
    squeeze = lambda t: re.sub(r"\s+", "", t.translate(_FLATTEN))  # noqa: E731
    if not before:
        return "was empty"
    if re.sub(r"\s+", "", before) == re.sub(r"\s+", "", after):
        return "spacing only (words were glued together)"
    if squeeze(before) == squeeze(after):
        return "superscript numbers (and spacing)"
    if squeeze(before) in squeeze(after):
        return "text added (old text was cut short)"
    if squeeze(after) in squeeze(before):
        return "text removed (old text carried extra lines)"
    return "wording differs"


def diff(old_path: Path, new_path: Path) -> dict:
    old, new = _load(old_path), _load(new_path)
    renumbered = []
    claimed_old: set[tuple[str, str]] = set()
    claimed_new: set[tuple[str, str]] = set()
    for key, art in new.items():
        doc, norm = key
        flat = (doc, norm.replace("-", ""))
        if "-" in norm and flat in old and _same_title(old[flat], art):
            renumbered.append({"code": doc, "old": flat[1], "new": norm, "number": art["article_number"],
                               "title": art["article_title"],
                               "text_changed": _comparable(old[flat]["content_ka"]) != _comparable(art["content_ka"])})
            claimed_old.add(flat)
            claimed_new.add(key)

    added, removed, fixed, unchanged = [], [], [], 0
    for key, art in new.items():
        if key in claimed_new:
            continue
        if key not in old or key in claimed_old:
            added.append({"code": key[0], "number": art["article_number"], "title": art["article_title"]})
            continue
        before, after = _comparable(old[key]["content_ka"]), _comparable(art["content_ka"])
        if before == after and _same_title(old[key], art):
            unchanged += 1
        else:
            fixed.append({"code": key[0], "number": art["article_number"], "title": art["article_title"],
                          "kind": _kind_of_fix(before, after),
                          "old_chars": len(before), "new_chars": len(after),
                          "old_paragraphs": len(json.loads(old[key]["paragraphs_json"] or "[]")),
                          "new_paragraphs": len(json.loads(art["paragraphs_json"] or "[]"))})
    for key, art in old.items():
        if key not in new and key not in claimed_old:
            removed.append({"code": key[0], "number": art["article_number"], "title": art["article_title"]})

    per_code: dict[str, dict[str, int]] = {}
    for label, items in (("added", added), ("fixed", fixed), ("removed", removed), ("renumbered", renumbered)):
        for item in items:
            per_code.setdefault(item["code"], {"added": 0, "fixed": 0, "removed": 0, "renumbered": 0})[label] += 1
    for (doc, _), _art in old.items():
        per_code.setdefault(doc, {"added": 0, "fixed": 0, "removed": 0, "renumbered": 0})
    counts_old: dict[str, int] = {}
    counts_new: dict[str, int] = {}
    for doc, _ in old:
        counts_old[doc] = counts_old.get(doc, 0) + 1
    for doc, _ in new:
        counts_new[doc] = counts_new.get(doc, 0) + 1
    for doc, row in per_code.items():
        row["old_articles"] = counts_old.get(doc, 0)
        row["new_articles"] = counts_new.get(doc, 0)

    kinds: dict[str, int] = {}
    for item in fixed:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1

    return {
        "old": str(old_path), "new": str(new_path), "fixed_by_kind": kinds,
        "old_articles": len(old), "new_articles": len(new), "unchanged": unchanged,
        "per_code": per_code, "added": added, "fixed": fixed, "removed": removed, "renumbered": renumbered,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    result = diff(args.old, args.new)
    if args.json:
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"old {result['old_articles']} articles → new {result['new_articles']} "
          f"(unchanged {result['unchanged']}, fixed {len(result['fixed'])}, added {len(result['added'])}, "
          f"removed {len(result['removed'])}, renumbered {len(result['renumbered'])})")
    for kind, count in sorted(result["fixed_by_kind"].items(), key=lambda kv: -kv[1]):
        print(f"  fixed: {count:5}  {kind}")
    print(f"{'code':26} {'old':>5} {'new':>5} {'fixed':>6} {'added':>6} {'removed':>8} {'renumbered':>11}")
    for doc, row in sorted(result["per_code"].items()):
        print(f"{doc:26} {row['old_articles']:5} {row['new_articles']:5} {row['fixed']:6} {row['added']:6} "
              f"{row['removed']:8} {row['renumbered']:11}")


if __name__ == "__main__":
    main()
