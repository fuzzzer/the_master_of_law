"""
Tests for the Citation Service.

Verifies:
- Georgian law citation extraction (მუხლი N pattern)
- Code name detection from context
- Citation verification against retrieved corpus chunks
- Deduplication of extracted citations
"""

from __future__ import annotations

import pytest

# We need sys.path for imports since tests run from backend/
import sys

sys.path.insert(0, ".")

from app.services.citation_service import CitationService


class TestCitationExtraction:
    """Tests for CitationService.extract_citations()."""

    def setup_method(self):
        self.svc = CitationService(chroma=None)

    def test_extract_single_article(self):
        text = "სისხლის სამართლის კოდექსი, მუხლი 120 ადგენს..."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 120"
        assert citations[0]["code_name"] == "სისხლის სამართლის კოდექსი"

    def test_extract_multiple_articles(self):
        text = (
            "სისხლის სამართლის კოდექსი, მუხლი 11 განსაზღვრავს ასაკს. "
            "ასევე მუხლი 120 ეხება ჯანმრთელობის დაზიანებას."
        )
        citations = self.svc.extract_citations(text)
        assert len(citations) == 2

    def test_extract_with_constitution(self):
        text = "კონსტიტუცია, მუხლი 42 იცავს..."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["code_name"] == "კონსტიტუცია"

    def test_extract_labor_code(self):
        text = "შრომის კოდექსი, მუხლი 37 ადგენს..."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["code_name"] == "შრომის კოდექსი"

    def test_deduplicate_same_article(self):
        text = (
            "სისხლის სამართლის კოდექსი, მუხლი 120 ერთხელ. "
            "სისხლის სამართლის კოდექსი, მუხლი 120 მეორეჯერ."
        )
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1

    def test_no_citations_in_plain_text(self):
        text = "This is plain text with no Georgian law references."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 0

    def test_article_without_code_name(self):
        text = "მუხლი 55 არის მნიშვნელოვანი."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        # Should have "Unknown" since no code name precedes it
        assert (
            citations[0]["code_name"] is None or citations[0]["code_name"] == "Unknown"
        )

    def test_multiple_codes_same_text(self):
        text = (
            "სისხლის სამართლის კოდექსი, მუხლი 11 და "
            "სამოქალაქო კოდექსი, მუხლი 992 ერთად."
        )
        citations = self.svc.extract_citations(text)
        assert len(citations) == 2
        codes = {c["code_name"] for c in citations}
        assert "სისხლის სამართლის კოდექსი" in codes
        assert "სამოქალაქო კოდექსი" in codes


class TestCitationVerification:
    """Tests for CitationService.verify_citations()."""

    def setup_method(self):
        self.svc = CitationService(chroma=None)

    def test_verify_found_citation(self, mock_chunks):
        citations = [
            {
                "article_number": "მუხლი 120",
                "code_name": "სისხლის სამართლის კოდექსი",
                "raw_text": "სისხლის სამართლის კოდექსი, მუხლი 120",
            }
        ]
        verified = self.svc.verify_citations(citations, mock_chunks)
        assert len(verified) == 1
        assert verified[0]["verified"] is True
        assert verified[0]["article_url"] != ""

    def test_verify_not_found_citation(self, mock_chunks):
        citations = [
            {
                "article_number": "მუხლი 999",
                "code_name": "სისხლის სამართლის კოდექსი",
                "raw_text": "სისხლის სამართლის კოდექსი, მუხლი 999",
            }
        ]
        verified = self.svc.verify_citations(citations, mock_chunks)
        assert len(verified) == 1
        assert verified[0]["verified"] is False

    def test_verify_mixed_citations(self, mock_chunks):
        citations = [
            {
                "article_number": "მუხლი 11",
                "code_name": "სისხლის სამართლის კოდექსი",
                "raw_text": "test",
            },
            {
                "article_number": "მუხლი 999",
                "code_name": "Unknown",
                "raw_text": "test",
            },
        ]
        verified = self.svc.verify_citations(citations, mock_chunks)
        assert len(verified) == 2
        verified_count = sum(1 for v in verified if v["verified"])
        assert verified_count == 1

    def test_verify_empty_citations(self, mock_chunks):
        verified = self.svc.verify_citations([], mock_chunks)
        assert len(verified) == 0

    def test_verify_empty_chunks(self):
        citations = [
            {"article_number": "მუხლი 11", "code_name": "test", "raw_text": "test"}
        ]
        verified = self.svc.verify_citations(citations, [])
        assert len(verified) == 1
        assert verified[0]["verified"] is False
