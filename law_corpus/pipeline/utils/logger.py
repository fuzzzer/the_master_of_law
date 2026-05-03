"""
Structured logging configuration for the pipeline.

Usage:
    from pipeline.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Processing document", extra={"doc_id": "civil_code"})
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_LOG_FORMAT = (
    "%(asctime)s │ %(levelname)-8s │ %(name)-30s │ %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger once for the whole application."""
    global _configured  # noqa: PLW0603
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "chromadb", "urllib3", "google"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (call ``setup_logging`` first for pretty output)."""
    return logging.getLogger(name)
