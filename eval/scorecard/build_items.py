"""Build the scorecard item set and its fixed tuning / held-back split.

Sources (all in this folder unless named):
  expected/scenario_messages.json   the 29 everyday questions (2026-10-24 set)
  expected/scenarios_expected.json  their written expected answers
  expected/targeted_items.json      targeted items for each known failure pattern
  expected/court_messages.json      citizen retellings of the stored court cases (2026-10-24)
  expected/court_expected.json      real outcomes and the six verdict corrections
  expected/court_cases_extra.json   extra public Supreme Court rulings (optional) with their retellings
Writes:
  items/tuning.json                 items fix workers may read in full
  items/heldback/HELDBACK_ITEMS.json  held-back items: scored only, never opened by fix workers
  items/split.json                  seed, method and the id lists of both sets

The split is stratified by group, about 70/30, and fixed: ids already in split.json keep their set; only new
ids are assigned (by a hash of seed + id within their group).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE / "expected"
ITEMS = HERE / "items"
SEED = "20261025"
HELDBACK_SHARE = 0.30


def load(name: str):
    return json.loads((EXP / name).read_text(encoding="utf-8"))


def scenario_items() -> list[dict]:
    msgs = load("scenario_messages.json")
    exp = load("scenarios_expected.json")["items"]
    out = []
    for m in msgs:
        group = "scenario-edge" if m.get("edge") else "scenario-everyday"
        out.append({"id": m["id"], "kind": "scenario", "group": group, "topic": m["topic"], "message": m["message"],
                    "expected": exp[m["id"]], "author_hint": m.get("expect")})
    return out


def targeted_items() -> list[dict]:
    out = []
    for t in load("targeted_items.json")["items"]:
        expected = {k: v for k, v in t.items() if k not in ("id", "kind", "topic", "pattern", "message")}
        out.append({"id": t["id"], "kind": "scenario", "group": "targeted", "topic": t["topic"], "pattern": t["pattern"],
                    "message": t["message"], "expected": expected})
    return out


def court_items() -> list[dict]:
    msgs = {m["id"]: m for m in load("court_messages.json")}
    exp = load("court_expected.json")
    out = []
    for cid, e in exp["cases"].items():
        m = msgs[cid]
        corr = exp["corrections"].get(cid)
        out.append({"id": cid, "kind": "court", "group": f"court-{m['category']}", "topic": m["category"],
                    "message": m["message"], "pattern": "prosecutor appeal" if "prosecutor" in e["appellant"] else None,
                    "expected": {"expected_user_win": e["expected_user_win"], "appellant": e["appellant"],
                                 "actual_outcome_en": e["actual_outcome_en"],
                                 "verdict": corr["verdict_corrected"] if corr else None,
                                 "verdict_corrected": bool(corr),
                                 "truth_source": "eval/test_cases/cases.json"}})
    extra = EXP / "court_cases_extra.json"
    if extra.exists():
        for c in json.loads(extra.read_text(encoding="utf-8"))["cases"]:
            out.append({"id": c["case_id"], "kind": "court", "group": f"court-{c['category']}", "topic": c["category"],
                        "message": c["message"], "pattern": "prosecutor appeal" if "prosecutor" in c["appellant"].lower() else None,
                        "expected": {"expected_user_win": c["expected_user_win"], "appellant": c["appellant"],
                                     "actual_outcome_en": c["verdict_en"], "verdict": c["verdict"],
                                     "verdict_corrected": False,
                                     "truth_source": "eval/scorecard/expected/court_cases_extra.json"}})
    return out


def check_articles(items: list[dict], store: Path | None) -> list[str]:
    """Every required article must exist in the article store (or be a declared corpus gap)."""
    if not store or not store.exists():
        return ["article store not found; required articles not validated"]
    conn = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
    problems = []
    for it in items:
        for group in it["expected"].get("required_articles", []):
            for ref in group:
                code, art = ref.split(":")
                if not conn.execute("SELECT 1 FROM articles WHERE document_id=? AND article_norm=?", (code, art)).fetchone():
                    problems.append(f"{it['id']}: {ref} not in article store")
    conn.close()
    return problems


def bucket(item_id: str) -> str:
    return hashlib.sha256(f"{SEED}:{item_id}".encode()).hexdigest()


def split(items: list[dict]) -> dict:
    path = ITEMS / "split.json"
    prev = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"tuning": [], "heldback": []}
    known = {i: "tuning" for i in prev["tuning"]} | {i: "heldback" for i in prev["heldback"]}
    groups: dict[str, list[dict]] = {}
    for it in items:
        groups.setdefault(it["group"], []).append(it)
    assign = {}
    for g, members in sorted(groups.items()):
        have_h = sum(1 for m in members if known.get(m["id"]) == "heldback")
        target_h = round(HELDBACK_SHARE * len(members))
        for m in sorted((m for m in members if m["id"] not in known), key=lambda m: bucket(m["id"])):
            if have_h < target_h:
                assign[m["id"]] = "heldback"
                have_h += 1
            else:
                assign[m["id"]] = "tuning"
        for m in members:
            if m["id"] in known:
                assign[m["id"]] = known[m["id"]]
    return assign


def main():
    store = Path(sys.argv[sys.argv.index("--store") + 1]) if "--store" in sys.argv else None
    items = scenario_items() + targeted_items() + court_items()
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "duplicate ids"
    for p in check_articles(items, store):
        print("WARN", p)
    assign = split(items)
    tuning = [i for i in items if assign[i["id"]] == "tuning"]
    held = [i for i in items if assign[i["id"]] == "heldback"]
    (ITEMS / "heldback").mkdir(parents=True, exist_ok=True)
    (ITEMS / "tuning.json").write_text(json.dumps(tuning, ensure_ascii=False, indent=1), encoding="utf-8")
    (ITEMS / "heldback" / "HELDBACK_ITEMS.json").write_text(json.dumps(
        {"warning": "HELD-BACK SET. Scored only. Fix workers must not open this file or tune on these items.",
         "items": held}, ensure_ascii=False, indent=1), encoding="utf-8")
    by_group = {}
    for i in items:
        by_group.setdefault(i["group"], {"tuning": 0, "heldback": 0})[assign[i["id"]]] += 1
    (ITEMS / "split.json").write_text(json.dumps({
        "seed": SEED, "heldback_share": HELDBACK_SHARE,
        "method": "stratified by group; within a group, new ids sorted by sha256(seed:id); ids keep their set once assigned",
        "counts": {"tuning": len(tuning), "heldback": len(held), "total": len(items)}, "by_group": by_group,
        "tuning": sorted(i["id"] for i in tuning), "heldback": sorted(i["id"] for i in held)},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"tuning": len(tuning), "heldback": len(held), "by_group": by_group}, ensure_ascii=False))


if __name__ == "__main__":
    main()
