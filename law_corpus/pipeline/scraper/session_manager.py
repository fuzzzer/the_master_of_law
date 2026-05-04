"""
Managed async HTTP session with retry logic, connection pooling,
and respectful User-Agent handling.
"""

from __future__ import annotations

import random
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pipeline.config import settings
from pipeline.scraper.rate_limiter import RateLimiter
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Rotating user-agent pool — all clearly identify as bots.
_USER_AGENTS = [
    settings.scrape_user_agent,
    "LawCorpusBot/1.0 (legal-research; +https://github.com/fuzzzy)",
    "GeorgianLawIndexer/1.0 (academic; research-bot)",
]


class SessionManager:
    """
    Async HTTP session wrapper around ``httpx.AsyncClient``.

    Features:
    - Automatic retry with exponential back-off (2 → 4 → 8 → 16 s)
    - Per-host rate limiting via ``RateLimiter``
    - Rotating User-Agent
    - Connection pooling
    - UTF-8 encoding for Georgian text
    """

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.rate_limiter = rate_limiter or RateLimiter(
            min_delay=settings.scrape_delay_seconds,
        )
        self._client: httpx.AsyncClient | None = None
        self._timeout = timeout

    async def __aenter__(self) -> "SessionManager":
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout, connect=10.0),
            limits=httpx.Limits(
                max_connections=settings.scrape_max_concurrent * 2,
                max_keepalive_connections=settings.scrape_max_concurrent,
            ),
            follow_redirects=True,
            http2=False,  # HTTP/1.1 is fine for matsne.gov.ge
        )
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _pick_ua(self) -> str:
        return random.choice(_USER_AGENTS)

    def _host(self, url: str) -> str:
        return urlparse(url).hostname or "unknown"

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Send a GET request with rate limiting and retry.

        Raises ``httpx.HTTPStatusError`` for 4xx/5xx after all retries.
        """
        if self._client is None:
            raise RuntimeError("SessionManager must be used as async context manager")

        host = self._host(url)
        merged_headers = {
            "User-Agent": self._pick_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ka,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            **(headers or {}),
        }

        await self.rate_limiter.acquire(host)

        try:
            response = await self._get_with_retry(
                url, params=params, headers=merged_headers,
            )
            self.rate_limiter.report_success(host)
            return response
        except (httpx.HTTPError, RetryError):
            self.rate_limiter.report_error(host)
            raise

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def _get_with_retry(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Inner GET with tenacity retry decoration."""
        assert self._client is not None
        logger.debug("GET %s", url)
        response = await self._client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response

    async def download_bytes(self, url: str) -> bytes:
        """Download a binary resource (PDF, DOCX, etc.)."""
        response = await self.get(url)
        return response.content
