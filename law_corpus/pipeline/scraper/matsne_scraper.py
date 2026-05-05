"""
matsne.gov.ge — Georgian Legislative Herald scraper.

Primary data source for consolidated Georgian legal texts.

IMPORTANT — matsne.gov.ge URL versioning:
  - No ``?publication=`` param  → latest consolidated version (საბოლოო)
  - ``?publication=0``          → ORIGINAL text as first enacted (პირველადი სახე)
  - ``?publication=N`` (N > 0)  → specific consolidated revision

We ALWAYS want the latest consolidated version, so we must NOT append
``?publication=0`` and instead strip any existing publication parameter.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

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

# Label that matsne.gov.ge shows on the latest consolidated version page.
CONSOLIDATED_LABEL = "კონსოლიდირებული ვერსია (საბოლოო)"
# Label for the original (initial) version — we must NEVER have this.
ORIGINAL_LABEL = "პირველადი სახე"

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


class ConsolidatedVersionError(Exception):
    """Raised when scraped HTML does not contain the consolidated version."""
    pass


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
            # Validate that the cached version is actually consolidated.
            cached_text = cached.content.decode("utf-8", errors="replace")
            if self._is_consolidated(cached_text):
                logger.info("Cache hit for %s (consolidated ✓)", document_id)
                return cached
            else:
                logger.warning(
                    "Cache for %s contains NON-consolidated version — re-scraping!",
                    document_id,
                )
                # Delete stale cache so we fetch fresh
                self._cache_path(document_id).unlink(missing_ok=True)

        consolidated_url = self._to_consolidated_url(url)
        logger.info("Scraping consolidated version: %s", consolidated_url)
        response = await self.session.get(consolidated_url)
        raw_bytes = response.content
        encoding = response.encoding or "utf-8"
        text = raw_bytes.decode(encoding, errors="replace")
        soup = BeautifulSoup(text, "lxml")

        # ── Verify we got the consolidated version ───────────
        version_label = self._detect_version_label(text)
        if not self._is_consolidated(text):
            raise ConsolidatedVersionError(
                f"Scraped {document_id} but got version '{version_label}' "
                f"instead of '{CONSOLIDATED_LABEL}'. URL: {consolidated_url}"
            )
        logger.info(
            "Verified %s: %s", document_id, version_label or "consolidated ✓",
        )

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
                    # Re-validate even completed items
                    cached_text = cached.content.decode("utf-8", errors="replace")
                    if not self._is_consolidated(cached_text):
                        logger.warning(
                            "Completed %s has non-consolidated cache — re-scraping!",
                            doc_id,
                        )
                        self._tracker.mark_pending(doc_id)
                        self._cache_path(doc_id).unlink(missing_ok=True)
                    else:
                        results.append(cached)
                        continue
                else:
                    continue
            try:
                result = await self.scrape_document(law["url"], doc_id)
                results.append(result)
                self._tracker.mark_completed(doc_id)
                self._save_law_metadata(law, result)
            except ConsolidatedVersionError as exc:
                logger.error("Version error for %s: %s", doc_id, exc)
                self._tracker.mark_failed(doc_id, str(exc))
            except Exception as exc:
                logger.error("Failed to scrape %s: %s", doc_id, exc)
                self._tracker.mark_failed(doc_id, str(exc))
            self._tracker.save()

        logger.info("Scrape done: %d ok, %d failed", self._tracker.completed_count, self._tracker.failed_count)
        return results

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _to_consolidated_url(url: str) -> str:
        """
        Return URL that fetches the **latest consolidated version**.

        On matsne.gov.ge:
        - No ``?publication=`` → latest consolidated version (საბოლოო)
        - ``?publication=0``   → ORIGINAL version (პირველადი სახე) ← WRONG!
        - ``?publication=N``   → specific historical revision

        We strip any ``publication`` parameter so the server returns the
        latest consolidated version by default.
        """
        parsed = urlparse(url)
        # Remove the 'publication' parameter if present
        if parsed.query:
            params = parse_qs(parsed.query)
            params.pop("publication", None)
            new_query = urlencode(params, doseq=True)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}" + (
                f"?{new_query}" if new_query else ""
            )
        # Base URL without query params — already returns consolidated
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    @staticmethod
    def _is_consolidated(html_text: str) -> bool:
        """Check if the HTML page contains the consolidated version label."""
        # If it has the "final consolidated" label, it's correct.
        if CONSOLIDATED_LABEL in html_text:
            return True
        # If it has the "original version" label, it's definitely wrong.
        if ORIGINAL_LABEL in html_text:
            return False
        # Some documents may only have a single version (no amendments),
        # in which case neither label appears. That's acceptable.
        return True

    @staticmethod
    def _detect_version_label(html_text: str) -> str | None:
        """Extract the version label from the HTML for logging."""
        if CONSOLIDATED_LABEL in html_text:
            return CONSOLIDATED_LABEL
        # Try to find "პირველადი სახე (DATE - DATE)" pattern
        match = re.search(r"პირველადი სახე\s*\([^)]+\)", html_text)
        if match:
            return match.group(0)
        return None

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
            "version": "consolidated_final",
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_law_metadata(self, law: dict, result: ScrapeResult) -> None:
        merged = {
            **law,
            "scraped_at": result.scraped_at.isoformat(),
            "content_hash": result.content_hash,
            "version": "consolidated_final",
        }
        (self._metadata_dir / f"{law['document_id']}.json").write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
