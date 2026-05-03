"""
parliament.ge scraper — secondary source for Georgian legislation.

This is a lightweight complement to the matsne.gov.ge scraper.
"""

from __future__ import annotations

from pipeline.models.scrape_result import ScrapeResult
from pipeline.scraper.base_scraper import BaseScraper
from pipeline.scraper.session_manager import SessionManager
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class ParliamentScraper(BaseScraper):
    """Minimal scraper for parliament.ge — reserved for future use."""

    def __init__(self, session: SessionManager) -> None:
        super().__init__(session)

    async def discover_laws(self, priority: str | None = None) -> list[dict]:
        logger.info("ParliamentScraper.discover_laws is not yet implemented")
        return []

    async def scrape_document(self, url: str, document_id: str) -> ScrapeResult:
        raise NotImplementedError("ParliamentScraper is reserved for future implementation")

    async def scrape_all(self, priorities: list[str] | None = None) -> list[ScrapeResult]:
        logger.info("ParliamentScraper.scrape_all is not yet implemented")
        return []
