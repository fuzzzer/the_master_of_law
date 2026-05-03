"""
matsne.gov.ge — Georgian Legislative Herald scraper.

Primary data source for consolidated Georgian legal texts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from pipeline.config import settings
from pipeline.models.scrape_result import ContentFormat, ScrapeResult
from pipeline.scraper.base_scraper import BaseScraper
from pipeline.scraper.session_manager import SessionManager
from pipeline.utils.deduplicator import content_hash
from pipeline.utils.logger import get_logger
from pipeline.utils.progress_tracker import ProgressTracker

logger = get_logger(__name__)

BASE_URL = "https://matsne.gov.ge"

SEED_LAWS: list[dict[str, Any]] = [
    {"document_id": "constitution", "title_ka": "საქართველოს კონსტიტუცია", "title_en": "Constitution of Georgia", "url": "https://matsne.gov.ge/ka/document/view/30346", "priority": "P0", "document_type": "constitution"},
    {"document_id": "civil_code", "title_ka": "სამოქალაქო კოდექსი", "title_en": "Civil Code", "url": "https://matsne.gov.ge/ka/document/view/31702", "priority": "P0", "document_type": "code"},
    {"document_id": "criminal_code", "title_ka": "სისხლის სამართლის კოდექსი", "title_en": "Criminal Code", "url": "https://matsne.gov.ge/ka/document/view/16426", "priority": "P0", "document_type": "code"},
    {"document_id": "civil_procedure_code", "title_ka": "სამოქალაქო საპროცესო კოდექსი", "title_en": "Code of Civil Procedure", "url": "https://matsne.gov.ge/ka/document/view/29962", "priority": "P0", "document_type": "code"},
    {"document_id": "criminal_procedure_code", "title_ka": "სისხლის სამართლის საპროცესო კოდექსი", "title_en": "Code of Criminal Procedure", "url": "https://matsne.gov.ge/ka/document/view/90034", "priority": "P0", "document_type": "code"},
    {"document_id": "admin_offences_code", "title_ka": "ადმინისტრაციულ სამართალდარღვევათა კოდექსი", "title_en": "Administrative Offences Code", "url": "https://matsne.gov.ge/ka/document/view/28216", "priority": "P0", "document_type": "code"},
    {"document_id": "general_admin_code", "title_ka": "ზოგადი ადმინისტრაციული კოდექსი", "title_en": "General Administrative Code", "url": "https://matsne.gov.ge/ka/document/view/16270", "priority": "P0", "document_type": "code"},
    {"document_id": "admin_procedure_code", "title_ka": "ადმინისტრაციული საპროცესო კოდექსი", "title_en": "Administrative Procedure Code", "url": "https://matsne.gov.ge/ka/document/view/16492", "priority": "P0", "document_type": "code"},
    {"document_id": "tax_code", "title_ka": "საგადასახადო კოდექსი", "title_en": "Tax Code", "url": "https://matsne.gov.ge/ka/document/view/1043717", "priority": "P1", "document_type": "code"},
    {"document_id": "labour_code", "title_ka": "შრომის კოდექსი", "title_en": "Labour Code", "url": "https://matsne.gov.ge/ka/document/view/1155567", "priority": "P1", "document_type": "code"},
    {"document_id": "entrepreneurial_law", "title_ka": "მეწარმეთა შესახებ საქართველოს კანონი", "title_en": "Law on Entrepreneurs", "url": "https://matsne.gov.ge/ka/document/view/5765049", "priority": "P1", "document_type": "law"},
    {"document_id": "consumer_rights_law", "title_ka": "მომხმარებელთა უფლებების დაცვის შესახებ", "title_en": "Consumer Rights Law", "url": "https://matsne.gov.ge/ka/document/view/3484942", "priority": "P1", "document_type": "law"},
    {"document_id": "personal_data_law", "title_ka": "პერსონალურ მონაცემთა დაცვის შესახებ", "title_en": "Personal Data Protection Law", "url": "https://matsne.gov.ge/ka/document/view/1561437", "priority": "P2", "document_type": "law"},
    {"document_id": "election_code", "title_ka": "საარჩევნო კოდექსი", "title_en": "Election Code", "url": "https://matsne.gov.ge/ka/document/view/1557168", "priority": "P2", "document_type": "code"},
    {"document_id": "customs_code", "title_ka": "საბაჟო კოდექსი", "title_en": "Customs Code", "url": "https://matsne.gov.ge/ka/document/view/4596066", "priority": "P2", "document_type": "code"},
]


class MatsneScraper(BaseScraper):
    """Scraper for matsne.gov.ge with caching and resumable progress."""

    def __init__(self, session: SessionManager) -> None:
        super().__init__(session)
        self._cache_dir = settings.raw_html_dir
        self._metadata_dir = settings.raw_metadata_dir
        self._tracker = ProgressTracker("scraper")

    async def discover_laws(self, priority: str | None = None) -> list[dict]:
        laws = list(SEED_LAWS)
        if priority:
            laws = [l for l in laws if l.get("priority") == priority]
        logger.info("Discovered %d laws (priority=%s)", len(laws), priority)
        return laws

    async def scrape_document(self, url: str, document_id: str) -> ScrapeResult:
        cached = self._read_cache(document_id)
        if cached is not None:
            logger.info("Cache hit for %s", document_id)
            return cached

        consolidated_url = self._to_consolidated_url(url)
        response = await self.session.get(consolidated_url)
        raw_bytes = response.content
        encoding = response.encoding or "utf-8"
        text = raw_bytes.decode(encoding, errors="replace")
        soup = BeautifulSoup(text, "lxml")

        result = ScrapeResult(
            url=consolidated_url,
            document_id=document_id,
            content=raw_bytes,
            content_format=ContentFormat.HTML,
            encoding=encoding,
            http_status=response.status_code,
            headers=dict(response.headers),
            scraped_at=datetime.now(timezone.utc),
            content_hash=content_hash(text),
            cached=False,
            discovered_title=self._extract_title(soup),
            discovered_links=self._extract_links(soup, consolidated_url),
        )
        self._write_cache(document_id, result)
        return result

    async def scrape_all(self, priorities: list[str] | None = None) -> list[ScrapeResult]:
        laws = await self.discover_laws()
        if priorities:
            laws = [l for l in laws if l.get("priority") in priorities]

        results: list[ScrapeResult] = []
        for law in laws:
            doc_id = law["document_id"]
            if self._tracker.is_completed(doc_id):
                logger.info("Skipping %s (already completed)", doc_id)
                cached = self._read_cache(doc_id)
                if cached:
                    results.append(cached)
                continue
            try:
                result = await self.scrape_document(law["url"], doc_id)
                results.append(result)
                self._tracker.mark_completed(doc_id)
                self._save_law_metadata(law, result)
            except Exception as exc:
                logger.error("Failed to scrape %s: %s", doc_id, exc)
                self._tracker.mark_failed(doc_id, str(exc))
            self._tracker.save()

        logger.info("Scrape done: %d ok, %d failed", self._tracker.completed_count, self._tracker.failed_count)
        return results

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _to_consolidated_url(url: str) -> str:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return f"{base}?publication=0" if "?" not in url else url

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str | None:
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else None

    @staticmethod
    def _extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
        links = set()
        for a in soup.find_all("a", href=True):
            if "/document/view/" in a["href"]:
                links.add(urljoin(base_url, a["href"]))
        return list(links)[:50]

    def _cache_path(self, doc_id: str) -> Path:
        return self._cache_dir / f"{doc_id}.html"

    def _meta_path(self, doc_id: str) -> Path:
        return self._metadata_dir / f"{doc_id}.json"

    def _read_cache(self, doc_id: str) -> ScrapeResult | None:
        path = self._cache_path(doc_id)
        if not path.exists():
            return None
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        meta: dict = {}
        mp = self._meta_path(doc_id)
        if mp.exists():
            meta = json.loads(mp.read_text("utf-8"))
        return ScrapeResult(
            url=meta.get("url", ""), document_id=doc_id, content=raw,
            content_format=ContentFormat.HTML, encoding="utf-8", http_status=200,
            scraped_at=datetime.fromisoformat(meta["scraped_at"]) if "scraped_at" in meta else datetime.now(timezone.utc),
            content_hash=content_hash(text), cached=True, discovered_title=meta.get("title"),
        )

    def _write_cache(self, doc_id: str, result: ScrapeResult) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path(doc_id).write_bytes(result.content)
        self._meta_path(doc_id).write_text(json.dumps({
            "url": result.url, "document_id": doc_id, "title": result.discovered_title,
            "scraped_at": result.scraped_at.isoformat(), "content_hash": result.content_hash,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_law_metadata(self, law: dict, result: ScrapeResult) -> None:
        merged = {**law, "scraped_at": result.scraped_at.isoformat(), "content_hash": result.content_hash}
        (self._metadata_dir / f"{law['document_id']}.json").write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
