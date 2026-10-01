"""
Tests for legal analysis service — LawContextFormatter, prompt building.

Tests formatting for all source types, system prompt injection,
and user prompt construction.
"""

from __future__ import annotations

import pytest

from app.services.legal_analysis_service import (
    LawContextFormatter,
    ConversationHistoryFormatter,
    LegalAnalysisService,
    _RAG_INSTRUCTIONS,
    _THRESHOLD_INSTRUCTIONS,
)
from app.prompts import PromptTemplate, PromptRole


# ── LawContextFormatter tests ────────────────────────────────

class TestLawContextFormatterEmpty:
    """Test formatting when no chunks provided."""

    def test_empty_chunks(self):
        result = LawContextFormatter.format([])
        assert result == "No relevant legal context was found."


class TestLawContextFormatterLaws:
    """Test formatting for georgian_laws chunks."""

    def test_law_chunks_format(self, sample_law_chunks):
        result = LawContextFormatter.format(sample_law_chunks)
        assert "RELEVANT GEORGIAN LAW ARTICLES" in result
        assert "სისხლის სამართლის კოდექსი" in result
        assert "მუხლი 1" in result

    def test_law_chunk_has_citation(self, sample_law_chunks):
        result = LawContextFormatter.format(sample_law_chunks)
        assert "Citation:" in result

    def test_law_chunk_has_url(self, sample_law_chunks):
        result = LawContextFormatter.format(sample_law_chunks)
        assert "URL:" in result


class TestLawContextFormatterCourt:
    """Test formatting for court_practice chunks."""

    def test_court_chunks_format(self, sample_court_chunks):
        result = LawContextFormatter.format(sample_court_chunks)
        assert "COURT PRACTICE" in result
        assert "ბს-245-1(კ-24)" in result
        assert "criminal" in result
        assert "2023" in result


class TestLawContextFormatterGrandChamber:
    """Test formatting for grand_chamber chunks."""

    def test_grand_chamber_format(self, sample_grand_chamber_chunks):
        result = LawContextFormatter.format(sample_grand_chamber_chunks)
        assert "GRAND CHAMBER" in result
        assert "GC-2023-001" in result
        assert "Norm interpreted" in result
        assert "Binding rule" in result


class TestLawContextFormatterMixed:
    """Test formatting with mixed sources."""

    def test_mixed_sources(self, sample_law_chunks, sample_court_chunks, sample_grand_chamber_chunks):
        all_chunks = sample_law_chunks + sample_court_chunks + sample_grand_chamber_chunks
        result = LawContextFormatter.format(all_chunks)
        assert "RELEVANT GEORGIAN LAW ARTICLES" in result
        assert "COURT PRACTICE" in result
        assert "GRAND CHAMBER" in result


class TestGetSourceTypes:
    """Test source type extraction."""

    def test_law_only(self, sample_law_chunks):
        sources = LawContextFormatter.get_source_types(sample_law_chunks)
        assert sources == {"georgian_laws"}

    def test_mixed(self, sample_law_chunks, sample_court_chunks):
        sources = LawContextFormatter.get_source_types(sample_law_chunks + sample_court_chunks)
        assert "georgian_laws" in sources
        assert "court_practice" in sources

    def test_empty(self):
        sources = LawContextFormatter.get_source_types([])
        assert sources == set()


# ── ConversationHistoryFormatter tests ───────────────────────

class TestConversationHistoryFormatter:
    """History formatting tests."""

    def test_empty_history(self):
        result = ConversationHistoryFormatter.format([])
        assert result == ""

    def test_format_history(self, sample_history):
        result = ConversationHistoryFormatter.format(sample_history)
        assert "CONVERSATION HISTORY" in result
        assert "USER:" in result
        assert "ASSISTANT:" in result

    def test_max_turns(self, sample_history):
        result = ConversationHistoryFormatter.format(sample_history, max_turns=2)
        # Should only have last 2 messages
        assert "მუხლი 177" in result  # Last user message


# ── System prompt building tests ─────────────────────────────

class TestBuildSystemPrompt:
    """System prompt building with source-specific injection."""

    def setup_method(self):
        self.svc = LegalAnalysisService.__new__(LegalAnalysisService)
        self.svc._gemini = None
        self.svc._law_formatter = LawContextFormatter()
        self.svc._history_formatter = ConversationHistoryFormatter()
        self.base_template = PromptTemplate(
            name="test",
            role=PromptRole.SYSTEM,
            template="Base system prompt.",
        )

    def test_laws_only_unchanged(self, sample_law_chunks):
        """Laws-only chunks should not inject extra instructions."""
        result = self.svc._build_system_prompt(sample_law_chunks, self.base_template)
        assert result == "Base system prompt."

    def test_with_court_practice(self, sample_court_chunks):
        """Court practice chunks should inject court instructions."""
        result = self.svc._build_system_prompt(sample_court_chunks, self.base_template)
        assert "SOURCE-SPECIFIC INSTRUCTIONS" in result
        assert "სასამართლო პრაქტიკა" in result

    def test_with_grand_chamber(self, sample_grand_chamber_chunks):
        """Grand chamber chunks should inject GC instructions."""
        result = self.svc._build_system_prompt(sample_grand_chamber_chunks, self.base_template)
        assert "SOURCE-SPECIFIC INSTRUCTIONS" in result
        assert "დიდი პალატა" in result

    def test_with_thresholds(self, sample_threshold_chunks):
        """Threshold chunks should inject threshold instructions."""
        result = self.svc._build_system_prompt(sample_threshold_chunks, self.base_template)
        assert "იურიდიული ზღვრები" in result


# ── User prompt building tests ───────────────────────────────

class TestBuildUserPrompt:
    """User prompt construction tests."""

    def setup_method(self):
        self.svc = LegalAnalysisService.__new__(LegalAnalysisService)
        self.svc._gemini = None
        self.svc._law_formatter = LawContextFormatter()
        self.svc._history_formatter = ConversationHistoryFormatter()

    def test_full_params(self, sample_law_chunks, sample_history):
        """Full prompt with all parameters."""
        status = {"phase": "ANALYSIS", "message_count": 5}
        result = self.svc._build_user_prompt(
            "my question", sample_law_chunks, sample_history,
            case_context="Case context here", conversation_status=status,
        )
        assert "SYSTEM METADATA" in result
        assert "CURRENT CASE CONTEXT" in result
        assert "RELEVANT GEORGIAN LAW ARTICLES" in result
        assert "CONVERSATION HISTORY" in result
        assert "my question" in result

    def test_minimal_params(self, sample_law_chunks):
        """Minimal prompt with just message + chunks."""
        result = self.svc._build_user_prompt(
            "my question", sample_law_chunks, None,
        )
        assert "my question" in result
        assert "RELEVANT GEORGIAN LAW ARTICLES" in result
        assert "SYSTEM METADATA" not in result
        assert "CASE CONTEXT" not in result
