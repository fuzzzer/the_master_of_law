"""Talks to the backend exactly like the Flutter app does (BYOK, one WebSocket per message, 60 s inactivity timeout)."""
import asyncio, json, os, sys, time, uuid
from pathlib import Path
import httpx, websockets

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from app.utils.script_purity import foreign_script_words  # noqa: E402 — the app's own check

BASE = os.environ.get("QA_BASE", "https://law-api.fuzzzycore.com")
WS = BASE.replace("https://","wss://").replace("http://","ws://")
KEY = [l.split("=", 1)[1].strip() for l in (Path(__file__).resolve().parents[2] / "backend/.env").read_text().splitlines()
    if l.startswith("GEMINI_API_KEY=")][0]
OUT = Path(__file__).parent / "logs"
OUT.mkdir(exist_ok=True)


def headers(device):
    return {"X-API-Key": KEY, "X-Device-Id": device}


async def new_conversation(device, title=None):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/v1/conversations", json={"title": title}, headers=headers(device))
        r.raise_for_status()
        return r.json()["id"]


async def turn(ws, message, mode="chat", case_file_id=None):
    payload = {"message": message, "mode": mode}
    if case_file_id:
        payload["case_file_id"] = case_file_id
    await ws.send(json.dumps(payload))
    t0 = last = time.monotonic()
    max_gap, text, events = 0.0, "", []
    while True:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=60)  # app's inactivity timeout
        except asyncio.TimeoutError:
            events.append({"type": "CLIENT_TIMEOUT_60s"})
            break
        now = time.monotonic(); max_gap = max(max_gap, now - last); last = now
        d = json.loads(raw)
        if d.get("type") == "chunk":
            text += d.get("content", "")
        else:
            events.append(d)
        if d.get("type") in ("done", "error"):
            break
    return {"message": message, "response": text, "events": events,
            "seconds": round(time.monotonic() - t0, 1), "max_gap": round(max_gap, 1)}


async def dialogue(name, messages, mode="chat", device=None, case_file_id=None, conv=None):
    device = device or f"qa-{name}-{uuid.uuid4().hex[:6]}"
    conv = conv or await new_conversation(device)
    url = f"{WS}/api/v1/chat/{conv}/ws?api_key={KEY}&device_id={device}&model_strong={os.environ.get('QA_STRONG','gemini-3.6-flash')}&model_cheap={os.environ.get('QA_CHEAP','gemini-3.1-flash-lite')}"
    turns = []
    if True:  # the app opens one socket per message
        for m in messages:
            for attempt in range(4):
                async with websockets.connect(url, max_size=None, open_timeout=15) as ws:
                    t = await turn(ws, m, mode, case_file_id)
                err = next((e for e in t["events"] if e.get("type") == "error"), None)
                if err and err.get("code") == "ai_quota_exhausted":
                    t["quota_retries"] = attempt + 1
                    await asyncio.sleep(max(err.get("retry_after_s") or 0, 90))
                    continue
                break
            turns.append(t)
            await asyncio.sleep(int(os.environ.get('QA_PAUSE','40')))
    rec = {"name": name, "device": device, "conversation_id": conv, "turns": turns}
    (OUT / f"{name}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    return rec


def summarize(rec):
    print(f"\n######## {rec['name']}  conv={rec['conversation_id']}")
    for t in rec["turns"]:
        types = [e.get("type") for e in t["events"]]
        done = next((e for e in t["events"] if e.get("type") == "done"), {})
        err = next((e for e in t["events"] if e.get("type") in ("error", "CLIENT_TIMEOUT_60s")), None)
        print(f"\n>>> {t['message'][:200]}")
        print(f"[{t['seconds']}s, max gap {t['max_gap']}s, events={types}]")
        if err: print("ERROR:", err)
        cits = done.get("citations") or []
        print("citations:", [ (c.get("code_name"), c.get("article_number"), c.get("paragraph"), c.get("sub_point"), c.get("verified"), c.get("unverified_reason")) for c in cits][:15])
        if done and not (done.get("full_response") or "").strip():
            print("REJECT: empty answer delivered as done")
        foreign = foreign_script_words(t["response"])
        if foreign:
            print("REJECT: foreign-script letters in a Georgian answer:", foreign)
        print(t["response"][:6000])


if __name__ == "__main__":
    scen = json.loads(Path(sys.argv[1]).read_text())
    async def main():
        for s in scen:
            r = await dialogue(s["name"], s["messages"], s.get("mode", "chat"))
            summarize(r); sys.stdout.flush()
    asyncio.run(main())
