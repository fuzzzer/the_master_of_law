"""Model prices for the scorecard's spending record (USD per 1M tokens; thinking tokens are billed as output).

Source: https://cloud.google.com/vertex-ai/generative-ai/pricing (read 2026-10-25): Gemini 3.7 Flash introductory
price $0.75 input / $3.75 output per 1M tokens through 31 December 2026 ($1.5 / $7.5 from 1 January 2027).
"""
from __future__ import annotations

import json
from pathlib import Path

PRICES = {"gemini-3.7-flash": (0.75, 3.75)}
DEFAULT_MODEL = "gemini-3.7-flash"
TOTAL_CAP_USD = 8.0


def usd(model: str, in_tokens: int, out_tokens: int) -> float:
    pin, pout = PRICES.get(model, PRICES[DEFAULT_MODEL])
    return round(in_tokens * pin / 1e6 + out_tokens * pout / 1e6, 6)


def ledger_usd(ledger: Path, worker_prefix: str | None = None) -> float:
    """Sum of recorded USD in the ledger (all workers, or those whose name starts with worker_prefix)."""
    if not ledger.exists():
        return 0.0
    total = 0.0
    for line in ledger.read_text().splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if worker_prefix and not str(d.get("worker", "")).startswith(worker_prefix):
            continue
        total += float(d.get("usd") or 0)
    return total
