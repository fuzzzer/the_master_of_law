"""
Article numbers as matsne writes them, and the version in force today.

Found 2026-10-02: 52¹ was stored as "521" and collided with real articles —
get_article(civil_code, 491) returned 49¹, chosen by a tie-break on the
length of its id. A superscript article is now "52-1" in the store and
"მუხლი 52¹" on screen; an article matsne prints in two versions keeps both,
the later one dated in its id ("article_61@2026-09-01").
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.config.settings import settings
from app.services.article_store_service import ArticleStoreService, _in_force, _normalize_article


@pytest.mark.parametrize("written, stored", [
    ("მუხლი 48", "48"), ("48", "48"), ("48-ე", "48"), ("მუხლი 48-ის", "48"),
    ("52¹", "52-1"), ("მუხლი 52¹", "52-1"), ("52¹-ე", "52-1"), ("52-1", "52-1"),
    ("181⁷", "181-7"), ("21³¹", "21-31"), ("491", "491"),
])
def test_every_way_an_article_number_is_written_finds_the_same_article(written, stored):
    assert _normalize_article(written) == stored


def _row(article_id):
    return {"article_id": article_id}


def test_the_version_in_force_today_is_chosen():
    rows = [_row("admin.article_61"), _row("admin.article_61@2026-09-01")]
    assert _in_force(rows, date(2026, 10, 2))["article_id"].endswith("@2026-09-01")
    assert _in_force(rows, date(2026, 8, 31))["article_id"].endswith("article_61")


def test_a_version_not_yet_in_force_is_used_only_when_there_is_nothing_else():
    rows = [_row("admin.article_159-5"), _row("admin.article_159-5@2027-01-01")]
    assert _in_force(rows, date(2026, 10, 2))["article_id"].endswith("article_159-5")
    assert _in_force([rows[1]], date(2026, 10, 2))["article_id"].endswith("@2027-01-01")


STORE = Path(settings.chroma_persist_dir).parent / "georgian_laws" / "article_store.db"
rebuilt = pytest.mark.skipif(
    not STORE.exists() or not ArticleStoreService(db_path=STORE).get_article("civil_code", "49¹"),
    reason="needs the article store rebuilt with superscript numbers",
)


@rebuilt
def test_civil_code_491_is_article_491_and_49_1_is_49_1():
    store = ArticleStoreService(db_path=STORE)
    assert store.get_article("civil_code", "491")["article_number"] == "მუხლი 491"
    assert store.get_article("civil_code", "49¹")["article_title"].startswith("ერთობლივი საინვესტიციო")


@rebuilt
def test_an_article_link_opens_the_article_on_matsne():
    store = ArticleStoreService(db_path=STORE)
    assert store.get_article("labour_code", "48")["article_url"].endswith("#part_174")
