"""Tests for the article store builder (scripts/build_article_store.py)."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "build_article_store", Path(__file__).resolve().parent.parent / "scripts" / "build_article_store.py"
)
build_article_store = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(build_article_store)


def _write_parsed(tmp_path: Path) -> Path:
    parsed = tmp_path / "parsed"
    parsed.mkdir()
    doc = {
        "metadata": {
            "document_id": "civil_procedure_code",
            "title_ka": "საქართველოს სამოქალაქო საპროცესო კოდექსი",
            "document_number": "1106",
            "source_url": "https://matsne.gov.ge/ka/document/view/29962",
            "publication_id": "178",
            "version_date": "2026-06-24",
            "scraped_at": "2026-10-25T00:47:16Z",
            "content_hash": "abc",
        },
        "articles": [
            {"article_id": "civil_procedure_code.chapter_XLV.article_369", "article_number": "მუხლი 369",
             "content_ka": "1. ვადაა 14 დღე.", "paragraphs": [{"number": "1", "text": "ვადაა 14 დღე.", "sub_points": []}],
             "matsne_anchor": "part_476", "in_force": True},
            {"article_id": "civil_procedure_code.chapter_XLV.article_372-1.pending", "article_number": "მუხლი 372¹",
             "content_ka": "1. ახალი წესი.", "paragraphs": [], "matsne_anchor": "part_482", "in_force": False},
        ],
    }
    (parsed / "civil_procedure_code.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return parsed


def test_store_carries_official_source_fields(tmp_path: Path) -> None:
    out = tmp_path / "article_store.db"
    build_article_store.build(_write_parsed(tmp_path), out)
    conn = sqlite3.connect(out)
    conn.row_factory = sqlite3.Row
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
    code = conn.execute("SELECT * FROM codes").fetchone()
    assert code["version_date"] == "2026-06-24"
    assert code["version_url"] == "https://matsne.gov.ge/ka/document/view/29962?publication=178"
    assert code["retrieved_at"] == "2026-10-25T00:47:16Z"
    art = conn.execute("SELECT * FROM articles WHERE article_norm = '369'").fetchone()
    assert art["official_url"] == "https://matsne.gov.ge/ka/document/view/29962#part_476"
    assert art["article_url"] == "https://matsne.gov.ge/ka/document/view/29962#article_369"
    assert art["in_force"] == 1 and art["version_date"] == "2026-06-24"


def test_future_wording_keeps_bare_norm_and_is_not_in_force(tmp_path: Path) -> None:
    out = tmp_path / "article_store.db"
    build_article_store.build(_write_parsed(tmp_path), out)
    row = sqlite3.connect(out).execute(
        "SELECT article_norm, in_force FROM articles WHERE article_id LIKE '%.pending'"
    ).fetchone()
    assert row == ("372-1", 0)
