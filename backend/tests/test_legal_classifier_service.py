"""
Tests for the Legal Classifier Service.

Verifies:
- Keyword-based heuristic classification
- Domain detection for Georgian legal terms
- Fallback behavior when Gemini is unavailable
- All 9 legal domains are recognized
"""

from __future__ import annotations

import sys
sys.path.insert(0, ".")

import pytest

from app.services.legal_classifier_service import (
    LEGAL_DOMAINS,
    LegalClassifierService,
)


class TestHeuristicClassification:
    """Tests for the keyword-based fallback classifier."""

    def setup_method(self):
        self.svc = LegalClassifierService(gemini_client=None)

    def test_criminal_keywords(self):
        result = self.svc._heuristic_classify("მეზობელმა ცემა მოახდინა პოლიცია გამოიძახეს")
        assert result["primary"] == "criminal"

    def test_labor_keywords(self):
        result = self.svc._heuristic_classify("დამსაქმებელი სამსახურიდან დათხოვნა ხელფასი")
        assert result["primary"] == "labor"

    def test_family_keywords(self):
        result = self.svc._heuristic_classify("განქორწინება შვილი ალიმენტი")
        assert result["primary"] == "family"

    def test_civil_keywords(self):
        result = self.svc._heuristic_classify("ხელშეკრულება ვალი ანაზღაურება")
        assert result["primary"] == "civil"

    def test_tax_keywords(self):
        result = self.svc._heuristic_classify("გადასახადი საგადასახადო დეკლარაცია")
        assert result["primary"] == "tax"

    def test_administrative_keywords(self):
        result = self.svc._heuristic_classify("ჯარიმა ნებართვა ადმინისტრაციული")
        assert result["primary"] == "administrative"

    def test_land_keywords(self):
        result = self.svc._heuristic_classify("მიწა ნაკვეთი მეზობელი საზღვარი")
        assert result["primary"] == "land"

    def test_fallback_to_civil(self):
        result = self.svc._heuristic_classify("something completely unrelated in English")
        assert result["primary"] == "civil"
        assert result["confidence"] == 0.1

    def test_result_includes_georgian_name(self):
        result = self.svc._heuristic_classify("ცემა დანაშაული")
        assert "primary_ka" in result
        assert result["primary_ka"] != ""

    def test_secondary_domains_detected(self):
        # Text with both criminal and civil keywords
        result = self.svc._heuristic_classify("ცემა ზიანი ანაზღაურება დანაშაული")
        assert len(result.get("secondary", [])) >= 1


class TestLegalDomains:
    """Tests for domain definitions."""

    def test_all_domains_have_georgian_names(self):
        assert len(LEGAL_DOMAINS) == 9
        for key, value in LEGAL_DOMAINS.items():
            assert isinstance(value, str)
            assert len(value) > 0

    def test_required_domains_exist(self):
        required = ["criminal", "civil", "labor", "family", "tax", "administrative"]
        for domain in required:
            assert domain in LEGAL_DOMAINS
