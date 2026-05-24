"""
Citation extraction tests with realistic Georgian legal text.

Tests CitationService against the kind of text Gemini actually produces,
not trivial mock strings. Verifies extraction, deduplication, code name
detection, and verification logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.citation_service import (
    ARTICLE_PATTERN,
    CitationService,
    _normalize_code_name,
)


# ── Realistic AI-generated Georgian legal text samples ───────

# Simulates a Gemini response about theft
THEFT_RESPONSE = (
    "საქართველოს სისხლის სამართლის კოდექსის მუხლი 177 განსაზღვრავს "
    "ქურდობას, როგორც სხვისი მოძრავი ნივთის ფარული დაუფლება "
    "მართლსაწინააღმდეგო მისაკუთრების მიზნით. პირველი ნაწილის მიხედვით "
    "ისჯება ჯარიმით ან შინაპატიმრობით ვადით ერთიდან სამ წლამდე. "
    "ასევე იხილეთ მუხლი 178, რომელიც ძარცვას ეხება."
)

# Response with mixed codes
MIXED_CODES_RESPONSE = (
    "საქართველოს სისხლის სამართლის კოდექსის მუხლი 126 ითვალისწინებს "
    "ოჯახში ძალადობას. საქართველოს სამოქალაქო კოდექსის მუხლი 1407 "
    "განსაზღვრავს ზიანის ანაზღაურების წესს. ასევე, საქართველოს "
    "სისხლის სამართლის საპროცესო კოდექსის მუხლი 72 არეგულირებს "
    "დამცველის მონაწილეობას საქმის წარმოებაში."
)

# Response with short-form code name (common Gemini output)
SHORT_FORM_RESPONSE = (
    "სისხლის სამართლის კოდექსის მუხლი 108 ადგენს პასუხისმგებლობას "
    "განზრახ მკვლელობისთვის. ამ შემთხვევაში ასევე შესაძლოა გამოიყენოს "
    "სისხლის სამართლის კოდექსის მუხლი 109, რომელიც დამამძიმებელ "
    "გარემოებებში ჩადენილ მკვლელობას ეხება."
)

# Response with duplicate citations
DUPLICATE_RESPONSE = (
    "საქართველოს სისხლის სამართლის კოდექსის მუხლი 177 ადგენს, რომ "
    "ქურდობა ისჯება. როგორც მუხლი 177 განსაზღვრავს, პირველი ნაწილი "
    "ითვალისწინებს ჯარიმას. მუხლი 177-ის მე-2 ნაწილი კი ამძიმებს სასჯელს."
)

# Greeting with no citations
GREETING_RESPONSE = "გამარჯობა! როგორ შემიძლია დაგეხმაროთ იურიდიულ საკითხებში?"

# Response mentioning narcotics law
NARCOTICS_RESPONSE = (
    "ნარკოტიკული საშუალებების შესახებ კანონის დანართი №2 განსაზღვრავს "
    "ნივთიერებათა ნუსხას. სისხლის სამართლის კოდექსის მუხლი 260 "
    "ადგენს პასუხისმგებლობას ნარკოტიკული საშუალების უკანონო "
    "შეძენა-შენახვისთვის."
)


# ── Extraction Tests ─────────────────────────────────────────

class TestArticlePatternRegex:
    """Test the raw regex pattern against Georgian text."""

    def test_finds_simple_article_reference(self):
        matches = ARTICLE_PATTERN.findall("მუხლი 177")
        assert matches == ["177"]

    def test_finds_multiple_articles(self):
        matches = ARTICLE_PATTERN.findall("მუხლი 177 და მუხლი 178")
        assert matches == ["177", "178"]

    def test_handles_large_article_numbers(self):
        matches = ARTICLE_PATTERN.findall("მუხლი 1407 ადგენს")
        assert matches == ["1407"]

    def test_no_match_in_plain_text(self):
        matches = ARTICLE_PATTERN.findall("ეს არის უბრალო ტექსტი")
        assert matches == []

    def test_handles_article_with_superscript_ref(self):
        """Text like 'მუხლი 260' should match even with surrounding text."""
        matches = ARTICLE_PATTERN.findall("კოდექსის მუხლი 260 ადგენს")
        assert matches == ["260"]


class TestExtractCitations:
    """Test CitationService.extract_citations with realistic text."""

    def setup_method(self):
        self.svc = CitationService(chroma=MagicMock())

    def test_single_article_from_theft_response(self):
        """Should extract მუხლი 177 and მუხლი 178 from theft response."""
        citations = self.svc.extract_citations(THEFT_RESPONSE)
        article_numbers = {c["article_number"] for c in citations}
        assert "მუხლი 177" in article_numbers
        assert "მუხლი 178" in article_numbers

    def test_code_name_detected_for_theft(self):
        """Should detect 'საქართველოს სისხლის სამართლის კოდექსი' as code name."""
        citations = self.svc.extract_citations(THEFT_RESPONSE)
        theft_citation = next(c for c in citations if c["article_number"] == "მუხლი 177")
        assert "სისხლის სამართლის კოდექსი" in theft_citation["code_name"]

    def test_mixed_codes_extracts_all(self):
        """Should extract articles from criminal, civil, and procedural codes."""
        citations = self.svc.extract_citations(MIXED_CODES_RESPONSE)
        article_numbers = {c["article_number"] for c in citations}
        assert "მუხლი 126" in article_numbers   # Criminal
        assert "მუხლი 1407" in article_numbers   # Civil
        assert "მუხლი 72" in article_numbers     # Procedural

    def test_mixed_codes_correct_code_names(self):
        """Each article should be associated with its correct code."""
        citations = self.svc.extract_citations(MIXED_CODES_RESPONSE)
        for c in citations:
            if c["article_number"] == "მუხლი 126":
                assert "სისხლის სამართლის კოდექსი" in c["code_name"]
            elif c["article_number"] == "მუხლი 1407":
                assert "სამოქალაქო კოდექსი" in c["code_name"]
            elif c["article_number"] == "მუხლი 72":
                assert "საპროცესო" in c["code_name"]

    def test_deduplication_same_article_mentioned_thrice(self):
        """მუხლი 177 mentioned 3 times should produce 1 citation."""
        citations = self.svc.extract_citations(DUPLICATE_RESPONSE)
        count_177 = sum(1 for c in citations if c["article_number"] == "მუხლი 177")
        assert count_177 == 1, f"Expected 1, got {count_177} (dedup failed)"

    def test_greeting_produces_no_citations(self):
        """Greeting text should produce empty list."""
        citations = self.svc.extract_citations(GREETING_RESPONSE)
        assert citations == []

    def test_short_form_code_name_still_detected(self):
        """Short form 'სისხლის სამართლის კოდექსის' should be recognized."""
        citations = self.svc.extract_citations(SHORT_FORM_RESPONSE)
        assert len(citations) >= 2
        for c in citations:
            assert c["code_name"] != "Unknown", f"Code name not detected for {c['article_number']}"

    def test_narcotics_law_code_name(self):
        """Narcotics law should be detected as code name."""
        citations = self.svc.extract_citations(NARCOTICS_RESPONSE)
        art_260 = next((c for c in citations if c["article_number"] == "მუხლი 260"), None)
        assert art_260 is not None
        assert "სისხლის სამართლის კოდექსი" in art_260["code_name"]


# ── Code Name Normalization ──────────────────────────────────

class TestCodeNameNormalization:
    """Test _normalize_code_name strips 'საქართველოს' prefix."""

    def test_strips_prefix(self):
        result = _normalize_code_name("საქართველოს სისხლის სამართლის კოდექსი")
        assert result == "სისხლის სამართლის კოდექსი"

    def test_no_prefix_unchanged(self):
        result = _normalize_code_name("სისხლის სამართლის კოდექსი")
        assert result == "სისხლის სამართლის კოდექსი"

    def test_narcotics_law_unchanged(self):
        """Narcotics law doesn't have საქართველოს prefix."""
        result = _normalize_code_name("ნარკოტიკული საშუალებების შესახებ კანონი")
        assert result == "ნარკოტიკული საშუალებების შესახებ კანონი"

    def test_empty_string(self):
        result = _normalize_code_name("")
        assert result == ""


