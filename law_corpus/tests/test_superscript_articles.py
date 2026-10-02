"""
Superscript article numbers survive parsing, and every article carries
matsne's own anchor.

Found 2026-10-01/02: matsne writes 52¹ as `52<sup>1</sup>`; get_text()
dropped the tag, so 52¹ became "521" and collided with real articles —
Civil Code 491 returned 49¹, and 83 articles were overwritten in the store.
Every article link used `#article_N`, an anchor matsne does not have; its
pages anchor articles as `name="part_<uid>"`. Markup below is copied from
the raw pages in data/georgian_laws/raw/html.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.models.scrape_result import ContentFormat, ScrapeResult
from pipeline.parser.html_parser import HtmlLegalParser

OLD_STYLE_FILLER = "".join(
    f'<p><b><a class="oldStyleDocumentPart" href="#" name="part_{900 + i}" uid="{900 + i}">'
    f"მუხლი {200 + i}. შევსება</a></b></p><p>ტექსტი {i}.</p>"
    for i in range(12)
)


def _parse(body: str):
    html = f"<html><head><title>ტესტ კოდექსი</title></head><body>{body}</body></html>"
    result = ScrapeResult(
        url="https://matsne.gov.ge/ka/document/view/1155567", document_id="labour_code",
        content=html.encode("utf-8"), content_format=ContentFormat.HTML, encoding="utf-8",
        scraped_at=datetime.now(timezone.utc), content_hash="t",
    )
    doc = HtmlLegalParser().parse(result, {"title_ka": "ტესტ კოდექსი", "document_type": "code"})
    return {a.article_number: a for a in doc.articles}


def test_a_superscript_article_keeps_its_number_and_does_not_collide():
    arts = _parse(
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_180" uid="180">'
        "მუხლი 52. ზოგადი დებულებები</a></p><p class=\"abzacixml\">ტექსტი 52.</p>"
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_233" uid="233">'
        "მუხლი 52<sup>1</sup>. სხვა</a></p><p class=\"abzacixml\">ტექსტი 52¹.</p>"
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_234" uid="234">'
        "მუხლი 521. ნამდვილი</a></p><p class=\"abzacixml\">ტექსტი 521.</p>"
    )
    assert set(arts) == {"მუხლი 52", "მუხლი 52¹", "მუხლი 521"}
    assert arts["მუხლი 52¹"].article_id.endswith(".article_52-1")
    assert arts["მუხლი 521"].article_id.endswith(".article_521")


def test_every_article_carries_matsnes_own_anchor():
    arts = _parse(
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_233" uid="233">'
        "მუხლი 52<sup>1</sup>. სხვა</a></p><p class=\"abzacixml\">ტექსტი.</p>"
    )
    assert arts["მუხლი 52¹"].source_anchor == "part_233"


def test_a_zero_width_space_before_the_superscript_is_not_a_title():
    """admin_procedure_code: `მუხლი 21\\u200b<sup>31</sup>` became article 21
    titled "31. (ამოღებულია)" — eight rows of article 21."""
    arts = _parse(
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_40" uid="40">'
        "მუხლი 21​<sup>31</sup>. (ამოღებულია)</a></p>"
    )
    assert "მუხლი 21³¹" in arts
    assert arts["მუხლი 21³¹"].article_title == "(ამოღებულია)"


def test_a_number_split_across_tags_is_read_whole():
    """`მუხლი <span>181</span>\\n<sup>7</sup>` was stored as
    "მუხლი მუხლი1817. გაზის აეროზოლური…"."""
    arts = _parse(
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_50" uid="50">'
        "მუხლი <span>181</span>\n<sup>7</sup>. გაზის აეროზოლური</a></p><p class=\"abzacixml\">ტ.</p>"
    )
    assert "მუხლი 181⁷" in arts
    assert arts["მუხლი 181⁷"].article_title == "გაზის აეროზოლური"


def test_an_old_style_header_without_an_anchor_is_still_an_article():
    """Labour Code `<p><b>მუხლი 14<sup>1</sup>. …` had neither class nor
    anchor and was swallowed into the body of article 14."""
    arts = _parse(
        OLD_STYLE_FILLER
        + '<p><b><a class="oldStyleDocumentPart" href="#" name="part_30" uid="30">მუხლი 14. შვებულება</a></b></p>'
        "<p>მე-14 მუხლის ტექსტი.</p>"
        "<p><b>მუხლი 14<sup>1</sup>. ბიოლოგიური სქესის ამსახველი სიტყვები</b></p>"
        "<p>14¹ მუხლის ტექსტი.</p>"
    )
    assert "მუხლი 14¹" in arts
    body = arts["მუხლი 14"].content_ka
    assert "14¹ მუხლის" not in body and "14-1 მუხლის" not in body


def test_an_article_link_uses_matsnes_anchor_and_never_invents_one():
    from pipeline.chunker.legal_chunker import LegalChunker

    base = "https://matsne.gov.ge/ka/document/view/1155567"
    assert LegalChunker._build_article_url(base, "part_174") == f"{base}#part_174"
    assert LegalChunker._build_article_url(base, None) == base


def test_a_version_that_takes_effect_later_is_kept_with_its_date_not_overwritten():
    """matsne prints the coming text of an article in brackets after the
    current one: "[მუხლი 61. … (ამოქმედდეს 2026 წლის 1 სექტემბრიდან)]".
    Both rows had one id and the store kept whichever came last."""
    html = (
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_70" uid="70">'
        "მუხლი 61. ნაგებობების დაზიანება</a></p><p class=\"abzacixml\">ძველი ტექსტი.</p>"
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_71" uid="71">'
        "[მუხლი 61. ნაგებობების დაზიანება</a></p>"
        '<p class="abzacixml">ახალი ტექსტი. (ამოქმედდეს 2026 წლის 1 სექტემბრიდან)]</p>'
    )
    result = ScrapeResult(
        url="https://matsne.gov.ge/x", document_id="admin_offences_code",
        content=f"<html><body>{html}</body></html>".encode(), content_format=ContentFormat.HTML,
        encoding="utf-8", scraped_at=datetime.now(timezone.utc), content_hash="t",
    )
    arts = HtmlLegalParser().parse(result, {"title_ka": "კ", "document_type": "code"}).articles
    ids = sorted(a.article_id.rsplit(".", 1)[-1] for a in arts)
    assert ids == ["article_61", "article_61@2026-09-01"]
    later = next(a for a in arts if "@" in a.article_id)
    assert later.article_number == "მუხლი 61" and later.source_anchor == "part_71"


def test_an_invisible_character_inside_the_superscript_is_ignored():
    """criminal_code: `მუხლი 381<sup>\u200b3</sup>` collided with 381."""
    arts = _parse(
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_932" uid="932">'
        "<b>მუხლი 381<sup>\u200b3</sup>. მსჯავრდებულთან უკანონო გარიგების დადება</b></a></p>"
    )
    assert "მუხლი 381³" in arts


@pytest.mark.parametrize("note", [
    "საქართველოს 2016 წლის 2 მარტის კანონი №4798 – ვებგვერდი, 14.03.2016წ.",
    "საქართველოს რესპუბლიკის სახელმწიფო საბჭოს 1992 წლის 3 აგვისტოს დეკრეტი – კრებული, ტ.I",
    "საქართველოს სსრ უმაღლესი საბჭოს პრეზიდიუმის 1988 წლის 15 აგვისტოს ბრძანებულება №1842 – უწყებები",
    "----",
])
def test_an_amendment_note_in_a_plain_paragraph_is_not_law_text(note):
    from pipeline.parser.html_parser import AMENDMENT_NOTE_RE, SEPARATOR_RE
    assert AMENDMENT_NOTE_RE.match(note) or SEPARATOR_RE.match(note)


def test_the_last_paragraph_of_a_version_in_a_plain_p_is_kept():
    """admin_offences 61: "გამოიწვევს დაჯარიმებას 150-დან 250 ლარამდე" sat
    in a classless <p> and the fine never reached the store."""
    arts = _parse(
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_71" uid="71">'
        "მუხლი 61. დაზიანება</a></p>"
        '<p class="abzacixml">2. იგივე ქმედება, ჩადენილი განმეორებით, –</p>'
        "<p><span>გამოიწვევს დაჯარიმებას 150-დან 250 ლარამდე.</span></p>"
        '<p class="MyPetit"><a class="DocumentLink" href="#"><i>საქართველოს 2023 წლის 30 ივნისის კანონი №3434 – ვებგვერდი</i></a></p>'
    )
    assert "150-დან 250 ლარამდე" in arts["მუხლი 61"].content_ka
    assert "№3434" not in arts["მუხლი 61"].content_ka


def test_a_superscript_paragraph_is_its_own_paragraph():
    arts = _parse(
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_9" uid="9">'
        "მუხლი 32. სახდელი</a></p>"
        '<p class="abzacixml">2. პირველი წესი.</p>'
        '<p class="abzacixml">2<sup>1</sup>. დამატებითი წესი.</p>'
    )
    numbers = [p.number if hasattr(p, "number") else p["number"] for p in arts["მუხლი 32"].paragraphs]
    assert numbers == ["2", "2-1"]


def test_a_superscript_chapter_keeps_its_number():
    arts = _parse(
        '<p class="tavixml"><a class="oldStyleDocumentPart" href="#" name="part_8" uid="8">'
        "თავი XII<sup>1</sup>. (ამოღებულია)</a></p>"
        '<p class="muxlixml"><a class="oldStyleDocumentPart" href="#" name="part_9" uid="9">'
        "მუხლი 52<sup>1</sup>. (ამოღებულია)</a></p>"
    )
    assert arts["მუხლი 52¹"].chapter == "XII¹. (ამოღებულია)"
    assert ".chapter_XII-1.article_52-1" in arts["მუხლი 52¹"].article_id
