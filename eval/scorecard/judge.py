"""AI judge for the scorecard (rubric: rubric/JUDGE_RUBRIC.md, version scorecard-judge-v1).

Usage (key inline, never printed):
  FL_JUDGE_KEY=... python -I judge.py --results <dir> --store <article_store.db> [--judge gemini|claude] [--model M]
      [--gap 8] [--worker scorecard-judge] [--ids a,b]
  python -I judge.py --results <dir> --store <db> --judge packets   # write packets only, for an agent judge

Judges every answer in <dir>/answers and <dir>/heldback that has status 200; results go to <dir>/judge/<id>.json,
keyed by a hash of answer + rubric version, so unchanged answers are not judged twice.
  gemini: Gemini over Vertex AI express (Google Cloud key) or AI Studio ("AIza" key). Default model gemini-3.7-flash.
  claude: Claude through the anthropic SDK (key service fuzzzy_law_anthropic). Skipped when absent.
Each judge call is one ledger line with purpose "judge" (it is not an app consultation).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from checks import run_checks  # noqa: E402
from pricing import TOTAL_CAP_USD, ledger_usd, usd  # noqa: E402

RUBRIC_VERSION = "scorecard-judge-v1"
RUBRIC = (HERE / "rubric" / "JUDGE_RUBRIC.md").read_text(encoding="utf-8")
REPO = HERE.parents[1]
DEFAULT_LEDGER = "/Volumes/Fuzzzity 2/fuzzzy_company/work/fuzzzy-law-overnight-20261025/consultations_ledger.jsonl"


def all_items() -> dict:
    t = json.loads((HERE / "items" / "tuning.json").read_text(encoding="utf-8"))
    h = json.loads((HERE / "items" / "heldback" / "HELDBACK_ITEMS.json").read_text(encoding="utf-8"))["items"]
    return {i["id"]: i for i in t + h}


def court_truth(item: dict) -> dict:
    exp = item["expected"]
    if exp["truth_source"].endswith("court_cases_extra.json"):
        cases = json.loads((HERE / "expected" / "court_cases_extra.json").read_text(encoding="utf-8"))["cases"]
    else:
        cases = json.loads((REPO / "eval" / "test_cases" / "cases.json").read_text(encoding="utf-8"))["cases"]
    c = next(c for c in cases if c["case_id"] == item["id"])
    resolution = "" if exp.get("verdict_corrected") else c.get("court_resolution", "")[:3000]
    return {"actual_outcome_en": exp["actual_outcome_en"], "verdict": exp.get("verdict") or c.get("verdict"),
            "expected_user_win": exp["expected_user_win"], "appellant": exp["appellant"],
            "court_reasoning_excerpt": c.get("court_reasoning", "")[:10000], "court_resolution_excerpt": resolution}


def packet(item: dict, rec: dict, store: str) -> dict:
    chk = run_checks(rec, item["expected"], store)
    cites = [{k: c.get(k) for k in ("code", "article", "paragraph", "status", "context")} |
             {"article_text": (c.get("article_text") or "")[:1500]} for c in chk["citations"]]
    p = {"id": item["id"], "kind": item["kind"], "question": item["message"],
         "answer": ((rec.get("body") or {}).get("response") or "")[:14000], "citations": cites,
         "expected": {k: v for k, v in item["expected"].items() if k not in ("truth_source",)}}
    if item["kind"] == "court":
        p["truth"] = court_truth(item)
    return p


def answer_hash(rec: dict) -> str:
    text = ((rec.get("body") or {}).get("response") or "") + RUBRIC_VERSION
    return hashlib.sha256(text.encode()).hexdigest()[:16]


LAST_USAGE: dict = {}

PROMPT = """{rubric}

Judge this packet. Reply with exactly one JSON object, no other text.

