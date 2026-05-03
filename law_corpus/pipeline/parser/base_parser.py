"""Abstract base parser for legal documents."""

from __future__ import annotations

import abc

from pipeline.models.legal_document import LegalDocument
from pipeline.models.scrape_result import ScrapeResult


class BaseParser(abc.ABC):
    """Interface for all format-specific legal document parsers."""

    @abc.abstractmethod
    def parse(self, result: ScrapeResult) -> LegalDocument:
        """Parse a scrape result into a structured legal document."""
        ...

    @abc.abstractmethod
    def can_parse(self, result: ScrapeResult) -> bool:
        """Return True if this parser can handle the given format."""
        ...
