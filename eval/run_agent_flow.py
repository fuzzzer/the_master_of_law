#!/usr/bin/env python3
"""
End-to-end grounded-session runner (VERIFICATION_PROTOCOL §4, agent surface).

Unlike run_golden_retrieval.py (which exercises only the REST chat path), this
runner drives a *complete real user session* in Georgian and captures everything
that happens under the hood, so grounding can be audited step-by-step:

    1. create conversation
    2. case intake      POST /api/v1/chat/{conv}/send   (mode=case_intake)
    3. build case file  POST /api/v1/case-files/build
    4. agent flow       POST /api/v1/chat/{conv2}/agent (tools-heavy, N turns)

For every AI request it pulls the full pipeline_trace (RAG chunks, LLM prompt,
tool calls, citation verification, all mechanism steps) and writes it to disk.

Each turn's trace is scored with the reusable C1-C8 checks from
run_golden_retrieval.py so this is a *regression harness*, not a one-off.

Env: talks to the live docker stack on 127.0.0.1:8000 (dev mode = auto-admin).
Free tier is rate limited (~10-15 rpm); requests are serialized with --sleep.

Usage:
    python3 eval/run_agent_flow.py --tag agentcert
    python3 eval/run_agent_flow.py --scenario eval/agent_flow_scenario.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests
import yaml

# Reuse the exact C1-C8 checks the chat certification uses.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_golden_retrieval as gold  # noqa: E402

DEFAULT_SCENARIO = Path(__file__).resolve().parent / "agent_flow_scenario.yaml"


def api(base: str, method: str, path: str, body: dict | None = None) -> dict:
    r = requests.request(method, f"{base}{path}", json=body or {}, timeout=180)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:400]}")
    return r.json() if r.text else {}


def send_agent_with_retry(
    base: str, conv: str, message: str, case_file_id: str, retries: int = 4
) -> dict:
    """POST to the case-agent endpoint, tolerating free-tier 429s (surface as 500)."""
    body = {"message": message, "mode": "case_agent", "case_file_id": case_file_id}
    for attempt in range(retries):
        try:
            return api(base, "POST", f"/api/v1/chat/{conv}/agent", body)
        except RuntimeError as e:
            if ("429" in str(e) or "500" in str(e)) and attempt < retries - 1:
                wait = 30 * (attempt + 1)
                print(f"    rate-limited, retry in {wait}s...", flush=True)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("agent send exhausted retries")


def latest_trace_id(base: str, conv: str) -> str | None:
    """Newest trace for this conversation (admin-only endpoint; dev = auto-admin)."""
    data = api(base, "GET", f"/api/v1/traces?conversation_id={conv}&limit=1")
    items = data.get("traces") or data.get("items") or []
    return items[0]["id"] if items else None


def fetch_trace(base: str, trace_id: str) -> dict:
    return api(base, "GET", f"/api/v1/traces/{trace_id}")


def steps_by_name(trace: dict) -> dict:
    """Mirror run_golden_retrieval's step index exactly.

    {step_name: data} keeping the LAST occurrence, plus `_tool_executed_all`
    (every tool_executed data blob) which C2/C4/C5 read.
    """
    out: dict = {"_tool_executed_all": []}
    for s in trace.get("steps", []):
        out[s["step"]] = s.get("data", {})
        if s["step"] == "tool_executed":
            out["_tool_executed_all"].append(s.get("data", {}))
    return out


def load_store_urls() -> set[str]:
    """Corpus URL allow-list for C4, loaded from the article store (read-only)."""
    import sqlite3
    if not gold.STORE.exists():
        return set()
    conn = sqlite3.connect(f"file:{gold.STORE}?mode=ro&immutable=1", uri=True)
    try:
        return {r[0] for r in conn.execute("SELECT article_url FROM articles")}
    finally:
        conn.close()


def score_turn(q: dict, trace: dict, response_text: str, citations: list[dict],
               store_urls: set[str]) -> dict:
    steps = steps_by_name(trace)
    checks = {
        "C1": gold.check_c1_language(response_text),
        "C2": gold.check_c2_grounding(q, steps),
        "C3": gold.check_c3_citations(steps, citations),
        "C4": gold.check_c4_links(response_text, steps, store_urls),
        "C5": gold.check_c5_case_attribution(response_text, steps),
        "C6": gold.check_c6_deadline(response_text),
        "C7": gold.check_c7_anchoring(steps),
        "C8": gold.check_c8_threshold_domain(q, steps),
    }
    return {k: {"pass": v[0], "detail": v[1]} for k, v in checks.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--scenario", default=str(DEFAULT_SCENARIO))
    ap.add_argument("--tag", default="agentflow")
    ap.add_argument("--sleep", type=float, default=25.0,
                    help="seconds between AI requests (free-tier throttle)")
    ap.add_argument("--out-root", default="eval/results/agent_flow")
    ap.add_argument("--case-file-id", default="",
                    help="use an existing case file and skip intake+build")
    args = ap.parse_args()

    scenario = yaml.safe_load(Path(args.scenario).read_text())
    store_urls = load_store_urls()  # corpus URL allow-list for C4

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out_root) / f"{ts}_{args.tag}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"session artifacts -> {out}")

    session: dict = {"scenario": scenario.get("name"), "steps": [], "turns": []}

    if args.case_file_id:
        # Skip intake+build (e.g. when the case already exists) and go straight
        # to the tools-heavy agent flow against a known case file.
        conv = None
        case_id = args.case_file_id
        print(f"[1-3] using existing case_file_id = {case_id}")
    else:
        # 1. conversation for intake --------------------------------------------
        conv = api(args.base_url, "POST", "/api/v1/conversations", {})["id"]
        print(f"[1] intake conversation {conv}")

        # 2. case intake (Georgian facts) ---------------------------------------
        for i, msg in enumerate(scenario["intake_messages"]):
            print(f"[2.{i}] intake message ({len(msg)} chars)")
            api(args.base_url, "POST", f"/api/v1/chat/{conv}/send",
                {"message": msg, "mode": "case_intake"})
            time.sleep(args.sleep)

        # 3. build the case file (2 Gemini calls; 429-tolerant on free tier) ----
        print("[3] building case file...")
        case = None
        for attempt in range(5):
            try:
                case = api(args.base_url, "POST", "/api/v1/case-files/build",
                           {"conversation_id": conv})
                break
            except RuntimeError as e:
                if ("429" in str(e) or "500" in str(e)) and attempt < 4:
                    wait = 45 * (attempt + 1)
                    print(f"    build rate-limited, retry in {wait}s...", flush=True)
                    time.sleep(wait)
                    continue
                raise
        case_id = case["id"]
        print(f"    case_file_id = {case_id}")
        (out / "case_file.json").write_text(
            json.dumps(case, ensure_ascii=False, indent=2))
        time.sleep(args.sleep)

    # 4. agent flow (tools-heavy, Georgian) ------------------------------------
    agent_conv = api(args.base_url, "POST", "/api/v1/conversations", {})["id"]
    print(f"[4] agent conversation {agent_conv}")

    all_pass = True
    for i, turn in enumerate(scenario["agent_turns"]):
        q = turn  # has id/domain/question/must_ground_in like a golden pair
        print(f"[4.{i}] {q['id']} :: {q['question'][:60]}...")
        reply = send_agent_with_retry(
            args.base_url, agent_conv, q["question"], case_id)
        response_text = reply.get("response") or reply.get("response_text") or ""
        citations = reply.get("citations", [])

        time.sleep(1.0)
        tid = latest_trace_id(args.base_url, agent_conv)
        trace = fetch_trace(args.base_url, tid) if tid else {}

        (out / f"{q['id']}_response.txt").write_text(response_text)
        (out / f"{q['id']}_trace.json").write_text(
            json.dumps(trace, ensure_ascii=False, indent=2))

        scored = score_turn(q, trace, response_text, citations, store_urls)
        turn_pass = all(c["pass"] for c in scored.values())
        all_pass = all_pass and turn_pass
        step_names = [s["step"] for s in trace.get("steps", [])]
        tools = [s["data"].get("tool") for s in trace.get("steps", [])
                 if s["step"] == "tool_executed"]
        line = " ".join(f"{k}{'✅' if v['pass'] else '❌'}" for k, v in scored.items())
        print(f"    {line}  | steps={len(step_names)} tools={tools}")
        session["turns"].append({
            "id": q["id"], "domain": q.get("domain"), "trace_id": tid,
            "pass": turn_pass, "checks": scored, "tools_called": tools,
            "step_names": step_names, "response_len": len(response_text),
        })

    session["case_file_id"] = case_id
    session["intake_conversation"] = conv
    session["agent_conversation"] = agent_conv
    session["all_pass"] = all_pass
    (out / "session.json").write_text(
        json.dumps(session, ensure_ascii=False, indent=2))

    print(f"\n=== {'ALL PASS' if all_pass else 'FAILURES PRESENT'} ===")
    print(f"session.json -> {out / 'session.json'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
