"""
Every article the threshold catalog cites exists in the article store.

Found 2026-10-02: the criminal appeal deadline was "20 days" from article
405 of the REPLACED Criminal Procedure Code (matsne 16428); the code in the
corpus (90034) gives one month (art. 293(1)), cassation one month (art.
302(1)), and no limit for newly discovered circumstances (art. 311). Four
entries also carried flattened numbers (2051 for 205¹).
"""

import json
from pathlib import Path

import pytest

from app.config.settings import settings
from app.services.article_store_service import ArticleStoreService

CATALOG = Path(__file__).parents[2] / "law_corpus" / "data" / "thresholds" / "threshold_catalog.json"
STORE = Path(settings.chroma_persist_dir).parent / "georgian_laws" / "article_store.db"


@pytest.mark.skipif(
    not STORE.exists() or not ArticleStoreService(db_path=STORE).get_article("civil_code", "49¹"),
    reason="needs the article store rebuilt with superscript numbers",
)
def test_every_cited_article_exists_in_the_code_it_names():
    store = ArticleStoreService(db_path=STORE)
    missing = [
        (e["id"], e["code_name"], e["article_number"])
        for e in json.loads(CATALOG.read_text(encoding="utf-8"))["thresholds"]
        if e["article_number"].startswith("მუხლი")
        and store.get_article(e["code_name"], e["article_number"]) is None
    ]
    assert not missing, missing


def test_the_criminal_appeal_deadline_is_the_current_codes():
    entry = next(e for e in json.loads(CATALOG.read_text(encoding="utf-8"))["thresholds"]
                 if e["id"] == "criminal_appeal_deadline")
    assert entry["article_number"] == "მუხლი 293"
    assert "90034" in entry["source_url"]
    assert entry["values"]["standard_appeal"].startswith("1 თვე")
