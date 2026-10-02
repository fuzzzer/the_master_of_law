"""The codes list links every code to its matsne page.

QA, 2026-10-01: `GET /laws/codes` returned `source_url: ""` for every code —
the browser's index lists chunk ids only, and the link was hard-coded empty.
"""

from unittest.mock import MagicMock, patch

from app.services.law_browser_service import LawBrowserService

LABOUR = "საქართველოს შრომის კოდექსი"


def test_every_code_carries_its_matsne_link():
    svc = LawBrowserService(chroma=MagicMock())
    svc._load_code_index = MagicMock(return_value={LABOUR: ["labour_code.article_1.chunk_0"]})
    store = MagicMock()
    store.list_codes.return_value = [{
        "document_id": "labour_code", "code_name": LABOUR,
        "source_url": "https://matsne.gov.ge/ka/document/view/1155567", "article_count": 90,
    }]

    with patch("app.services.law_browser_service.get_article_store_service", return_value=store):
        codes = svc.list_codes()

    assert codes[0]["source_url"] == "https://matsne.gov.ge/ka/document/view/1155567"


def test_a_search_lists_each_article_once():
    """QA, 2026-10-01: "სამსახურიდან გათავისუფლება" showed Labour Code
    art. 47 five times in the top six — one row per chunk."""
    def chunk(article, n, distance):
        return {"chunk_id": f"labour_code.article_{article}.chunk_{n}", "distance": distance,
                "metadata": {"code_name": LABOUR, "article_number": f"მუხლი {article}"}}

    chroma = MagicMock()
    chroma.vector_search.return_value = [
        chunk(47, 0, 0.1), chunk(47, 1, 0.11), chunk(47, 2, 0.12), chunk(48, 0, 0.2),
        chunk(47, 3, 0.21), chunk(37, 0, 0.3),
    ]
    svc = LawBrowserService(chroma=chroma)

    with patch("app.services.law_browser_service.get_embedding_client"):
        hits = svc.search("სამსახურიდან გათავისუფლება", top_k=3)

    assert [h["metadata"]["article_number"] for h in hits] == ["მუხლი 47", "მუხლი 48", "მუხლი 37"]
    assert hits[0]["chunk_id"].endswith("chunk_0"), "the best-matching chunk stands for the article"
