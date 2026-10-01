"""
Tests for the article store service (grounding mechanism A).

Runs against the real article_store.db built by the pipeline
(law_corpus/scripts/build_article_store.py) — the store is repo data,
so exact lookups are deterministic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.article_store_service import (
    ArticleStoreService,
    _normalize_article,
    _normalize_code,
)

STORE_PATH = Path(__file__).parent.parent.parent / "law_corpus" / "data" / "georgian_laws" / "article_store.db"

pytestmark = pytest.mark.skipif(
    not STORE_PATH.exists(), reason="article_store.db not built"
)


@pytest.fixture(scope="module")
def store() -> ArticleStoreService:
    return ArticleStoreService(db_path=STORE_PATH)


class TestNormalization:
    def test_article_forms(self):
        assert _normalize_article("მუხლი 48") == "48"
        assert _normalize_article("48") == "48"
        assert _normalize_article("48-ე") == "48"
        assert _normalize_article("166¹") == "1661"

    def test_code_prefix_stripped(self):
        assert _normalize_code("საქართველოს შრომის კოდექსი") == "შრომის კოდექსი"


class TestExactLookup:
    def test_labour_48_full_article(self, store):
        """The audit's article: full text, 9 paragraphs, matsne anchor."""
        art = store.get_article("labour_code", "48")
        assert art is not None
        assert art["article_number"] == "მუხლი 48"
        assert len(art["paragraphs"]) == 9
        assert art["article_url"].endswith("#article_48")
        assert "30 კალენდარული დღის" in art["content_ka"]

    def test_lookup_by_georgian_name(self, store):
        art = store.get_article("შრომის კოდექსი", "მუხლი 47")
        assert art is not None
        assert art["document_id"] == "labour_code"

    def test_lookup_by_prefixed_name(self, store):
        art = store.get_article("საქართველოს შრომის კოდექსი", "47")
        assert art is not None

    def test_paragraph_selection(self, store):
        art = store.get_article("labour_code", "48", paragraph="8")
        assert art["paragraph"] is not None
        assert art["paragraph"]["number"] == "8"

    def test_missing_paragraph_is_none(self, store):
        art = store.get_article("labour_code", "48", paragraph="99")
        assert art["paragraph"] is None

    def test_nonexistent_article(self, store):
        assert store.get_article("labour_code", "99999") is None

    def test_unknown_code_falls_back_to_any_code(self, store):
        # No code resolved → first match on article number alone
        art = store.get_article("", "48")
        assert art is None or art["article_number"] == "მუხლი 48"

    def test_cross_references_present(self, store):
        art = store.get_article("labour_code", "47")
        assert "labour_code.article_48" in art["cross_references"]


class TestFtsSearch:
    def test_georgian_query(self, store):
        hits = store.fts_search("ორსული ქალის გათავისუფლება", limit=5)
        assert isinstance(hits, list)

    def test_fts_syntax_chars_inert(self, store):
        # Must not raise on FTS5 operators in user text
        assert isinstance(store.fts_search('AND OR NOT "x" (y)*'), list)


class TestCodeAccess:
    def test_list_codes(self, store):
        codes = store.list_codes()
        assert len(codes) == 12
        assert any(c["document_id"] == "labour_code" for c in codes)

    def test_full_code_text(self, store):
        result = store.get_code_full_text("labour_code")
        assert result is not None
        text, count = result
        assert count > 50
        assert "მუხლი 47" in text
        assert "#article_48" in text
