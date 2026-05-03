"""
Pipeline progress tracking and checkpointing.

Checkpoints are JSON files written to ``settings.checkpoint_dir``.
If the pipeline crashes at any stage, it can resume from the last
saved checkpoint rather than restarting from scratch.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import orjson

from pipeline.config import settings
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class ProgressTracker:
    """Track pipeline stage progress and persist checkpoints."""

    def __init__(self, stage: str) -> None:
        self.stage = stage
        self._checkpoint_path = settings.checkpoint_dir / f"{stage}_checkpoint.json"
        self._state: dict[str, Any] = self._load()
        self._start_time: float = time.monotonic()

    # ── Persistence ──────────────────────────────────────────

    def _load(self) -> dict[str, Any]:
        """Load existing checkpoint or return empty state."""
        if self._checkpoint_path.exists():
            try:
                data = orjson.loads(self._checkpoint_path.read_bytes())
                logger.info(
                    "Resumed checkpoint for stage=%s — %d items completed",
                    self.stage,
                    data.get("completed_count", 0),
                )
                return dict(data)
            except (orjson.JSONDecodeError, KeyError):
                logger.warning("Corrupt checkpoint for stage=%s — starting fresh", self.stage)
        return {
            "stage": self.stage,
            "completed_items": [],
            "completed_count": 0,
            "failed_items": [],
            "last_updated": None,
            "metadata": {},
        }

    def save(self) -> None:
        """Persist current state to disk."""
        settings.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._checkpoint_path.write_bytes(orjson.dumps(self._state, option=orjson.OPT_INDENT_2))

    # ── Tracking API ─────────────────────────────────────────

    def is_completed(self, item_id: str) -> bool:
        """Return True if *item_id* was already processed in a prior run."""
        return item_id in set(self._state["completed_items"])

    def mark_completed(self, item_id: str) -> None:
        """Mark *item_id* as successfully processed."""
        completed = self._state["completed_items"]
        if item_id not in completed:
            completed.append(item_id)
            self._state["completed_count"] = len(completed)

    def mark_failed(self, item_id: str, error: str) -> None:
        """Record a failure for *item_id*."""
        self._state["failed_items"].append({
            "item_id": item_id,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def set_metadata(self, key: str, value: Any) -> None:
        self._state["metadata"][key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self._state["metadata"].get(key, default)

    @property
    def completed_count(self) -> int:
        return int(self._state["completed_count"])

    @property
    def failed_count(self) -> int:
        return len(self._state["failed_items"])

    @property
    def completed_ids(self) -> set[str]:
        return set(self._state["completed_items"])

    def reset(self) -> None:
        """Clear all progress (use with care)."""
        if self._checkpoint_path.exists():
            self._checkpoint_path.unlink()
        self._state = {
            "stage": self.stage,
            "completed_items": [],
            "completed_count": 0,
            "failed_items": [],
            "last_updated": None,
            "metadata": {},
        }

    def summary(self) -> dict[str, Any]:
        """Return a human-readable summary of progress."""
        elapsed = time.monotonic() - self._start_time
        return {
            "stage": self.stage,
            "completed": self.completed_count,
            "failed": self.failed_count,
            "elapsed_seconds": round(elapsed, 1),
        }
