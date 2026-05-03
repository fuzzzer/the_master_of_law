"""
Adaptive rate limiter that respects remote servers.

Guarantees a minimum delay between successive requests to the same
host, with exponential back-off on errors.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Per-host adaptive rate limiter.

    Parameters
    ----------
    min_delay : float
        Minimum seconds between requests to the same host.
    max_delay : float
        Maximum back-off delay (cap).
    backoff_factor : float
        Multiplier applied on each consecutive error.
    """

    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
    ) -> None:
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

        # Tracks the monotonic time of the last request per host.
        self._last_request: dict[str, float] = defaultdict(float)
        # Current delay per host (increases on errors, resets on success).
        self._current_delay: dict[str, float] = defaultdict(lambda: min_delay)
        # Lock per host to serialise access.
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def acquire(self, host: str) -> None:
        """Wait until it is safe to send a request to *host*."""
        async with self._locks[host]:
            now = time.monotonic()
            elapsed = now - self._last_request[host]
            delay = self._current_delay[host]
            if elapsed < delay:
                wait = delay - elapsed
                logger.debug("Rate limiter: sleeping %.1fs for %s", wait, host)
                await asyncio.sleep(wait)
            self._last_request[host] = time.monotonic()

    def report_success(self, host: str) -> None:
        """Reset the delay for *host* after a successful request."""
        self._current_delay[host] = self.min_delay

    def report_error(self, host: str) -> None:
        """Increase the delay for *host* after a failed request."""
        current = self._current_delay[host]
        new_delay = min(current * self.backoff_factor, self.max_delay)
        self._current_delay[host] = new_delay
        logger.warning(
            "Rate limiter: back-off for %s increased to %.1fs",
            host,
            new_delay,
        )
