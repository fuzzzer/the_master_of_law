"""Tests for the parser module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.models.scrape_result import ContentFormat, ScrapeResult
from pipeline.parser.html_parser import HtmlLegalParser
from pipeline.parser.structure_extractor import StructureExtractor
from pipeline.parser.metadata_extractor import MetadataExtractor
from pipeline.utils.georgian_text import (
    contains_georgian,
    extract_article_references,
    normalise_superscripts,
)


class TestGeorgianText:
    """Test Georgian text utilities."""

    def test_contains_georgian(self) -> None:
        assert contains_georgian("მუხლი 1")
        assert not contains_georgian("Article 1")

    def test_normalise_superscripts(self) -> None:
        assert normalise_superscripts("45¹") == "45-1"
        assert normalise_superscripts("100²³") == "100-23"
        assert normalise_superscripts("99") == "99"

    def test_extract_article_references(self) -> None:
        text = "მუხლი 123-ის შესაბამისად და მუხლი 45"
        refs = extract_article_references(text)
        assert "123" in refs
        assert "45" in refs


class TestStructureExtractor:
    """Test structure extraction from Georgian legal text."""

    def test_extract_articles(self) -> None:
        text = """
        თავი I - ძირითადი დებულებები

        მუხლი 1. პირველი მუხლი
        ეს არის პირველი მუხლის ტექსტი.
        1. პირველი პუნქტი.
        2. მეორე პუნქტი.

        მუხლი 2. მეორე მუხლი
        ეს არის მეორე მუხლის ტექსტი.
        """
        extractor = StructureExtractor()
        nodes = extractor.extract(text)
        articles = extractor.flatten_articles(nodes)

        assert len(articles) >= 2
        assert articles[0]["number"] == "1"
        assert articles[1]["number"] == "2"
        assert "ძირითადი დებულებები" in (articles[0].get("chapter") or "")

    def test_extract_with_books(self) -> None:
        text = """
        წიგნი I - ზოგადი დებულებები

        თავი I - პრინციპები

        მუხლი 1. ტესტი
        ტესტის ტექსტი.
        """
        extractor = StructureExtractor()
        nodes = extractor.extract(text)
        articles = extractor.flatten_articles(nodes)

        assert len(articles) >= 1
        assert articles[0].get("book") is not None


class TestMetadataExtractor:
    """Test metadata extraction from HTML."""

    def test_extract_from_sample_html(self, sample_html: str) -> None:
        extractor = MetadataExtractor()
        meta = extractor.extract(sample_html, "civil_code", {
            "title_ka": "სამოქალაქო კოდექსი",
            "title_en": "Civil Code",
            "document_type": "code",
        })
        assert meta.document_id == "civil_code"
        assert "კოდექსი" in meta.title_ka or "სამოქალაქო" in meta.title_ka
        assert meta.document_type.value in ("code", "law")


class TestHtmlParser:
    """Test the full HTML parser on sample data."""

    def test_parse_sample_html(self, sample_html_bytes: bytes) -> None:
        result = ScrapeResult(
            url="https://matsne.gov.ge/ka/document/view/31702",
            document_id="civil_code",
            content=sample_html_bytes,
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="test",
        )
        parser = HtmlLegalParser()
        doc = parser.parse(result, {
            "title_ka": "სამოქალაქო კოდექსი",
            "title_en": "Civil Code",
            "document_type": "code",
            "url": "https://matsne.gov.ge/ka/document/view/31702",
        })

        assert doc.document_id == "civil_code"
        assert doc.article_count >= 3
        # Check that articles contain Georgian text
        for article in doc.articles:
            assert contains_georgian(article.content_ka)

    def test_cross_reference_extraction(self, sample_html_bytes: bytes) -> None:
        result = ScrapeResult(
            url="https://matsne.gov.ge/ka/document/view/31702",
            document_id="civil_code",
            content=sample_html_bytes,
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="test",
        )
        parser = HtmlLegalParser()
        doc = parser.parse(result, {"document_type": "code", "title_ka": "test"})

        # Article 8 references Article 123
        article_8 = [a for a in doc.articles if "8" in a.article_number]
        if article_8:
            assert any("123" in ref for ref in article_8[0].cross_references)