# ── Verification Tests ───────────────────────────────────────

class TestVerifyCitations:
    """Test verify_citations against corpus chunks."""

    def setup_method(self):
        self.svc = CitationService(chroma=MagicMock())

    def _make_chunk(self, code_name: str, article_number: str, content: str = "Law text") -> dict:
        return {
            "chunk_id": f"test_{article_number}",
            "content": content,
            "metadata": {
                "code_name": code_name,
                "article_number": article_number,
                "article_url": f"https://matsne.gov.ge/test#{article_number}",
                "source_url": "https://matsne.gov.ge/test",
                "citation_text": f"{code_name}, {article_number}",
            },
        }

    def test_verified_when_in_chunks(self):
        """Citation found in retrieved chunks → verified: True."""
        chunks = [self._make_chunk("საქართველოს სისხლის სამართლის კოდექსი", "მუხლი 177")]
        citations = [{"article_number": "მუხლი 177", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"}]
        result = self.svc.verify_citations(citations, chunks)
        assert result[0]["verified"] is True
        assert "matsne.gov.ge" in result[0]["article_url"]

    def test_unverified_when_not_in_chunks(self):
        """Citation NOT in chunks → verified: False."""
        chunks = [self._make_chunk("საქართველოს სისხლის სამართლის კოდექსი", "მუხლი 177")]
        citations = [{"article_number": "მუხლი 999", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"}]
        result = self.svc.verify_citations(citations, chunks)
        assert result[0]["verified"] is False

    def test_short_form_matches_full_form_in_corpus(self):
        """Short-form code name should match full-form in chunks (normalization)."""
        chunks = [self._make_chunk("საქართველოს სისხლის სამართლის კოდექსი", "მუხლი 108")]
        citations = [{"article_number": "მუხლი 108", "code_name": "სისხლის სამართლის კოდექსი", "raw_text": "test"}]
        result = self.svc.verify_citations(citations, chunks)
        assert result[0]["verified"] is True, "Short-form code name didn't match full-form in corpus"

    def test_full_form_matches_short_form_in_corpus(self):
        """Full-form citation should match short-form in chunks (reverse normalization)."""
        # This simulates the 20 chunks stored with short-form code names
        chunks = [self._make_chunk("სისხლის სამართლის კოდექსი", "მუხლი 108")]
        citations = [{"article_number": "მუხლი 108", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"}]
        result = self.svc.verify_citations(citations, chunks)
        assert result[0]["verified"] is True, "Full-form citation didn't match short-form chunk"

    def test_multiple_citations_partial_match(self):
        """2 citations, 1 in chunks → 1 verified, 1 not."""
        chunks = [self._make_chunk("საქართველოს სისხლის სამართლის კოდექსი", "მუხლი 177")]
        citations = [
            {"article_number": "მუხლი 177", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"},
            {"article_number": "მუხლი 999", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"},
        ]
        result = self.svc.verify_citations(citations, chunks)
        verified = [r for r in result if r["verified"]]
        unverified = [r for r in result if not r["verified"]]
        assert len(verified) == 1
        assert len(unverified) == 1

    def test_empty_chunks_all_unverified(self):
        """No chunks → all citations unverified."""
        citations = [{"article_number": "მუხლი 177", "code_name": "test", "raw_text": "test"}]
        result = self.svc.verify_citations(citations, [])
        assert result[0]["verified"] is False


# ── Corpus Verification Tests ────────────────────────────────

class TestVerifyAgainstCorpus:
    """Test verify_against_corpus classification logic."""

    def setup_method(self):
        mock_chroma = MagicMock()
        # Default: corpus search returns nothing
        mock_chroma.search_by_metadata = MagicMock(return_value=[])
        self.svc = CitationService(chroma=mock_chroma)

    def test_verified_in_chunks(self):
        """Citation in retrieved chunks → 'verified' bucket."""
        chunks = [{
            "chunk_id": "c1",
            "content": "ქურდობა, ესე იგი...",
            "metadata": {
                "code_name": "საქართველოს სისხლის სამართლის კოდექსი",
                "article_number": "მუხლი 177",
                "article_url": "https://matsne.gov.ge/test",
                "citation_text": "სსკ, მუხლი 177",
            },
        }]
        citations = [{"article_number": "მუხლი 177", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"}]
        result = self.svc.verify_against_corpus(citations, chunks)
        assert len(result["verified"]) == 1
        assert len(result["not_found"]) == 0
        assert len(result["corpus_found"]) == 0

    def test_not_in_chunks_but_found_in_corpus(self):
        """Citation not in chunks but found via metadata search → 'corpus_found'."""
        corpus_hit = {
            "chunk_id": "c_corpus",
            "content": "found via search",
            "metadata": {
                "code_name": "საქართველოს სისხლის სამართლის კოდექსი",
                "article_number": "მუხლი 300",
                "article_url": "https://matsne.gov.ge/300",
            },
        }
        self.svc._chroma.search_by_metadata = MagicMock(return_value=[corpus_hit])

        citations = [{"article_number": "მუხლი 300", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"}]
        result = self.svc.verify_against_corpus(citations, [])
        assert len(result["corpus_found"]) == 1
        assert len(result["not_found"]) == 0

    def test_hallucinated_article(self):
        """Citation not in chunks and not in corpus → 'not_found'."""
        citations = [{"article_number": "მუხლი 99999", "code_name": "საქართველოს სისხლის სამართლის კოდექსი", "raw_text": "test"}]
        result = self.svc.verify_against_corpus(citations, [])
        assert len(result["not_found"]) == 1
        assert result["not_found"][0]["verified"] is False
