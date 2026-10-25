"""Tests for the parser module."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Ensure ingest_thresholds.py (in law_corpus/) is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.models.scrape_result import ContentFormat, ScrapeResult
from pipeline.parser.html_parser import HtmlLegalParser
from pipeline.parser.structure_extractor import StructureExtractor
from pipeline.parser.metadata_extractor import MetadataExtractor
from pipeline.utils.georgian_text import (
    contains_georgian,
    extract_article_references,
    normalise_superscripts,
)


class TestGeorgianText:
    """Test Georgian text utilities."""

    def test_contains_georgian(self) -> None:
        assert contains_georgian("მუხლი 1")
        assert not contains_georgian("Article 1")

    def test_normalise_superscripts(self) -> None:
        assert normalise_superscripts("45¹") == "45-1"
        assert normalise_superscripts("100²³") == "100-23"
        assert normalise_superscripts("99") == "99"

    def test_extract_article_references(self) -> None:
        text = "მუხლი 123-ის შესაბამისად და მუხლი 45"
        refs = extract_article_references(text)
        assert "123" in refs
        assert "45" in refs


class TestStructureExtractor:
    """Test structure extraction from Georgian legal text."""

    def test_extract_articles(self) -> None:
        text = """
        თავი I - ძირითადი დებულებები

        მუხლი 1. პირველი მუხლი
        ეს არის პირველი მუხლის ტექსტი.
        1. პირველი პუნქტი.
        2. მეორე პუნქტი.

        მუხლი 2. მეორე მუხლი
        ეს არის მეორე მუხლის ტექსტი.
        """
        extractor = StructureExtractor()
        nodes = extractor.extract(text)
        articles = extractor.flatten_articles(nodes)

        assert len(articles) >= 2
        assert articles[0]["number"] == "1"
        assert articles[1]["number"] == "2"
        assert "ძირითადი დებულებები" in (articles[0].get("chapter") or "")

    def test_extract_with_books(self) -> None:
        text = """
        წიგნი I - ზოგადი დებულებები

        თავი I - პრინციპები

        მუხლი 1. ტესტი
        ტესტის ტექსტი.
        """
        extractor = StructureExtractor()
        nodes = extractor.extract(text)
        articles = extractor.flatten_articles(nodes)

        assert len(articles) >= 1
        assert articles[0].get("book") is not None


class TestMetadataExtractor:
    """Test metadata extraction from HTML."""

    def test_extract_from_sample_html(self, sample_html: str) -> None:
        extractor = MetadataExtractor()
        meta = extractor.extract(sample_html, "civil_code", {
            "title_ka": "სამოქალაქო კოდექსი",
            "title_en": "Civil Code",
            "document_type": "code",
        })
        assert meta.document_id == "civil_code"
        assert "კოდექსი" in meta.title_ka or "სამოქალაქო" in meta.title_ka
        assert meta.document_type.value in ("code", "law")


class TestHtmlParser:
    """Test the full HTML parser on sample data."""

    def test_parse_sample_html(self, sample_html_bytes: bytes) -> None:
        result = ScrapeResult(
            url="https://matsne.gov.ge/ka/document/view/31702",
            document_id="civil_code",
            content=sample_html_bytes,
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="test",
        )
        parser = HtmlLegalParser()
        doc = parser.parse(result, {
            "title_ka": "სამოქალაქო კოდექსი",
            "title_en": "Civil Code",
            "document_type": "code",
            "url": "https://matsne.gov.ge/ka/document/view/31702",
        })

        assert doc.document_id == "civil_code"
        assert doc.article_count >= 3
        # Check that articles contain Georgian text
        for article in doc.articles:
            assert contains_georgian(article.content_ka)

    def test_cross_reference_extraction(self, sample_html_bytes: bytes) -> None:
        result = ScrapeResult(
            url="https://matsne.gov.ge/ka/document/view/31702",
            document_id="civil_code",
            content=sample_html_bytes,
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="test",
        )
        parser = HtmlLegalParser()
        doc = parser.parse(result, {"document_type": "code", "title_ka": "test"})

        # Article 8 references Article 123
        article_8 = [a for a in doc.articles if "8" in a.article_number]
        if article_8:
            assert any("123" in ref for ref in article_8[0].cross_references)


class TestArticleNumberFallback:
    """
    Regression: when ARTICLE_RE doesn't match (no space between მუხლი and number),
    the parser should still extract just the number, not the entire raw text.

    Bug: 'მუხლი მუხლი7.საქართველოს...' instead of 'მუხლი 7'
    Fix: html_parser.py fallback regex extracts number from 'მუხლი7.Title'
    """

    def test_no_space_article_header(self) -> None:
        """Simulate a <p class='muxlixml'> with no space: 'მუხლი7.სათაური'"""
        html = """
        <html><head><title>საქართველოს ტესტ კოდექსი</title></head><body>
        <p class="muxlixml">მუხლი7.საარჩევნო ადმინისტრაციის სტატუსი</p>
        <p class="abzacixml">ტესტ ტექსტი პარაგრაფი.</p>
        </body></html>
        """
        result = ScrapeResult(
            url="https://matsne.gov.ge/test",
            document_id="test_code",
            content=html.encode("utf-8"),
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="test",
        )
        parser = HtmlLegalParser()
        doc = parser.parse(result, {"title_ka": "ტესტ კოდექსი", "document_type": "code"})

        assert len(doc.articles) >= 1
        art = doc.articles[0]
        # Must be "მუხლი 7", NOT "მუხლი მუხლი7.საარჩევნო..."
        assert art.article_number == "მუხლი 7", f"Got: {art.article_number}"
        assert "მუხლი მუხლი" not in art.article_number

    def test_no_space_with_superscript_suffix(self) -> None:
        """Simulate 'მუხლი276.ტრანსპორტის...' — common in criminal code."""
        html = """
        <html><head><title>ტესტ</title></head><body>
        <p class="muxlixml">მუხლი276.ტრანსპორტის მოძრაობის წესის დარღვევა</p>
        <p class="abzacixml">შინაარსი.</p>
        </body></html>
        """
        result = ScrapeResult(
            url="https://matsne.gov.ge/test",
            document_id="test_code",
            content=html.encode("utf-8"),
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="test",
        )
        parser = HtmlLegalParser()
        doc = parser.parse(result, {"title_ka": "ტესტ", "document_type": "code"})

        assert len(doc.articles) >= 1
        assert doc.articles[0].article_number == "მუხლი 276"

    def test_standard_article_still_works(self) -> None:
        """Normal 'მუხლი 45. სათაური' must still work."""
        html = """
        <html><head><title>ტესტ კოდექსი</title></head><body>
        <p class="muxlixml">მუხლი 45. ნორმალური სათაური</p>
        <p class="abzacixml">ტექსტი.</p>
        </body></html>
        """
        result = ScrapeResult(
            url="https://matsne.gov.ge/test",
            document_id="test_code",
            content=html.encode("utf-8"),
            content_format=ContentFormat.HTML,
            encoding="utf-8",
            scraped_at=datetime.now(timezone.utc),
            content_hash="test",
        )
        parser = HtmlLegalParser()
        doc = parser.parse(result, {"title_ka": "ტესტ კოდექსი", "document_type": "code"})

        assert len(doc.articles) >= 1
        assert doc.articles[0].article_number == "მუხლი 45"
        assert doc.articles[0].article_title == "ნორმალური სათაური"


class TestThresholdCodeNameCanonical:
    """
    Regression: threshold_catalog.json uses short-form code names
    (e.g. 'სისხლის სამართლის კოდექსი') but ChromaDB needs the full
    canonical form ('საქართველოს სისხლის სამართლის კოდექსი').

    Fix: ingest_thresholds._canonicalize_code_name() maps short → full.
    """

    def test_canonicalize_criminal_code(self) -> None:
        from ingest_thresholds import _canonicalize_code_name

        assert _canonicalize_code_name("სისხლის სამართლის კოდექსი") == \
            "საქართველოს სისხლის სამართლის კოდექსი"

    def test_canonicalize_civil_code(self) -> None:
        from ingest_thresholds import _canonicalize_code_name

        assert _canonicalize_code_name("სამოქალაქო კოდექსი") == \
            "საქართველოს სამოქალაქო კოდექსი"

    def test_canonicalize_labor_code(self) -> None:
        from ingest_thresholds import _canonicalize_code_name

        assert _canonicalize_code_name("შრომის კოდექსი") == \
            "საქართველოს შრომის კოდექსი"

    def test_already_canonical_unchanged(self) -> None:
        from ingest_thresholds import _canonicalize_code_name

        full = "საქართველოს სისხლის სამართლის კოდექსი"
        assert _canonicalize_code_name(full) == full

    def test_narcotics_law_unchanged(self) -> None:
        """Narcotics law doesn't have საქართველოს prefix — should pass through."""
        from ingest_thresholds import _canonicalize_code_name

        name = "ნარკოტიკული საშუალებების შესახებ კანონი"
        assert _canonicalize_code_name(name) == name

    def test_build_metadata_uses_canonical(self) -> None:
        """build_threshold_metadata must output canonical code_name."""
        from ingest_thresholds import build_threshold_metadata

        entry = {
            "code_name": "სისხლის სამართლის კოდექსი",
            "article_number": "მუხლი 177",
            "threshold_type": "monetary",
            "description_ka": "ტესტ",
            "source_url": "https://matsne.gov.ge",
            "last_verified": "2026-01-01",
        }
        meta = build_threshold_metadata(entry)
        assert meta["code_name"] == "საქართველოს სისხლის სამართლის კოდექსი"



