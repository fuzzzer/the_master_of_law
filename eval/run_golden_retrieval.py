#!/usr/bin/env python3
"""
Golden retrieval/grounding runner — plan 4.2 + certification driver (§4).

Sends every question of eval/golden_retrieval.yaml through the live backend
(serialized, 429-tolerant), fetches each request's pipeline trace, and scores
the automated certification checks C1–C8. Writes a JSON report + markdown
scorecard to eval/results/golden/.

Usage:
    python3 eval/run_golden_retrieval.py [--ids G1,G2] [--sleep 25]
        [--base-url http://127.0.0.1:8000] [--tag phase4]

Exit code 1 if any check fails on any question (CI gate: C2 at minimum —
use --checks C2 to gate on grounding only).
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
ROOT = EVAL_DIR.parent
STORE = ROOT / "law_corpus" / "data" / "georgian_laws" / "article_store.db"

# Mirrors backend threshold_service._CODE_NAME_TO_DOMAIN (C8)
CODE_NAME_TO_DOMAIN = {
    "ნარკოტიკული საშუალებების შესახებ კანონი": "criminal",
    "სისხლის სამართლის კოდექსი": "criminal",
    "სისხლის სამართლის საპროცესო კოდექსი": "criminal",
    "სამოქალაქო კოდექსი": "civil",
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი": "administrative",
    "შრომის კოდექსი": "labor",
}

CASE_NUMBER_RE = re.compile(
    r"\b(?:ას|ბს|გს)-\d+(?:-\d+)*\b|\b\d+(?:აპ|აგ|კოლ|კ)-\d+\b"
)
ACTION_RE = re.compile(r"სასამართლო|საჩივ|სარჩელ|გაასაჩივრ|იჩივლ|მიმართ")
DEADLINE_RE = re.compile(r"ვადა|ვადაში|ვადის|დღის განმავლობაში|გადაამოწმ|დაუყოვნებლ")


# ── tiny YAML reader (flat schema of golden_retrieval.yaml only) ─────────

def load_golden(path: Path) -> list[dict]:
    questions: list[dict] = []
    current: dict | None = None
    target: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  - id:"):
            current = {"id": line.split(":", 1)[1].strip(), "must_ground_in": []}
            questions.append(current)
            target = None
        elif line.startswith("      - code:"):
            target = {"code": line.split(":", 1)[1].strip()}
            current["must_ground_in"].append(target)
        elif line.startswith("        ") and target is not None:
            key, val = line.strip().split(":", 1)
            target[key] = json.loads(val.strip()) if val.strip().startswith('"') else val.strip().strip("'")
        elif line.startswith("    ") and current is not None and ":" in line:
            key, val = line.strip().split(":", 1)
            if key != "must_ground_in":
                current[key] = json.loads(val.strip()) if val.strip().startswith('"') else val.strip()
    return questions


# ── HTTP helpers ─────────────────────────────────────────────────────────

def api(base: str, method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())


def send_with_retry(base: str, conv: str, message: str, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            return api(base, "POST", f"/api/v1/chat/{conv}/send", {"message": message})
        except Exception as e:
            wait = 35 * (attempt + 1)
            print(f"    retry after error ({e}); sleeping {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"chat send failed after {retries} attempts")


# ── checks ───────────────────────────────────────────────────────────────

def strip_links(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown links → label
    return re.sub(r"https?://\S+", " ", text)


def check_c1_language(response: str) -> tuple[bool, dict]:
    latin = re.findall(r"[A-Za-z]{2,}", strip_links(response))
    return (not latin), {"latin_fragments": latin[:10]}


def _article_in_chunks(target: dict, chunks: list[dict]) -> bool:
    code, art = target["code"], str(target["article"])
    for c in chunks:
        cid = str(c.get("chunk_id", ""))
        if cid.startswith(code) and re.search(rf"article_{art}(\.|$|:)", cid):
            return True
        if (
            c.get("article_number") == target.get("article_number")
            and target.get("code_name", "") in (c.get("code_name") or "")
        ):
            return True
    return False


def check_c2_grounding(q: dict, steps: dict) -> tuple[bool, dict]:
    chunks = (steps.get("rag_final_selection") or {}).get("chunks", [])
    injected_codes = [
        c["code"] for c in (steps.get("full_code_injected") or {}).get("codes", [])
    ]
    tool_articles: list[str] = []
    for te in steps.get("_tool_executed_all", []):
        if te.get("tool") == "get_article" and te.get("result", {}).get("found"):
            tool_articles.append(
                f"{te['result'].get('code','')}|{te['result'].get('article','')}"
            )
    detail = {}
    ok = True
    for target in q["must_ground_in"]:
        grounded = (
            _article_in_chunks(target, chunks)
            or target["code"] in injected_codes
            or any(
                target.get("article_number", "") in ta or str(target["article"]) in ta
                for ta in tool_articles
            )
        )
        detail[f"{target['code']}:{target['article']}"] = grounded
        ok = ok and grounded
    return ok, detail


def check_c3_citations(steps: dict, response_citations: list[dict]) -> tuple[bool, dict]:
    cv = steps.get("citation_verification")
    not_found = (cv or {}).get("not_found", [])
    unresolved = [
        c for c in response_citations
        if c.get("verified") and not c.get("article_url")
    ]
    return (not not_found), {
        "not_found": not_found,
        "verified_without_url": len(unresolved),
    }


def check_c4_links(response: str, steps: dict, store_urls: set[str]) -> tuple[bool, dict]:
    urls = set(re.findall(r"https?://matsne\.gov\.ge[^\s)\]\"']+", response))
    chunks = (steps.get("rag_final_selection") or {}).get("chunks", [])
    known = store_urls | {c.get("article_url", "") for c in chunks}
    for te in steps.get("_tool_executed_all", []):
        u = te.get("result", {}).get("url")
        if u:
            known.add(u)
    invented = sorted(u for u in urls if u.rstrip(".,;") not in known)
    return (not invented), {"urls": len(urls), "invented": invented}


def check_c5_case_attribution(response: str, steps: dict) -> tuple[bool, dict]:
    chunks = (steps.get("rag_final_selection") or {}).get("chunks", [])
    court_in_context = any(
        c.get("collection") in ("court_practice", "grand_chamber") for c in chunks
    )
    practice_claims = bool(re.search(
        r"სასამართლო პრაქტიკ|პრაქტიკის მიხედვით|პრაქტიკით დადგენილ"
        r"|სასამართლომ განმარტ|უზენაესმა|უზენაესი სასამართლოს განმარტ",
        response,
    ))
    cases_cited = CASE_NUMBER_RE.findall(strip_links(response))
    # the trace's not_found reflects a mid-loop state; a case is only truly
    # hallucinated if it SURVIVED into the final response
    ccv = steps.get("case_citation_verification") or {}
    flagged = {h.get("case_number") for h in ccv.get("not_found", [])}
    hallucinated = sorted(flagged & set(cases_cited))
    if hallucinated:
        return False, {"hallucinated_cases": hallucinated}
    if court_in_context and practice_claims and not cases_cited:
        return False, {"reason": "practice-based claims without case numbers"}
    return True, {"cases_cited": cases_cited, "court_in_context": court_in_context,
                  "removed_by_correction": sorted(flagged - set(cases_cited))}


def check_c6_deadline(response: str) -> tuple[bool, dict]:
    advises_action = bool(ACTION_RE.search(response))
    has_deadline = bool(DEADLINE_RE.search(response))
    return (not advises_action or has_deadline), {
        "advises_action": advises_action,
        "mentions_deadline": has_deadline,
    }


def check_c7_anchoring(steps: dict) -> tuple[bool, dict]:
    a = steps.get("anchoring_check") or {}
    rate = a.get("unanchored_rate", 0.0)
    return (rate < 0.05), {
        "unanchored_rate": rate,
        "claim_paragraphs": a.get("claim_paragraphs"),
        "samples": a.get("unanchored_samples", []),
    }


def check_c8_threshold_domain(q: dict, steps: dict) -> tuple[bool, dict]:
    chunks = (steps.get("rag_final_selection") or {}).get("chunks", [])
    domain = q.get("domain")
    # family/land questions live in the civil code
    domain_alias = {"family": "civil", "land": "civil", "personal_data": None,
                    "commercial": None, "constitutional": None}
    expected = domain_alias.get(domain, domain)
    polluting = []
    for c in chunks:
        if not str(c.get("chunk_id", "")).startswith("threshold_"):
            continue
        entry_domain = CODE_NAME_TO_DOMAIN.get(c.get("code_name", ""))
        if expected and entry_domain and entry_domain != expected:
            polluting.append(c["chunk_id"])
    return (not polluting), {"polluting_thresholds": polluting}


# ── main ─────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--ids", default="", help="comma-separated subset, e.g. G1,G2")
    ap.add_argument("--sleep", type=int, default=25, help="seconds between questions")
    ap.add_argument("--tag", default="run")
    ap.add_argument("--checks", default="C1,C2,C3,C4,C5,C6,C7,C8",
                    help="which checks gate the exit code")
    args = ap.parse_args()

    golden = load_golden(EVAL_DIR / "golden_retrieval.yaml")
    if args.ids:
        wanted = set(args.ids.split(","))
        golden = [q for q in golden if q["id"] in wanted]

    store_urls: set[str] = set()
    if STORE.exists():
        conn = sqlite3.connect(f"file:{STORE}?mode=ro&immutable=1", uri=True)
        store_urls = {r[0] for r in conn.execute("SELECT article_url FROM articles")}
        conn.close()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = EVAL_DIR / "results" / "golden" / f"{stamp}_{args.tag}"
    out_dir.mkdir(parents=True, exist_ok=True)

    gate_checks = set(args.checks.split(","))
    results = []
    for i, q in enumerate(golden):
        print(f"[{q['id']}] {q['question'][:60]}…")
        conv = api(args.base_url, "POST", "/api/v1/conversations", {})["id"]
        reply = send_with_retry(args.base_url, conv, q["question"])
        response = reply.get("response", "")

        traces = api(args.base_url, "GET",
                     f"/api/v1/traces?conversation_id={conv}&limit=1")
        trace_list = traces if isinstance(traces, list) else traces.get("traces", [])
        trace_id = trace_list[0]["id"] if trace_list else None
        trace = api(args.base_url, "GET", f"/api/v1/traces/{trace_id}") if trace_id else {"steps": []}

        steps: dict = {"_tool_executed_all": []}
        for s in trace.get("steps", []):
            steps[s["step"]] = s.get("data", {})  # keeps the LAST occurrence
            if s["step"] == "tool_executed":
                steps["_tool_executed_all"].append(s.get("data", {}))

        checks = {
            "C1": check_c1_language(response),
            "C2": check_c2_grounding(q, steps),
            "C3": check_c3_citations(steps, reply.get("citations", [])),
            "C4": check_c4_links(response, steps, store_urls),
            "C5": check_c5_case_attribution(response, steps),
            "C6": check_c6_deadline(response),
            "C7": check_c7_anchoring(steps),
            "C8": check_c8_threshold_domain(q, steps),
        }
        row = {
            "id": q["id"],
            "domain": q.get("domain"),
            "conversation_id": conv,
            "trace_id": trace_id,
            "checks": {k: {"pass": v[0], **v[1]} for k, v in checks.items()},
            "all_pass": all(v[0] for k, v in checks.items() if k in gate_checks),
        }
        results.append(row)
        (out_dir / f"{q['id']}_response.txt").write_text(response, encoding="utf-8")
        (out_dir / f"{q['id']}_trace.json").write_text(
            json.dumps(trace, ensure_ascii=False, indent=1), encoding="utf-8")
        marks = " ".join(f"{k}{'✓' if v[0] else '✗'}" for k, v in checks.items())
        print(f"    {marks}")
        if i < len(golden) - 1:
            time.sleep(args.sleep)

    passed = sum(1 for r in results if r["all_pass"])
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "tag": args.tag,
        "gate_checks": sorted(gate_checks),
        "total": len(results),
        "passed": passed,
        "results": results,
    }
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [f"# Golden grounding run — {stamp} ({args.tag})", "",
             f"Gate: {'+'.join(sorted(gate_checks))} — **{passed}/{len(results)} passed**", "",
             "| id | domain | " + " | ".join(f"C{i}" for i in range(1, 9)) + " | trace |",
             "|----|--------|" + "----|" * 8 + "-------|"]
    for r in results:
        marks = " | ".join("✅" if r["checks"][f"C{i}"]["pass"] else "❌" for i in range(1, 9))
        lines.append(f"| {r['id']} | {r['domain']} | {marks} | `{r['trace_id']}` |")
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n{passed}/{len(results)} passed (gate: {','.join(sorted(gate_checks))})")
    print(f"report → {out_dir}")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
