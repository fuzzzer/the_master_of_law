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
