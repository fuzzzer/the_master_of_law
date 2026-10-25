"""Answer target: a running Fuzzzy Law server over HTTP (default: the live testing server).

One consultation = create a conversation, then one chat send, exactly as the app does. The caller's key
(the live server accepts only Google AI Studio keys, "AIza...") is sent only in the X-API-Key header and is
never printed or stored; error texts are scrubbed of it.
"""
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://law-api.fuzzzycore.com"
UA = "fuzzzy-law-scorecard/1.0 (owner test)"


class LiveHttpTarget:
    name = "live"

    def __init__(self, key: str, base: str = DEFAULT_BASE, device_id: str = "scorecard-20261025", timeout_s: float = 600):
        self.key, self.base, self.device_id, self.timeout_s = key, base.rstrip("/"), device_id, timeout_s
        self.info = {"target": "live", "base_url": self.base, "key_kind": "AI Studio" if key.startswith("AIza") else "other",
                     "note": "live server: vector search and court-practice collections as deployed"}

    def scrub(self, s: str) -> str:
        return s.replace(self.key, "[REDACTED]") if self.key else s

    def _request(self, method: str, path: str, body: dict | None, timeout: float):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={
            "User-Agent": UA, "Content-Type": "application/json", "X-API-Key": self.key, "X-Device-Id": self.device_id})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8"), time.time() - t, None
        except urllib.error.HTTPError as e:
            return e.code, self.scrub(e.read().decode("utf-8", "replace")), time.time() - t, f"HTTP {e.code}"
        except Exception as e:
            return None, "", time.time() - t, self.scrub(f"{type(e).__name__}: {e}")

    def _answer_sync(self, item: dict) -> dict:
        rec = {"id": item["id"], "message": item["message"], "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        st, raw, _, err = self._request("POST", "/api/v1/conversations", {"title": f"scorecard {item['id']}"}, 60)
        if st not in (200, 201):
            rec.update({"status": st, "error": f"create failed: {err} {raw[:300]}", "latency_s": None,
                        "degraded": True, "degraded_events": ["conversation create failed"]})
            return rec
        conv_id = json.loads(raw)["id"]
        st, raw, lat, err = self._request("POST", f"/api/v1/chat/{conv_id}/send", {"message": item["message"]}, self.timeout_s)
        rec.update({"status": st, "latency_s": round(lat, 2), "error": err, "conversation_id": conv_id})
        if st == 200:
            try:
                rec["body"] = json.loads(raw)
            except json.JSONDecodeError:
                rec["error"], rec["raw_text"] = "non-json body", raw[:2000]
        else:
            rec["raw_text"] = raw[:2000]
        rec["degraded"] = st == 429
        rec["degraded_events"] = ["HTTP 429"] if st == 429 else []
        return rec

    async def answer(self, item: dict) -> dict:
        return await asyncio.to_thread(self._answer_sync, item)
