"""
Key validation for both Google key kinds, and the free law search without a key.

The bugs this pins (2026-10-24/25): the company's Google Cloud key was refused
outright, the validate check would call models.list — which Vertex refuses for
API keys — and the free law search on the open-access server returned zero
results for anyone without a key, because it needed a model call to embed the
query.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.request_context import reset_byok_key, set_byok_key
from app.services.article_store_service import ArticleStoreService
from app.services.law_browser_service import LawBrowserService

CLOUD_KEY = "AQ.Ab8RN6" + "x" * 40
STUDIO_KEY = "AIza" + "A" * 35


# ── /api-keys/validate ───────────────────────────────────────

def _validate(key, client):
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.middleware import byok_middleware

    st = byok_middleware.settings
    before = (st.byok_required, st.auth_enabled)
    st.byok_required, st.auth_enabled = True, False
    try:
        with patch("app.integrations.vertex_ai_client.create_genai_client", return_value=client):
            return TestClient(create_app()).get(
                "/api/v1/api-keys/validate", headers={"X-API-Key": key},
            )
    finally:
        st.byok_required, st.auth_enabled = before


def test_a_cloud_key_is_validated_with_a_free_token_count():
    client = MagicMock()
    client.aio.models.count_tokens = AsyncMock(return_value=MagicMock(total_tokens=1))
    client.aio.models.list = AsyncMock(side_effect=AssertionError("Vertex refuses list for keys"))

    r = _validate(CLOUD_KEY, client)

    assert r.status_code == 200 and r.json()["valid"] is True
    client.aio.models.count_tokens.assert_awaited_once()


def test_a_rejected_cloud_key_says_the_key_does_not_work():
    client = MagicMock()
    client.aio.models.count_tokens = AsyncMock(side_effect=RuntimeError(
        "ClientError: 401 UNAUTHENTICATED. API key not valid. Please pass a valid API key."
    ))

    r = _validate(CLOUD_KEY, client)

    assert r.status_code == 401
    assert r.json()["error"] == "byok_key_invalid"
    assert "არ მუშაობს" in r.json()["message"]
    assert "Vertex AI" in r.json()["message"]


def test_an_ai_studio_key_is_still_validated_by_listing_models():
    async def models():
        yield "m1"
        yield "m2"

    client = MagicMock()
    client.aio.models.list = AsyncMock(return_value=models())

    r = _validate(STUDIO_KEY, client)

    assert r.json() == {"valid": True, "models_available": 2}


# ── free law search ──────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    db = tmp_path / "article_store.db"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE codes (document_id TEXT PRIMARY KEY, code_name TEXT NOT NULL, title_en TEXT,
            document_number TEXT, source_url TEXT NOT NULL, article_count INTEGER NOT NULL);
        CREATE TABLE articles (article_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, code_name TEXT NOT NULL,
            article_number TEXT NOT NULL, article_norm TEXT NOT NULL, article_title TEXT, book TEXT, part TEXT,
            chapter TEXT, content_ka TEXT NOT NULL, paragraphs_json TEXT NOT NULL, cross_references_json TEXT NOT NULL,
            article_url TEXT NOT NULL, is_repealed INTEGER NOT NULL DEFAULT 0, effective_date TEXT);
        CREATE VIRTUAL TABLE articles_fts USING fts5(article_id UNINDEXED, code_name, article_number,
            article_title, content_ka);
    """)
    rows = [
        ("labour_code", "საქართველოს შრომის კოდექსი", "labour_code.article_47", "მუხლი 47",
         "შრომითი ხელშეკრულების შეწყვეტა", "დამსაქმებელი ვალდებულია შრომითი ხელშეკრულების შეწყვეტისას..."),
        ("civil_code", "საქართველოს სამოქალაქო კოდექსი", "civil_code.article_1158", "მუხლი 1158",
         "მეუღლეთა თანასაკუთრება", "ქორწინების განმავლობაში შეძენილი ქონება მეუღლეთა თანასაკუთრებაა."),
    ]
    for doc, name, aid, num, title, text in rows:
        conn.execute("INSERT OR IGNORE INTO codes VALUES (?,?,?,?,?,?)", (doc, name, "", "", "https://matsne.gov.ge", 1))
        conn.execute("INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (aid, doc, name, num, num.split()[-1], title, "", "", "", text, "[]", "[]",
                      f"https://matsne.gov.ge/x#article_{num.split()[-1]}", 0, None))
        conn.execute("INSERT INTO articles_fts VALUES (?,?,?,?,?)", (aid, name, num, title, text))
    conn.commit()
    conn.close()
    return ArticleStoreService(db_path=db)


def test_keyword_search_matches_inflected_georgian_words(store):
    hits = store.keyword_search("ხელშეკრულებით რა ხდება შეწყვეტის დროს")
    assert [h["article_id"] for h in hits] == ["labour_code.article_47"]


def test_keyword_search_filters_by_code(store):
    assert store.keyword_search("ქონება ხელშეკრულება", code="სამოქალაქო კოდექსი")[0]["code_name"] \
        == "საქართველოს სამოქალაქო კოდექსი"


def test_keyword_search_keeps_fts_syntax_inert(store):
    assert isinstance(store.keyword_search('AND OR NOT "x" (y)*'), list)


def test_free_search_without_a_key_uses_keyword_search(store):
    svc = LawBrowserService(chroma=MagicMock())
    with patch("app.services.law_browser_service.settings") as st, \
         patch("app.services.article_store_service.get_article_store_service", return_value=store), \
         patch("app.services.law_browser_service.get_embedding_client") as embed:
        st.byok_required = True
        results = svc.search("ქორწინების დროს შეძენილი ქონება")
    embed.assert_not_called()
    assert results[0]["chunk_id"] == "civil_code.article_1158"
    assert results[0]["metadata"]["article_url"].endswith("#article_1158")
    assert results[0]["metadata"]["search"] == "keyword"


def test_free_search_falls_back_when_vector_search_fails(store):
    svc = LawBrowserService(chroma=MagicMock())
    token = set_byok_key(STUDIO_KEY)
    try:
        with patch("app.services.article_store_service.get_article_store_service", return_value=store), \
             patch("app.services.law_browser_service.get_embedding_client") as embed:
            embed.return_value.embed_query.side_effect = RuntimeError("401 UNAUTHENTICATED")
            results = svc.search("შრომითი ხელშეკრულების შეწყვეტა")
    finally:
        reset_byok_key(token)
    assert results[0]["chunk_id"] == "labour_code.article_47"


def test_vector_results_are_used_when_available():
    chroma = MagicMock()
    chroma.vector_search.return_value = [{"chunk_id": "v1", "content": "x", "metadata": {}}]
    svc = LawBrowserService(chroma=chroma)
    token = set_byok_key(STUDIO_KEY)
    try:
        with patch("app.services.law_browser_service.get_embedding_client") as embed:
            embed.return_value.embed_query.return_value = [0.0] * 768
            assert svc.search("ქონება")[0]["chunk_id"] == "v1"
    finally:
        reset_byok_key(token)