def _parse_fixture(name: str, document_id: str, url: str):
    raw = (Path(__file__).parent / "fixtures" / name).read_bytes()
    result = ScrapeResult(
        url=url, document_id=document_id, content=raw,
        content_format=ContentFormat.HTML, encoding="utf-8",
        scraped_at=datetime.now(timezone.utc), content_hash="test",
    )
    return HtmlLegalParser().parse(result, {"url": url, "title_ka": "x", "document_type": "code"})


class TestMatsneClassLayout:
    """Defects found in the live corpus (2026-10-24 compliance run)."""

    @pytest.fixture
    def articles(self) -> dict[str, object]:
        doc = _parse_fixture("matsne_class_layout.html", "civil_procedure_code",
                             "https://matsne.gov.ge/ka/document/view/29962")
        return {a.article_id: a for a in doc.articles}

    def test_body_in_msonormal_paragraph_is_kept(self, articles) -> None:
        art = articles["civil_procedure_code.chapter_XLV.article_369"]
        assert art.content_ka.startswith("1. სააპელაციო საჩივრის შეტანის ვადაა 14 დღე.")
        assert [p.number for p in art.paragraphs] == ["1", "2"]

    def test_inline_links_keep_their_spacing(self, articles) -> None:
        art = articles["civil_procedure_code.chapter_XLV.article_369"]
        assert "ჩაბარება ამ კოდექსის 70-ე–78-ე მუხლების ან 259¹ მუხლის შესაბამისად." in art.content_ka

    def test_amendment_citations_are_not_article_text(self, articles) -> None:
        art = articles["civil_procedure_code.chapter_XLV.article_369"]
        assert "კანონი №741" not in art.content_ka
        assert "№5669" not in articles["civil_procedure_code.chapter_XLV.article_368-1"].content_ka

    def test_superscript_number_is_not_flattened(self, articles) -> None:
        sup = articles["civil_procedure_code.chapter_XLV.article_3-1"]
        plain = articles["civil_procedure_code.chapter_XLV.article_31"]
        assert sup.article_number == "მუხლი 3¹"
        assert plain.article_number == "მუხლი 31"
        assert sup.content_ka == "ტექსტი."

    def test_hierarchy_and_anchor(self, articles) -> None:
        art = articles["civil_procedure_code.chapter_XLV.article_369"]
        assert art.book == "მესამე. სასამართლო გადაწყვეტილებათა გასაჩივრება"
        assert art.part == "მეოთხე."
        assert art.chapter == "XLV. აპელაციის დასაშვებობა"
        assert art.matsne_anchor == "part_476"

    def test_mis_styled_body_class_is_body(self, articles) -> None:
        assert articles["civil_procedure_code.chapter_XLV.article_31"].content_ka == "ა) პირველი;"

    def test_repealed_placeholder(self, articles) -> None:
        assert articles["civil_procedure_code.chapter_XLV.article_370"].is_repealed
        assert not articles["civil_procedure_code.chapter_XLV.article_369"].is_repealed

    def test_future_heading_wording_stays_with_current_article(self, articles) -> None:
        art = articles["civil_procedure_code.chapter_XLV.article_371"]
        assert art.in_force
        assert art.content_ka.splitlines()[0].startswith("[მუხლი 371. ახალი სათაური (ამოქმედდეს")
        assert "1. საერთო ტექსტი." in art.content_ka
        assert "civil_procedure_code.chapter_XLV.article_371.pending" not in articles

    def test_future_article_is_marked_not_in_force(self, articles) -> None:
        art = articles["civil_procedure_code.chapter_XLV.article_372-1.pending"]
        assert not art.in_force
        assert art.article_number == "მუხლი 372¹"
        assert art.content_ka == "1. ახალი წესი. (ამოქმედდეს 2027 წლის 1 იანვრიდან)"

    def test_no_duplicate_ids(self, articles) -> None:
        doc = _parse_fixture("matsne_class_layout.html", "civil_procedure_code",
                             "https://matsne.gov.ge/ka/document/view/29962")
        assert len(doc.articles) == len(articles)


