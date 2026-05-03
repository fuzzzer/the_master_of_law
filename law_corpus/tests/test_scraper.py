"""Tests for the scraper module."""

from __future__ import annotations

import pytest

from pipeline.scraper.matsne_scraper import SEED_LAWS, MatsneScraper
from pipeline.scraper.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test the adaptive rate limiter."""

    @pytest.mark.asyncio
    async def test_basic_acquire(self) -> None:
        limiter = RateLimiter(min_delay=0.01, max_delay=1.0)
        await limiter.acquire("test.com")
        # Should complete without error

    @pytest.mark.asyncio
    async def test_backoff_increases(self) -> None:
        limiter = RateLimiter(min_delay=0.01, max_delay=1.0, backoff_factor=2.0)
        assert limiter._current_delay["test.com"] == 0.01
        limiter.report_error("test.com")
        assert limiter._current_delay["test.com"] == 0.02
        limiter.report_error("test.com")
        assert limiter._current_delay["test.com"] == 0.04

    @pytest.mark.asyncio
    async def test_success_resets_delay(self) -> None:
        limiter = RateLimiter(min_delay=0.01, max_delay=1.0)
        limiter.report_error("test.com")
        limiter.report_error("test.com")
        limiter.report_success("test.com")
        assert limiter._current_delay["test.com"] == 0.01

    @pytest.mark.asyncio
    async def test_max_delay_cap(self) -> None:
        limiter = RateLimiter(min_delay=0.01, max_delay=0.1, backoff_factor=10.0)
        limiter.report_error("test.com")
        limiter.report_error("test.com")
        limiter.report_error("test.com")
        assert limiter._current_delay["test.com"] <= 0.1


class TestSeedLaws:
    """Verify the seed law list is properly configured."""

    def test_seed_laws_not_empty(self) -> None:
        assert len(SEED_LAWS) >= 10

    def test_p0_laws_present(self) -> None:
        p0 = [l for l in SEED_LAWS if l["priority"] == "P0"]
        assert len(p0) >= 8  # Constitution + 7 codes

    def test_all_seeds_have_required_fields(self) -> None:
        for law in SEED_LAWS:
            assert "document_id" in law
            assert "url" in law
            assert "title_ka" in law
            assert "priority" in law
            assert law["url"].startswith("https://matsne.gov.ge")

    def test_unique_document_ids(self) -> None:
        ids = [l["document_id"] for l in SEED_LAWS]
        assert len(ids) == len(set(ids)), "Duplicate document IDs in seed data"
