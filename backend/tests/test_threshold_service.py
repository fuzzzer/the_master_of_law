"""
Tests for threshold-related functionality:
- Threshold data format validation
- RAG pipeline threshold boost heuristic
- Threshold chunk detection in system prompt
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

import pytest

from app.services.rag_retrieval_service import RAGRetrievalService
from app.services.legal_analysis_service import LegalAnalysisService


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

    def test_all_entries_have_unique_ids(self):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        ids = [e["id"] for e in data["thresholds"]]
        assert len(ids) == len(set(ids)), "Duplicate IDs in threshold catalog"


class TestThresholdBoost:
    def _make_rag_service(self):
        return RAGRetrievalService(chroma=None, embedding_client=None, gemini_client=None)

    def test_query_with_numbers_triggers_boost(self):
        svc = self._make_rag_service()
        assert svc._query_involves_thresholds("70 გრამი მარიხუანა")
        assert svc._query_involves_thresholds("2 წელი ვადა")

    def test_query_with_keywords_triggers_boost(self):
        svc = self._make_rag_service()
        assert svc._query_involves_thresholds("რამდენი გრამი ითვლება დიდ ოდენობად")
        assert svc._query_involves_thresholds("ჯარიმა რამდენია")
        assert svc._query_involves_thresholds("სასჯელი რა ვადაა")

    def test_generic_query_no_boost(self):
        svc = self._make_rag_service()
        assert not svc._query_involves_thresholds("რა უფლებები მაქვს")
        assert not svc._query_involves_thresholds("ადვოკატი მჭირდება")

    def test_boost_reduces_threshold_distance(self):
        svc = self._make_rag_service()
        chunks = [
            {"chunk_id": "law_1", "content": "law text", "metadata": {}, "distance": 0.3},
            {"chunk_id": "threshold_1", "content": "threshold text",
             "metadata": {"chunk_type": "threshold"}, "distance": 0.3},
        ]
        boosted = svc._boost_threshold_chunks("70 გრამი", chunks)
        threshold_chunk = next(c for c in boosted if c["chunk_id"] == "threshold_1")
        law_chunk = next(c for c in boosted if c["chunk_id"] == "law_1")
        assert threshold_chunk["distance"] < law_chunk["distance"]
        assert threshold_chunk["distance"] == pytest.approx(0.2, rel=0.01)

    def test_no_boost_without_threshold_query(self):
        svc = self._make_rag_service()
        chunks = [
            {"chunk_id": "threshold_1", "content": "threshold text",
             "metadata": {"chunk_type": "threshold"}, "distance": 0.3},
        ]
        result = svc._boost_threshold_chunks("რა უფლებები მაქვს", chunks)
        assert result[0]["distance"] == 0.3


class TestThresholdSystemPrompt:
    def test_threshold_instructions_appended_when_present(self):
        svc = LegalAnalysisService(gemini_client=None)
        chunks = [
            {"chunk_id": "t1", "content": "data",
             "metadata": {"_collection": "georgian_laws", "chunk_type": "threshold"}},
        ]
        prompt = svc._build_system_prompt(chunks)
        assert "იურიდიული ზღვრები" in prompt
        assert "EXACT values" in prompt

    def test_no_threshold_instructions_without_threshold_chunks(self):
        svc = LegalAnalysisService(gemini_client=None)
        chunks = [
            {"chunk_id": "l1", "content": "law data",
             "metadata": {"_collection": "georgian_laws"}},
        ]
        prompt = svc._build_system_prompt(chunks)
        assert "იურიდიული ზღვრები" not in prompt
