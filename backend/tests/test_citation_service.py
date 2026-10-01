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


class TestGeorgianArticleForms:
    """Citation extraction across Georgian ordinal/superscript syntax (finding #9)."""

    def setup_method(self):
        self.svc = CitationService(chroma=None)

    def test_number_before_keyword(self):
        """'177-ე მუხლი' (ordinal, number first) → article 177."""
        text = "სისხლის სამართლის კოდექსი, 177-ე მუხლი ეხება ქურდობას."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 177"

    def test_plain_number_before_keyword(self):
        """'177 მუხლი' (number first, no ordinal) → article 177."""
        text = "სამოქალაქო კოდექსი, 177 მუხლი."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 177"

    def test_ordinal_suffix_after_keyword(self):
        """'მუხლი 177-ე' (keyword first, ordinal suffix) → article 177."""
        text = "სისხლის სამართლის კოდექსი, მუხლი 177-ე."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 177"

    def test_superscript_index_preserved(self):
        """'მუხლი 115¹' → article keeps the superscript (not truncated to 115)."""
        text = "სისხლის სამართლის კოდექსი, მუხლი 115¹ ეხება ოჯახურ ძალადობას."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 115¹"

    def test_abbreviation_with_ordinal(self):
        """'სსკ-ის 177-ე მუხლი' → resolves abbreviation + ordinal article."""
        text = "სსკ-ის 177-ე მუხლი ადგენს პასუხისმგებლობას."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 177"
        assert citations[0]["code_name"] == "საქართველოს სისხლის სამართლის კოდექსი"


class TestSubArticleExtraction:
    """Sub-article (paragraph) references must be captured (audit fix 0.5)."""

    def setup_method(self):
        self.svc = CitationService(chroma=None)

    def test_dot_form(self):
        """'მუხლი 48.8' → article 48, paragraph 8."""
        text = "შრომის კოდექსი, მუხლი 48.8 ითვალისწინებს კომპენსაციას."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 48"
        assert citations[0]["paragraph"] == "8"

    def test_me_natsili_form(self):
        """'48-ე მუხლის მე-8 ნაწილი' → article 48, paragraph 8."""
        text = "შრომის კოდექსის 48-ე მუხლის მე-8 ნაწილი ადგენს ვადას."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 48"
        assert citations[0]["paragraph"] == "8"

    def test_word_ordinal_natsili_form(self):
        """'48-ე მუხლის პირველი ნაწილი' → article 48, paragraph 1."""
        text = "შრომის კოდექსის 48-ე მუხლის პირველი ნაწილის თანახმად."
        citations = self.svc.extract_citations(text)
        assert len(citations) == 1
        assert citations[0]["article_number"] == "მუხლი 48"
        assert citations[0]["paragraph"] == "1"

    def test_plain_article_has_empty_paragraph(self):
        """'მუხლი 45' without sub-article → empty paragraph."""
        citations = self.svc.extract_citations("სამოქალაქო კოდექსი, მუხლი 45.")
        assert len(citations) == 1
        assert citations[0]["paragraph"] == ""

    def test_sentence_end_dot_not_a_paragraph(self):
        """'მუხლი 48. 1990 წელს' — sentence dot must not create a paragraph."""
        citations = self.svc.extract_citations("მუხლი 48. 1990 წელს მიღებული.")
        assert len(citations) == 1
        assert citations[0]["paragraph"] == ""

    def test_same_article_different_paragraphs_not_deduped(self):
        """48.1 and 48.8 are distinct citations."""
        text = "შრომის კოდექსი, მუხლი 48.1 და შრომის კოდექსი, მუხლი 48.8."
        citations = self.svc.extract_citations(text)
        assert [c["paragraph"] for c in citations] == ["1", "8"]


class TestOverlappingArticleRefs:
    """Same article number under two codes must map to the correct code (finding #7)."""

    def setup_method(self):
        self.svc = CitationService(chroma=None)

    def test_same_number_two_codes_resolved_independently(self):
        """Civil 177 and Criminal 177 must keep distinct, correct code names."""
        text = (
            "სამოქალაქო კოდექსი, მუხლი 177 ეხება საკუთრებას. "
            "ხოლო სისხლის სამართლის კოდექსი, მუხლი 177 ეხება ქურდობას."
        )
        citations = self.svc.extract_citations(text)
        assert len(citations) == 2
        by_code = {c["code_name"]: c["article_number"] for c in citations}
        assert by_code["სამოქალაქო კოდექსი"] == "მუხლი 177"
        assert by_code["სისხლის სამართლის კოდექსი"] == "მუხლი 177"


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
