"""Read-only probes of a running Fuzzzy Law server (default: the live testing server). GET requests only.

Usage: [FL_KEY=<AI Studio key>] python -I live_probes.py --out <dir> [--base-url URL]
Checks: health and readiness, reported version, key-handling messages (no key, malformed key, fake AI Studio
key, and the real key when FL_KEY is set), the free law browse and search (no key), and latency of a cheap
endpoint (10 calls). Writes <dir>/live_probes.json and <dir>/live_probes.md. The key is sent only as a header,
never printed or stored.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "fuzzzy-law-scorecard/1.0 (owner test, read-only)"
FAKE_AISTUDIO = "AIza" + "0" * 35


def get(base: str, path: str, key: str | None = None, timeout: float = 30):
    headers = {"User-Agent": UA, "X-Device-Id": "scorecard-probe"}
    if key is not None:
        headers["X-API-Key"] = key
    t = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers), timeout=timeout) as r:
            raw, st = r.read().decode("utf-8", "replace"), r.status
    except urllib.error.HTTPError as e:
        raw, st = e.read().decode("utf-8", "replace"), e.code
    except Exception as e:
        return {"status": None, "error": type(e).__name__, "latency_s": round(time.time() - t, 3)}
    real = os.environ.get("FL_KEY", "")
    if real:
        raw = raw.replace(real, "[REDACTED]")
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        body = raw[:500]
    return {"status": st, "latency_s": round(time.time() - t, 3), "body": body}


def short(body, n=400):
    s = json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body
    return s[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-url", default="https://law-api.fuzzzycore.com")
    a = ap.parse_args()
    base = a.base_url.rstrip("/")
    key = os.environ.get("FL_KEY") or None
    r: dict = {"base_url": base, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "real_key_present": bool(key)}
    r["health"] = get(base, "/api/v1/health")
    r["ready"] = get(base, "/api/v1/health/ready")
    hb = r["health"].get("body") if isinstance(r["health"].get("body"), dict) else {}
    r["reported_version"] = hb.get("version")
    r["openapi_no_key"] = {k: v for k, v in get(base, "/api/v1/openapi.json").items() if k != "body"}
    r["key_messages"] = {
        "no_key": get(base, "/api/v1/api-keys/validate"),
        "malformed_key": get(base, "/api/v1/api-keys/validate", key="not-a-real-key"),
        "fake_ai_studio_key": get(base, "/api/v1/api-keys/validate", key=FAKE_AISTUDIO),
    }
    if key:
        r["key_messages"]["real_key"] = get(base, "/api/v1/api-keys/validate", key=key)
        oa = get(base, "/api/v1/openapi.json", key=key)
        r["openapi_with_key_version"] = (oa.get("body") or {}).get("info", {}).get("version") if isinstance(oa.get("body"), dict) else None
    codes = get(base, "/api/v1/laws/codes")
    r["laws_codes"] = {"status": codes["status"], "latency_s": codes["latency_s"],
                       "total": (codes.get("body") or {}).get("total") if isinstance(codes.get("body"), dict) else None}
    q = urllib.parse.quote("ხანდაზმულობის ვადა")
    s1 = get(base, f"/api/v1/laws/search?q={q}&top_k=5")
    r["laws_search_no_key"] = {"status": s1["status"], "latency_s": s1["latency_s"],
                               "total": (s1.get("body") or {}).get("total") if isinstance(s1.get("body"), dict) else None,
                               "body_if_error": short(s1.get("body")) if s1["status"] != 200 else None}
    if key:
        s2 = get(base, f"/api/v1/laws/search?q={q}&top_k=5", key=key)
        r["laws_search_with_key"] = {"status": s2["status"], "total": (s2.get("body") or {}).get("total")
                                     if isinstance(s2.get("body"), dict) else None}
    lat = []
    for _ in range(10):
        lat.append(get(base, "/api/v1/health")["latency_s"])
        time.sleep(0.5)
    r["cheap_endpoint_latency_s"] = {"median": round(statistics.median(lat), 3), "max": max(lat), "n": len(lat)}

    checks = [
        ("Server healthy", r["health"]["status"] == 200),
        ("Server ready", r["ready"]["status"] == 200),
        ("Version is a real build number, not the 0.1.0 placeholder", r["reported_version"] not in (None, "0.1.0")),
        ("No key: clear message", r["key_messages"]["no_key"]["status"] == 401),
        ("Malformed key: clear message", r["key_messages"]["malformed_key"]["status"] in (400, 401)),
        ("Fake AI Studio key refused", r["key_messages"]["fake_ai_studio_key"]["status"] in (400, 401, 403)),
        ("Free law list works without a key", r["laws_codes"]["status"] == 200 and (r["laws_codes"]["total"] or 0) > 0),
        ("Free law search returns results without a key", r["laws_search_no_key"]["status"] == 200 and (r["laws_search_no_key"]["total"] or 0) > 0),
        ("Cheap endpoint median under 1 s", r["cheap_endpoint_latency_s"]["median"] < 1.0),
    ]
    if key:
        checks.append(("Real AI Studio key accepted", r["key_messages"]["real_key"]["status"] == 200))
    r["checks"] = [{"check": c, "pass": bool(p)} for c, p in checks]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "live_probes.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# Live server probes ({base}, {r['ts']})", "", "| Check | Result |", "|---|---|"]
    md += [f"| {c} | {'PASS' if p else 'FAIL'} |" for c, p in checks]
    md += ["", f"- Reported version: {r['reported_version']}; readiness: {short(r['ready'].get('body'), 300)}",
           f"- Key messages: " + "; ".join(f"{k}: HTTP {v['status']} {short(v.get('body'), 220)}" for k, v in r["key_messages"].items()),
           f"- Free search without key: HTTP {r['laws_search_no_key']['status']}, {r['laws_search_no_key']['total']} results"
           + (f" ({r['laws_search_no_key']['body_if_error']})" if r['laws_search_no_key']['body_if_error'] else ""),
           f"- Health latency over 10 calls: median {r['cheap_endpoint_latency_s']['median']} s, max {r['cheap_endpoint_latency_s']['max']} s",
           "" if key else "- No AI Studio key present: real-key check and full answer probes skipped."]
    (out / "live_probes.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
