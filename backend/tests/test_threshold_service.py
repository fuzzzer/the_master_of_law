"""
Tests for threshold-related functionality:
- Threshold data format validation
- Threshold service exact search lookup
- Threshold chunk detection in system prompt
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

import pytest

from app.services.threshold_service import ThresholdService
from app.services.legal_analysis_service import LegalAnalysisService
from app.prompts.legal_analysis import LEGAL_ANALYSIS_SYSTEM


CATALOG_PATH = Path(__file__).parent.parent.parent / "law_corpus" / "data" / "thresholds" / "threshold_catalog.json"


class TestThresholdCatalog:
    def test_catalog_exists(self):
        assert CATALOG_PATH.exists(), f"Threshold catalog not found at {CATALOG_PATH}"

    def test_catalog_has_entries(self):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["thresholds"]) >= 20

    def test_entry_schema(self):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        required_keys = {"id", "type", "code_name", "article_number", "threshold_type",
                         "description_ka", "values", "consequence_ka", "source_url",
                         "last_verified"}
        for entry in data["thresholds"]:
            missing = required_keys - set(entry.keys())
            assert not missing, f"Entry {entry.get('id', '?')} missing keys: {missing}"
            assert entry["type"] == "legal_threshold"
            assert isinstance(entry["values"], dict)
            assert len(entry["values"]) > 0


class TestThresholdServiceSearch:
    def test_search_matches_substance(self):
        svc = ThresholdService()
        res = svc.search("კანაფის ფისი")
        assert len(res) > 0
        assert "კანაფის ფისი" in res[0]["content"]

    def test_search_empty_or_generic_query(self):
        svc = ThresholdService()
        assert len(svc.search("")) == 0
        assert len(svc.search("ადვოკატი მჭირდება")) == 0


class TestThresholdSystemPrompt:
    def test_threshold_instructions_appended_when_present(self):
        svc = LegalAnalysisService(gemini_client=None)
        chunks = [
            {"chunk_id": "t1", "content": "data",
             "metadata": {"_collection": "georgian_laws", "chunk_type": "threshold"}},
        ]
        prompt = svc._build_system_prompt(chunks, LEGAL_ANALYSIS_SYSTEM)
        assert "იურიდიული ზღვრები" in prompt
        assert "EXACT values" in prompt

    def test_no_threshold_instructions_without_threshold_chunks(self):
        svc = LegalAnalysisService(gemini_client=None)
        chunks = [
            {"chunk_id": "l1", "content": "law data",
             "metadata": {"_collection": "georgian_laws"}},
        ]
        prompt = svc._build_system_prompt(chunks, LEGAL_ANALYSIS_SYSTEM)
        assert "იურიდიული ზღვრები" not in prompt

