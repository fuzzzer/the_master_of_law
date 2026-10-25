"""Answer target: the app's own backend pipeline, run in-process from any worktree.

It imports <worktree>/backend unchanged and runs exactly the REST chat path: guardrail, then the agent
pipeline with CHAT_SYSTEM (planner, retrieval, whole-code injection, generation with get_article /
browse_code / search_law tools, citation verification, faithfulness pass, repairs and guards).

Differences from the live server, recorded in every result as `target_info`:
  * Model calls go to Vertex AI express mode with the caller's Google Cloud key (FL_KEY), or to AI Studio
    when the key starts with "AIza".
  * When the corpus folder has no real vector data (marker file VECTORS_ARE_PLACEHOLDERS), the vector-search stage is replaced by keyword (BM25) search
    over the same statute chunks; the keyword stage, merge, rerank, quotas and thresholds are the real code.
  * No court-practice or binding-decision collections exist locally, so answers are grounded in statutes only.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import sys
import time
import traceback
from functools import lru_cache
from pathlib import Path

BENIGN = ("model_config_read_failed", "chroma_collection_missing")
DEFAULT_CORPUS = Path("/Volumes/Fuzzzity 2/fuzzzy_company/work/fuzzzy-law-overnight-20261025/scorecard/corpus")
HARD_TIMEOUT_S = 240


class _Tee:
    def __init__(self, stream, sink: list[str]):
        self._s, self._sink = stream, sink

    def write(self, data):
        self._sink.append(data)
        return self._s.write(data)

    def flush(self):
        self._s.flush()

    def __getattr__(self, name):
        return getattr(self._s, name)


def degraded_events(text: str) -> list[str]:
    """Log lines that show a stage was skipped or failed (429s, unavailable guardrail, failed passes)."""
    out = []
    for line in text.splitlines():
        if any(b in line for b in BENIGN):
            continue
        if re.search(r"429|RESOURCE_EXHAUSTED|_failed|_unavailable|timeout|Timeout", line):
            out.append(line[:300])
    return out


class LocalPipelineTarget:
    name = "local"

    def __init__(self, worktree: str, key: str, corpus: str | None = None):
        self.key = key
        self.worktree = Path(worktree).resolve()
        self.corpus = Path(corpus or os.environ.get("FL_CORPUS_DIR") or DEFAULT_CORPUS)
        self._log: list[str] = []
        sys.stdout = _Tee(sys.stdout, self._log)
        sys.stderr = _Tee(sys.stderr, self._log)
        os.environ.update({
            "CHROMA_PERSIST_DIR": str(self.corpus / "chroma"),
            "DATABASE_URL": "postgresql+asyncpg://none:none@127.0.0.1:1/none",
            "REDIS_URL": "redis://127.0.0.1:1/0",
            "AUTH_ENABLED": "false",
            "BYOK_REQUIRED": "true",
            "ANONYMIZED_TELEMETRY": "False",
            "LOG_LEVEL": "WARNING",
        })
        sys.path.insert(0, str(self.worktree / "backend"))
        self._setup()

    def _setup(self):
        from google import genai
        import app.integrations.vertex_ai_client as vac
        from app.services import rag_retrieval_service as rrs

        vertex = not self.key.startswith("AIza")

        @lru_cache(maxsize=4)
        def _client(api_key: str):
            opts = genai.types.HttpOptions(timeout=HARD_TIMEOUT_S * 1000)
            return genai.Client(vertexai=True, api_key=api_key, http_options=opts) if vertex else \
                genai.Client(api_key=api_key, http_options=opts)

        usage = self.usage = {"calls": 0, "in_tokens": 0, "out_tokens": 0, "models": set()}

        def _count(resp, model):
            um = getattr(resp, "usage_metadata", None)
            if um is None:
                return
            usage["in_tokens"] += int(getattr(um, "prompt_token_count", 0) or 0)
            usage["out_tokens"] += int(getattr(um, "candidates_token_count", 0) or 0) + \
                int(getattr(um, "thoughts_token_count", 0) or 0)

        def _metered(api_key: str):
            client = _client(api_key)
            if getattr(client, "_scorecard_metered", False):
                return client
            aio = client.aio.models
            orig_gen, orig_stream = aio.generate_content, aio.generate_content_stream

            async def gen(*a, **kw):
                resp = await orig_gen(*a, **kw)
                usage["calls"] += 1
                usage["models"].add(str(kw.get("model", "")))
                _count(resp, kw.get("model"))
                return resp

            async def stream(*a, **kw):
                inner = await orig_stream(*a, **kw)
                usage["calls"] += 1
                usage["models"].add(str(kw.get("model", "")))

                async def it():
                    last = None
                    async for chunk in inner:
                        if getattr(chunk, "usage_metadata", None) is not None:
                            last = chunk
                        yield chunk
                    if last is not None:
                        _count(last, kw.get("model"))
                return it()

            aio.generate_content, aio.generate_content_stream = gen, stream
            client._scorecard_metered = True
            return client

        if hasattr(vac, "_client_for_key"):
            vac._client_for_key = _metered
        self.vector_stage = "real"
        chroma_has_vectors = (self.corpus / "chroma" / "chroma.sqlite3").exists() and \
            not (self.corpus / "VECTORS_ARE_PLACEHOLDERS").exists()
        fts = self.corpus / "georgian_laws" / "chunks_fts.db"
        if not chroma_has_vectors and fts.exists():
            self._install_bm25(rrs, fts)
            self.vector_stage = "keyword (BM25) stand-in: no vectors in corpus"
        elif not chroma_has_vectors:
            self.vector_stage = "missing: no vectors and no keyword index"
        self.info = {
            "target": "local",
            "worktree": str(self.worktree),
            "git_head": _git_head(self.worktree),
            "model_route": "Vertex AI express (Google Cloud key)" if vertex else "Google AI Studio key",
            "vector_stage": self.vector_stage,
            "corpus": str(self.corpus),
            "court_practice": "absent (statutes only)",
        }

    def _install_bm25(self, rrs, fts_db: Path):
        index = json.loads((self.corpus / "georgian_laws" / "index" / "article_index.json").read_text(encoding="utf-8"))

        def terms(query: str) -> str:
            toks = [t for t in re.findall(r"[ა-ჿ\w]+", query.lower()) if len(t) >= 3]
            return " OR ".join(f'"{t[: max(4, len(t) - 2)] if len(t) > 5 else t}"*' for t in toks[:12])

        def hits_for(queries: list[str], per_query: int = 40) -> list[dict]:
            conn = sqlite3.connect(f"file:{fts_db}?mode=ro", uri=True)
            hits = []
            for qi, q in enumerate(queries):
                expr = terms(q)
                if not expr:
                    continue
                rows = conn.execute("SELECT chunk_id, content, bm25(c) AS s FROM c WHERE c MATCH ? ORDER BY s LIMIT ?",
                                    (expr, per_query)).fetchall()
                if not rows:
                    continue
                best = rows[0][2]
                for cid, content, s in rows:
                    a = index.get(cid, {})
                    meta = {"code_name": a.get("code_name", ""), "article_number": a.get("article_number", ""),
                            "article_title": a.get("article_title", ""), "_collection": "georgian_laws"}
                    hits.append({"chunk_id": cid, "content": content, "metadata": meta,
                                 "distance": round(0.2 + 0.6 * (1 - s / best), 4) if best else 0.5,
                                 "source": "bm25", "query_index": qi})
            conn.close()
            return hits

        async def stage_1(self_, queries, collections=None):
            hits = await asyncio.to_thread(hits_for, queries)
            try:
                full = {i["chunk_id"]: i for i in await self_.chroma.get_by_ids_async([h["chunk_id"] for h in hits])}
                for h in hits:
                    if h["chunk_id"] in full:
                        m = dict(full[h["chunk_id"]].get("metadata") or {})
                        m["_collection"] = "georgian_laws"
                        h["metadata"] = m
            except Exception:
                pass
            return hits

        rrs.RAGRetrievalService._stage_1_vector_search = stage_1

    def scrub(self, s: str) -> str:
        return s.replace(self.key, "[REDACTED]") if self.key else s

    async def answer(self, item: dict) -> dict:
        from app.config.request_context import set_byok_key
        from app.prompts.chat import CHAT_SYSTEM
        from app.services.agent_pipeline_service import get_agent_pipeline_service
        from app.services.guardrail_service import get_guardrail_service
        from app.services.trace_service import get_current_trace, start_trace

        set_byok_key(self.key)
        msg = item["message"]
        rec = {"id": item["id"], "message": msg, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        start_trace(entry_point="rest_chat", user_message=msg)
        self._log.clear()
        self.usage.update({"calls": 0, "in_tokens": 0, "out_tokens": 0, "models": set()})
        t0 = time.time()
        try:
            decision = await get_guardrail_service().classify(msg, user_tier="FREE", in_conversation=False)
            rec["guardrail"] = {"category": decision.category, "should_proceed": decision.should_proceed}
            if not decision.should_proceed:
                rec["body"] = {"response": decision.response_text or "", "citations": [], "retrieved_chunks": []}
            else:
                result = await get_agent_pipeline_service().run(
                    user_message=msg, conversation_history=[], system_prompt=CHAT_SYSTEM.template,
                    rag_collections=None, is_case_chat=False, db=None)
                text = re.sub(r"\s*\[CASE_READY\]\s*", "", result.response_text or "").rstrip()
                chunks = [{"code_name": (c.get("metadata") or {}).get("code_name", ""),
                           "article_number": (c.get("metadata") or {}).get("article_number", ""),
                           "collection": (c.get("metadata") or {}).get("_collection", "")}
                          for c in (result.chunks or [])[:20]]
                rec["body"] = {"response": text, "citations": result.verified_citations or [], "retrieved_chunks": chunks,
                               "tool_calls": [t.tool_name for t in (result.tool_results or [])]}
            rec["status"], rec["error"] = 200, None
        except Exception as e:
            rec["status"] = 500
            rec["error"] = self.scrub(f"{type(e).__name__}: {e}")[:1500]
            rec["traceback"] = self.scrub(traceback.format_exc())[-3000:]
        rec["latency_s"] = round(time.time() - t0, 2)
        tr = get_current_trace()
        ev = degraded_events(self.scrub("".join(self._log)))
        if tr is not None:
            for st in tr.steps:
                d = st.get("data") or {}
                if st.get("name") == "phase_1_plan_failed" or (isinstance(d, dict) and d.get("failed")):
                    ev.append(f"trace:{st.get('name')}")
            rec["trace_step_names"] = [s.get("name") for s in tr.steps]
        rec["degraded"], rec["degraded_events"] = bool(ev), ev
        rec["usage"] = {"model_calls": self.usage["calls"], "in_tokens": self.usage["in_tokens"],
                        "out_tokens": self.usage["out_tokens"], "models": sorted(m for m in self.usage["models"] if m)}
        return rec


def _git_head(path: Path) -> str:
    try:
        import subprocess
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return ""