class TestMatsneTableLayout:
    """The table layout used by newer acts (e.g. the 2023 personal data law)."""

    def test_articles_chapters_and_notes(self) -> None:
        doc = _parse_fixture("matsne_table_layout.html", "personal_data_law",
                             "https://matsne.gov.ge/ka/document/view/5827307")
        arts = {a.article_id: a for a in doc.articles}
        assert list(arts) == ["personal_data_law.chapter_I.article_1", "personal_data_law.chapter_I.article_3"]
        definitions = arts["personal_data_law.chapter_I.article_3"]
        assert definitions.chapter == "I. ზოგადი დებულებები"
        assert definitions.article_title == "ტერმინთა განმარტება"
        assert definitions.content_ka == "ამ კანონის მიზნებისთვის:\nა) პერსონალური მონაცემი − ნებისმიერი ინფორმაცია;"
        assert definitions.matsne_anchor == "DOCUMENT:1;CHAPTER:1;ARTICLE:3;"


class TestParagraphs:
    def test_sub_points_belong_to_their_paragraph(self) -> None:
        paras = HtmlLegalParser._parse_paragraphs(
            "1. შეიძლება გასაჩივრდეს:\nა) დადგენილება;\nბ¹) გადაწყვეტილება;\n2. სხვა."
        )
        assert [p.number for p in paras] == ["1", "2"]
        assert [s.number for s in paras[0].sub_points] == ["ა", "ბ¹"]
        assert paras[0].text == "შეიძლება გასაჩივრდეს:\nა) დადგენილება;\nბ¹) გადაწყვეტილება;"

    def test_letters_without_numbered_parent_stay_top_level(self) -> None:
        paras = HtmlLegalParser._parse_paragraphs("ა) პირველი;\nბ) მეორე.")
        assert [p.number for p in paras] == ["ა", "ბ"]
