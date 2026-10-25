"""Deterministic scorecard checks (eval/scorecard/checks.py) on recorded answer snippets. No keys, no network."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

SCORECARD = Path(__file__).resolve().parents[2] / "eval" / "scorecard"
sys.path.insert(0, str(SCORECARD))

from checks import run_checks, unsourced_practice  # noqa: E402

ARTICLES = [
    ("civil_procedure_code", "369", "სააპელაციო საჩივრის შეტანის ვადა", "1. სააპელაციო საჩივრის შეტანის ვადაა 14 დღე.\n2. ..."),
    ("civil_code", "129", "ხანდაზმულობის ვადები", "1. სახელშეკრულებო მოთხოვნების ხანდაზმულობის ვადა შეადგენს სამ წელს."),
    ("criminal_code", "1261", "ოჯახში ძალადობა", "1. ოჯახის ერთი წევრის მიერ ..."),
    ("labour_code", "48", "შრომითი ხელშეკრულების შეწყვეტის პროცედურა", "1. ...\n4. 30 კალენდარული დღის ვადაში ..."),
]


@pytest.fixture()
def store(tmp_path: Path) -> str:
    path = tmp_path / "article_store.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE articles (document_id TEXT, article_norm TEXT, article_title TEXT, content_ka TEXT, "
                 "article_url TEXT, is_repealed INTEGER)")
    conn.executemany("INSERT INTO articles VALUES (?,?,?,?,?,0)",
                     [(d, n, t, c, f"https://matsne.gov.ge/ka/document/view/{i}#article_{n}") for i, (d, n, t, c) in enumerate(ARTICLES)])
    conn.commit()
    conn.close()
    return str(path)


def answer(text: str, status: int = 200) -> dict:
    return {"status": status, "latency_s": 12.0, "degraded": False, "body": {"response": text}}


def test_missing_deadline_is_caught(store):
    rec = answer("სამოქალაქო საპროცესო კოდექსის 369-ე მუხლის თანახმად, ვადა მითითებულია გადაწყვეტილებაში, გადაამოწმეთ.")
    res = run_checks(rec, {"required_articles": [["civil_procedure_code:369"]], "required_numbers": ["14d"]}, store)
    assert res["required_articles_missing"] == []
    assert res["required_numbers_missing"] == ["14d"]


def test_correct_deadline_passes(store):
    rec = answer("სამოქალაქო საპროცესო კოდექსის 369-ე მუხლის მიხედვით, სააპელაციო საჩივარი 14 დღეში უნდა შეიტანოთ.")
    res = run_checks(rec, {"required_articles": [["civil_procedure_code:369"]], "required_numbers": ["14d"]}, store)
    assert res["required_numbers_missing"] == [] and not res["empty_or_broken"]


def test_invented_article_is_flagged(store):
    rec = answer("სამოქალაქო კოდექსის 9999-ე მუხლი გიცავთ ამ შემთხვევაში და ეს საკმარისია.")
    assert run_checks(rec, {}, store)["invented_articles"] == ["civil_code:9999"]


def test_superscript_article_is_normalised(store):
    rec = answer("სისხლის სამართლის კოდექსის 126¹ მუხლი ოჯახში ძალადობას ეხება, ეს მნიშვნელოვანი განსხვავებაა.")
    res = run_checks(rec, {"required_articles": [["criminal_code:1261"]]}, store)
    assert res["required_articles_missing"] == []
    assert res["citations"][0]["superscript"] is True


def test_unsourced_court_practice_is_flagged_but_named_case_is_not():
    bad = "საქართველოს უზენაესი სასამართლოს დამკვიდრებული განმარტებით, პროკურატურაში საჩივარი ვადას არ წყვეტს."
    good = "უზენაესი სასამართლოს განმარტებით (საქმე №ას-1042-2023), ვადა წყდება."
    quote = "საჩივარი დასაშვებია, თუ ხელს შეუწყობს ერთგვაროვანი სასამართლო პრაქტიკის ჩამოყალიბებას."
    assert len(unsourced_practice(bad)) == 1
    assert unsourced_practice(good) == []
    assert unsourced_practice(quote) == []


def test_empty_and_error_answers_are_broken(store):
    assert run_checks(answer(""), {}, store)["empty_or_broken"]
    assert run_checks(answer("კარგი პასუხი, მაგრამ შეცდომით დაბრუნდა სერვერიდან ამჯერად.", status=500), {}, store)["empty_or_broken"]


def test_refusal_and_labour_only_trap(store):
    refusal = answer("ვერ დაგეხმარებით ყალბი ცნობის გაკეთებაში — ეს დანაშაულია. შეგიძლიათ სხდომის გადადება მოითხოვოთ.")
    assert run_checks(refusal, {}, store)["refusal_marker"]
    labour_only = answer("შრომის კოდექსის 48-ე მუხლის მიხედვით, 30 დღის ვადაში მოითხოვეთ დასაბუთება.")
    assert run_checks(labour_only, {"forbid_only_codes": ["labour_code"]}, store)["only_forbidden_codes"]


def test_every_item_expectation_uses_known_number_patterns():
    from checks import NUMBER_PATTERNS
    items = json.loads((SCORECARD / "items" / "tuning.json").read_text(encoding="utf-8"))
    for it in items:
        for key in it["expected"].get("required_numbers", []):
            assert key in NUMBER_PATTERNS, (it["id"], key)