PACKET:
{packet}"""


def call_gemini(key: str, model: str, prompt: str) -> str:
    if key.startswith("AIza"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    else:
        url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent"
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.0, "maxOutputTokens": 16384,
                                            "responseMimeType": "application/json"}}).encode()
    for attempt in range(4):
        req = urllib.request.Request(url, data=body, headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.loads(r.read())
            um = d.get("usageMetadata") or {}
            LAST_USAGE.update(in_tokens=um.get("promptTokenCount", 0),
                              out_tokens=um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0))
            parts = d["candidates"][0]["content"].get("parts", [])
            return "".join(x.get("text", "") for x in parts if not x.get("thought"))
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:200].replace(key, "[R]")
            print(f"  judge http {e.code} {msg}", flush=True)
            time.sleep(60 * (attempt + 1) if e.code == 429 else 15)
        except Exception as e:
            print(f"  judge error {type(e).__name__}", flush=True)
            time.sleep(15)
    raise RuntimeError("judge call failed")


def call_claude(key: str, model: str, prompt: str) -> str:
    import anthropic  # installed only where the Claude judge is used
    client = anthropic.Anthropic(api_key=key)
    resp = client.beta.messages.create(
        model=model, max_tokens=16000, output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        messages=[{"role": "user", "content": prompt}])
    if resp.stop_reason == "refusal":
        raise RuntimeError("judge refused")
    return "".join(b.text for b in resp.content if b.type == "text")


def parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--store", required=True)
    ap.add_argument("--judge", choices=["gemini", "claude", "packets"], default="gemini")
    ap.add_argument("--model")
    ap.add_argument("--gap", type=float, default=45)
    ap.add_argument("--worker", default="scorecard-judge")
    ap.add_argument("--ids")
    ap.add_argument("--usd-cap", type=float, default=TOTAL_CAP_USD, help="max USD for this worker family (answers + judge)")
    args = ap.parse_args()
    res = Path(args.results)
    jdir = res / "judge"
    jdir.mkdir(exist_ok=True)
    items = all_items()
    key = os.environ.get("FL_JUDGE_KEY", "")
    if args.judge != "packets" and not key:
        print(f"SKIP judge: no key for the {args.judge} judge", flush=True)
        return
    model = args.model or ("gemini-3.7-flash" if args.judge == "gemini" else "claude-opus-5-5")
    ledger = Path(os.environ.get("FL_LEDGER", DEFAULT_LEDGER))
    wanted = set(args.ids.split(",")) if args.ids else None
    n = 0
    for sub in ("answers", "heldback"):
        for p in sorted((res / sub).glob("*.json")):
            if p.name == "details.json":
                continue
            rec = json.loads(p.read_text(encoding="utf-8"))
            iid = rec["id"]
            if (wanted and iid not in wanted) or iid not in items or rec.get("status") != 200:
                continue
            if not ((rec.get("body") or {}).get("response") or "").strip():
                continue
            out = jdir / f"{iid}.json"
            h = answer_hash(rec)
            if out.exists() and json.loads(out.read_text()).get("_answer_hash") == h:
                continue
            pk = packet(items[iid], rec, args.store)
            if args.judge == "packets":
                (jdir / "packets").mkdir(exist_ok=True)
                (jdir / "packets" / f"{iid}.json").write_text(json.dumps(pk, ensure_ascii=False, indent=1))
                continue
            if ledger_usd(ledger) >= TOTAL_CAP_USD or ledger_usd(ledger, args.worker.split("-")[0]) >= args.usd_cap:
                print("spending cap reached; judge stopping", flush=True)
                break
            prompt = PROMPT.format(rubric=RUBRIC, packet=json.dumps(pk, ensure_ascii=False))
            try:
                raw = call_gemini(key, model, prompt) if args.judge == "gemini" else call_claude(key, model, prompt)
                verdict = parse_json(raw)
            except Exception as e:
                LAST_USAGE.clear()
                print(f"{iid if sub == 'answers' else 'heldback-item'}: judge failed {type(e).__name__}", flush=True)
                continue
            cost = usd(model, LAST_USAGE.get("in_tokens", 0), LAST_USAGE.get("out_tokens", 0)) if LAST_USAGE else None
            with ledger.open("a") as f:
                f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "worker": args.worker,
                                    "item": iid if sub == "answers" else "heldback-item",
                                    "purpose": f"judge ({args.judge} {model}; not an app consultation)", "model": model,
                                    "in_tokens": LAST_USAGE.get("in_tokens"), "out_tokens": LAST_USAGE.get("out_tokens"),
                                    "usd": cost}) + "\n")
            verdict.update({"id": iid, "_answer_hash": h, "_rubric": RUBRIC_VERSION, "_judge": f"{args.judge}:{model}"})
            out.write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding="utf-8")
            n += 1
            print(f"{iid if sub == 'answers' else 'heldback-item'}: judged ({verdict.get('verdict') or verdict.get('outcome_agreement')})", flush=True)
            time.sleep(args.gap)
    print(f"judged {n}")


if __name__ == "__main__":
    main()
