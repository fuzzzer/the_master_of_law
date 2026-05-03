"""
Abstract base scraper — shared interface for all source-specific scrapers.
"""

from __future__ import annotations

import abc

from pipeline.models.scrape_result import ScrapeResult
from pipeline.scraper.session_manager import SessionManager


class BaseScraper(abc.ABC):
    """Interface that every source-specific scraper must implement."""

    def __init__(self, session: SessionManager) -> None:
        self.session = session

    @abc.abstractmethod
    async def discover_laws(self, priority: str | None = None) -> list[dict]:
        """
        Return a list of dicts describing laws to scrape.

        Each dict must contain at least ``url`` and ``document_id``.
        """
        ...

    @abc.abstractmethod
    async def scrape_document(self, url: str, document_id: str) -> ScrapeResult:
        """Download and return a single document."""
        ...

    @abc.abstractmethod
    async def scrape_all(
        self,
        priorities: list[str] | None = None,
    ) -> list[ScrapeResult]:
        """Run the full discovery + download loop."""
        ...
