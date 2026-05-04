"""
Logging configuration — stdlib-based with structured output.

Provides a structlog-compatible interface using only stdlib logging,
so the server works without the structlog package installed.

When structlog becomes available (pip install structlog), this module
can be upgraded to use it. The public API stays the same:

    from app.utils.logger import get_logger, setup_logging
    logger = get_logger(__name__)
    logger.info("event_name", key="value")

Usage:
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("server_started", port=8000)
"""

from __future__ import annotations

import logging
import sys

from app.config.settings import settings

_LOGGING_CONFIGURED = False


def setup_logging() -> None:
    """Configure stdlib logging with a clean format."""
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Quieten noisy libraries
    for noisy in ("chromadb", "httpcore", "httpx", "urllib3", "google", "posthog"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _LOGGING_CONFIGURED = True


class StructuredLogger:
    """
    A thin wrapper around stdlib Logger that accepts keyword arguments
    like structlog, formatting them into the log message.

    This lets us write ``logger.info("event", key=val)`` everywhere
    and upgrade to real structlog later without code changes.
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def _format(self, msg: str, **kwargs) -> str:
        if kwargs:
            pairs = " ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{msg} | {pairs}"
        return msg

    def debug(self, msg: str, **kwargs) -> None:
        self._logger.debug(self._format(msg, **kwargs))

    def info(self, msg: str, **kwargs) -> None:
        self._logger.info(self._format(msg, **kwargs))

    def warning(self, msg: str, **kwargs) -> None:
        self._logger.warning(self._format(msg, **kwargs))

    def error(self, msg: str, exc_info: bool = False, **kwargs) -> None:
        self._logger.error(self._format(msg, **kwargs), exc_info=exc_info)

    def critical(self, msg: str, **kwargs) -> None:
        self._logger.critical(self._format(msg, **kwargs))


def get_logger(name: str) -> StructuredLogger:
    """Get a named structured logger."""
    return StructuredLogger(name)
