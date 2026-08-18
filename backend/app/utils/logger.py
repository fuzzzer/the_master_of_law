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
import re
import sys

from app.config.settings import settings

_LOGGING_CONFIGURED = False

# ── Secret redaction ─────────────────────────────────────────
# Under bring-your-own-key the caller's Google credential travels in the
# WebSocket URL, because browsers cannot set headers on a WebSocket
# handshake. Uvicorn's access logger writes the full request line, so
# without this every chat connection would deposit a working, billable
# third-party API key into the container logs — and from there into any
# log shipper, backup or support paste. Redaction happens at the logging
# layer rather than at each call site precisely because the leak comes
# from code we do not own.
_SECRET_PATTERNS = (
    # api_key=... in a query string, up to the next separator.
    re.compile(r"(api[_-]?key=)[^&\s\"']+", re.IGNORECASE),
    # A Google AI Studio key anywhere at all, however it got there.
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
)


def redact_secrets(text: str) -> str:
    """Replace anything that looks like a caller credential."""
    text = _SECRET_PATTERNS[0].sub(r"\1<redacted>", text)
    return _SECRET_PATTERNS[1].sub("AIza<redacted>", text)


class _RedactingFilter(logging.Filter):
    """Scrub credentials from a record before any handler formats it."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - never let logging break a request
            return True

        if "AIza" in message or "api_key=" in message.lower():
            record.msg = redact_secrets(message)
            record.args = ()
        return True


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

    redactor = _RedactingFilter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(redactor)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Uvicorn installs its own handlers and sets propagate=False on these, so
    # the root handler above never sees their records. The access logger is
    # the one that writes request URLs — the exact place a WebSocket key would
    # surface — so the filter is attached to each of them directly.
    for uvicorn_logger in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        log = logging.getLogger(uvicorn_logger)
        log.addFilter(redactor)
        for h in log.handlers:
            h.addFilter(redactor)

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
