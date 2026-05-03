"""
Extracts document-level metadata from scraped legal pages.

Works with both HTML pages and JSON metadata files.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from bs4 import BeautifulSoup

from pipeline.models.document_metadata import DocumentMetadata, LegalDocumentType
from pipeline.utils.georgian_text import normalise_georgian
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# Date patterns found on matsne.gov.ge
_DATE_PATTERNS = [
    re.compile(r"(\d{2})[./](\d{2})[./](\d{4})"),   # DD/MM/YYYY or DD.MM.YYYY
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),          # YYYY-MM-DD
]

_DOC_TYPE_MAP: dict[str, LegalDocumentType] = {
    "კონსტიტუცია": LegalDocumentType.CONSTITUTION,
    "ორგანული კანონი": LegalDocumentType.ORGANIC_LAW,
    "კოდექსი": LegalDocumentType.CODE,
    "კანონი": LegalDocumentType.LAW,
    "ბრძანებულება": LegalDocumentType.PRESIDENTIAL_DECREE,
    "დადგენილება": LegalDocumentType.GOVERNMENT_RESOLUTION,
}


class MetadataExtractor:
    """Extract document metadata from HTML content."""

    def extract(
        self,
        html: str,
        document_id: str,
        seed_meta: dict | None = None,
    ) -> DocumentMetadata:
        """
        Parse metadata from an HTML page.

        Parameters
        ----------
        html : str
            Raw HTML content of the law page.
        document_id : str
            Slug identifier for this document.
        seed_meta : dict, optional
            Pre-populated metadata from the seed list.
        """
        soup = BeautifulSoup(html, "lxml")
        seed = seed_meta or {}

        title_ka = self._extract_title(soup) or seed.get("title_ka", "")
        doc_type = self._detect_type(title_ka, seed.get("document_type", "other"))
        adoption_date = self._extract_date(soup, "adoption")
        effective_date = self._extract_date(soup, "effective")
        last_amendment = self._extract_date(soup, "amendment")

        return DocumentMetadata(
            document_id=document_id,
            title_ka=normalise_georgian(title_ka),
            title_en=seed.get("title_en"),
            document_type=doc_type,
            document_number=self._extract_doc_number(soup),
            adoption_date=adoption_date,
            effective_date=effective_date or adoption_date,
            last_amendment_date=last_amendment,
            issuing_body=self._extract_issuing_body(soup),
            legal_domain=seed.get("legal_domain", []),
            source_url=seed.get("url", ""),
            language="ka",
            version="consolidated",
            is_in_force=True,
        )

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
        return ""

    @staticmethod
    def _extract_doc_number(soup: BeautifulSoup) -> str:
        """Try to find the official document number."""
        for label in ("რეგისტრაცია", "ნომერი", "number"):
            el = soup.find(string=re.compile(label, re.IGNORECASE))
            if el and el.parent:
                sibling = el.parent.find_next_sibling()
                if sibling:
                    return sibling.get_text(strip=True)
        return ""

    @staticmethod
    def _extract_date(soup: BeautifulSoup, kind: str) -> Optional[date]:
        """Extract a date by looking for Georgian labels near date strings."""
        labels = {
            "adoption": ["მიღების თარიღი", "მიღებულია"],
            "effective": ["ამოქმედება", "ძალაში შესვლა"],
            "amendment": ["ბოლო ცვლილება", "ცვლილება"],
        }
        for label in labels.get(kind, []):
            el = soup.find(string=re.compile(label, re.IGNORECASE))
            if el:
                context = el.parent.get_text() if el.parent else str(el)
                for pat in _DATE_PATTERNS:
                    m = pat.search(context)
                    if m:
                        try:
                            groups = m.groups()
                            if len(groups[0]) == 4:
                                return date(int(groups[0]), int(groups[1]), int(groups[2]))
                            return date(int(groups[2]), int(groups[1]), int(groups[0]))
                        except (ValueError, IndexError):
                            continue
        return None

    @staticmethod
    def _detect_type(title: str, fallback: str) -> LegalDocumentType:
        title_lower = title.lower()
        for keyword, doc_type in _DOC_TYPE_MAP.items():
            if keyword in title_lower:
                return doc_type
        try:
            return LegalDocumentType(fallback)
        except ValueError:
            return LegalDocumentType.OTHER

    @staticmethod
    def _extract_issuing_body(soup: BeautifulSoup) -> str:
        for label in ("გამომცემელი", "ავტორი"):
            el = soup.find(string=re.compile(label, re.IGNORECASE))
            if el and el.parent:
                sibling = el.parent.find_next_sibling()
                if sibling:
                    return sibling.get_text(strip=True)
        return "საქართველოს პარლამენტი"
