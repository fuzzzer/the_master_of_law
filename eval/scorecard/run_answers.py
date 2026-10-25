"""Collect answers for the scorecard items from one target.

Usage (key set inline by the caller, never printed):
  FL_KEY=... python -I -B run_answers.py --target local --worktree <path> --set tuning|heldback|all \
      --out <results dir> [--ids a,b] [--limit N] [--gap 45] [--cap N] [--worker name] [--rerun-degraded]
  FL_KEY=... python -I -B run_answers.py --target live [--base-url URL] ...

Answers go to <out>/answers/<id>.json (tuning) and <out>/heldback/<id>.json (held-back). Items already
answered with status 200 are skipped, so an interrupted run resumes. Every consultation is one line in the
ledger (FL_LEDGER, default the overnight task ledger).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pricing import TOTAL_CAP_USD, ledger_usd, usd  # noqa: E402
DEFAULT_LEDGER = "/Volumes/Fuzzzity 2/fuzzzy_company/work/fuzzzy-law-overnight-20261025/consultations_ledger.jsonl"


def load_items(which: str) -> list[dict]:
    tuning = json.loads((HERE / "items" / "tuning.json").read_text(encoding="utf-8"))
    for i in tuning:
        i["_set"] = "tuning"
    if which == "tuning":
        return tuning
    held = json.loads((HERE / "items" / "heldback" / "HELDBACK_ITEMS.json").read_text(encoding="utf-8"))["items"]
    for i in held:
        i["_set"] = "heldback"
    if which in ("lean", "lean-tuning"):
        lean = json.loads((HERE / "items" / "lean_set.json").read_text(encoding="utf-8"))
        if which == "lean-tuning":
            return [i for i in tuning if i["id"] in set(lean["tuning"])]
        keep = set(lean["tuning"]) | set(lean["heldback"])
        return [i for i in tuning + held if i["id"] in keep]
    return held if which == "heldback" else tuning + held


def ledger_count(ledger: Path, worker: str) -> int:
    if not ledger.exists():
        return 0
    n = 0
    for line in ledger.read_text().splitlines():
        try:
            if json.loads(line).get("worker") == worker:
                n += 1
        except json.JSONDecodeError:
            pass
    return n


def make_target(args, key: str):
    if args.target == "local":
        from targets.local_pipeline import LocalPipelineTarget
        return LocalPipelineTarget(args.worktree, key, args.corpus)
    if args.target == "live":
        from targets.live_http import LiveHttpTarget
        return LiveHttpTarget(key, args.base_url)
    from targets.external_connector import ExternalConnectorTarget
    t = ExternalConnectorTarget(args.assistant, key or None, connector=not args.no_connector)
    if not t.available:
        print(f"SKIP external target ({args.assistant}): key absent or not wired yet", flush=True)
        sys.exit(0)
    return t


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["local", "live", "external"], default="local")
    ap.add_argument("--worktree", default=str(HERE.parents[1]))
    ap.add_argument("--corpus")
    ap.add_argument("--base-url", default="https://law-api.fuzzzycore.com")
    ap.add_argument("--assistant", default="claude")
    ap.add_argument("--no-connector", action="store_true")
    ap.add_argument("--set", default="tuning", choices=["tuning", "heldback", "all", "lean", "lean-tuning"])
    ap.add_argument("--ids")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--gap", type=float, default=45)
    ap.add_argument("--cap", type=int, default=10_000, help="max ledger lines for this worker, all runs together")
    ap.add_argument("--usd-cap", type=float, default=TOTAL_CAP_USD,
                    help="max recorded USD for workers named like --worker, all runs together")
    ap.add_argument("--worker", default="scorecard")
    ap.add_argument("--purpose", default="scorecard answer")
    ap.add_argument("--rerun-degraded", action="store_true")
    ap.add_argument("--item-timeout", type=float, default=900)
    args = ap.parse_args()

    key = os.environ.get("FL_KEY", "")
    if not key and args.target != "external":
        print("SKIP: no key in FL_KEY", flush=True)
        sys.exit(2)
    ledger = Path(os.environ.get("FL_LEDGER", DEFAULT_LEDGER))
    out = Path(args.out)
    (out / "answers").mkdir(parents=True, exist_ok=True)
    (out / "heldback").mkdir(parents=True, exist_ok=True)
    items = load_items(args.set)
    if args.ids:
        wanted = set(args.ids.split(","))
        items = [i for i in items if i["id"] in wanted]
    target = make_target(args, key)
    meta_path = out / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {"runs": []}
    meta["runs"].append({"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "target_info": target.info, "set": args.set,
                         "gap_s": args.gap, "n_items": len(items)})
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1))

    done = fails = 0
    for it in items:
        if args.limit is not None and done >= args.limit:
            break
        p = out / ("heldback" if it["_set"] == "heldback" else "answers") / f"{it['id']}.json"
        if p.exists():
            prev = json.loads(p.read_text())
            if prev.get("status") == 200 and not (args.rerun_degraded and prev.get("degraded")):
                continue
        if ledger_count(ledger, args.worker) >= args.cap:
            print("consultation cap reached; stopping", flush=True)
            break
        total, mine = ledger_usd(ledger), ledger_usd(ledger, args.worker)
        if total >= TOTAL_CAP_USD or mine >= args.usd_cap:
            print(f"spending cap reached (all workers {total:.2f} USD, this worker {mine:.2f} USD); stopping", flush=True)
            break
        try:
            rec = await asyncio.wait_for(target.answer(it), timeout=args.item_timeout)
        except asyncio.TimeoutError:
            rec = {"id": it["id"], "message": it["message"], "status": 504, "error": f"harness timeout {args.item_timeout} s",
                   "latency_s": args.item_timeout, "degraded": True, "degraded_events": ["harness timeout"]}
        rec["kind"], rec["set"], rec["target_info"] = it["kind"], it["_set"], target.info
        u = rec.get("usage") or {}
        model = (u.get("models") or ["gemini-3.7-flash"])[0]
        cost = usd(model, u.get("in_tokens", 0), u.get("out_tokens", 0)) if u else None
        rec["usd"] = cost
        with ledger.open("a") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "worker": args.worker,
                                "item": it["id"] if it["_set"] == "tuning" else "heldback-item",
                                "purpose": f"{args.purpose} ({args.target})", "model": model,
                                "in_tokens": u.get("in_tokens"), "out_tokens": u.get("out_tokens"), "usd": cost,
                                "model_calls": u.get("model_calls")}) + "\n")
        if p.exists():
            (p.parent / "attempts").mkdir(exist_ok=True)
            (p.parent / "attempts" / f"{it['id']}.{int(time.time())}.json").write_text(p.read_text(), encoding="utf-8")
        p.write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        b = rec.get("body") or {}
        shown = it["id"] if it["_set"] == "tuning" else "heldback-item"
        print(f"{shown}: status={rec.get('status')} lat={rec.get('latency_s')} len={len(b.get('response', '') or '')} "
              f"usd={cost} degraded={rec.get('degraded')} err={(rec.get('error') or '')[:160]}", flush=True)
        done += 1
        fails = fails + 1 if rec.get("status") != 200 else 0
        if fails >= 3:
            print("three failures in a row; stopping", flush=True)
            break
        await asyncio.sleep(args.gap * (3 if rec.get("degraded") else 1))
    print(f"run finished: {done} consultations this run", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
