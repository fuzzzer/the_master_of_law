"""
Tests for the law connector service — every tool, on real stored law text.

The fixture store holds real articles copied from the store the live server
serves, including Civil Procedure Code art. 369 with its first paragraph
missing (the gap the 2026-10-24 compliance test found), so the tests also
prove the connector says so instead of hiding it.
"""

from __future__ import annotations

from app.schemas.connector_schema import NOT_LEGAL_ADVICE, VERSION_UNKNOWN_NOTE
from app.services.article_store_service import ArticleStoreService
from app.services.law_connector_service import LawConnectorService
from tests.conftest import build_connector_article_store, build_court_chroma

MATSNE = "https://matsne.gov.ge/ka/document/view/"


def _with_court(store, tmp_path) -> LawConnectorService:
    return LawConnectorService(store=store, chroma=build_court_chroma(tmp_path / "chroma"))


class TestListCodes:
    def test_lists_codes_with_links_and_counts(self, connector_service):
        result = connector_service.list_codes()
        by_code = {c.code: c for c in result.codes}
        assert set(by_code) == {"civil_code", "civil_procedure_code", "labour_code"}
        assert by_code["labour_code"].source_url == MATSNE + "1155567"
        assert by_code["civil_code"].article_count > 0
        assert by_code["civil_code"].version_date is None
        assert by_code["civil_code"].version_note == VERSION_UNKNOWN_NOTE


class TestSearchLaw:
    def test_finds_appeal_deadline_article_with_exact_snippet(
        self, connector_service, connector_store
    ):
        result = connector_service.search_law("სააპელაციო საჩივრის შეტანის ვადა")
        assert result.found
        top = result.results[0]
        assert top.id == "article:civil_procedure_code:369"
        assert top.article_number == "მუხლი 369"
        stored = connector_store.get_article("civil_procedure_code", "369")["content_ka"]
        assert top.snippet.removesuffix(" …") in stored
        assert top.source_url == MATSNE + "29962#article_369"

    def test_inflected_words_still_match(self, connector_service):
        """'ხანდაზმულობას' is not literally in the text; its stem is."""
        result = connector_service.search_law("ხანდაზმულობას როდის წყვეტს სარჩელი")
        assert result.found
        assert any(h.code == "civil_code" for h in result.results)

    def test_code_filter(self, connector_service):
        result = connector_service.search_law("ვადა", code="labour_code")
        assert result.results
        assert all(h.code == "labour_code" for h in result.results)

    def test_unknown_code_is_reported(self, connector_service):
        result = connector_service.search_law("ვადა", code="space_law")
        assert not result.found
        assert "list_codes" in result.message

    def test_nothing_found_says_so(self, connector_service):
        result = connector_service.search_law("კრიპტოვალუტა ბლოკჩეინი")
        assert not result.found
        assert result.results == []
        assert "Do not answer from memory" in result.message

    def test_limit_is_capped(self, connector_service):
        assert len(connector_service.search_law("ვადა", limit=500).results) <= 25


class TestGetArticle:
    def test_full_text_paragraphs_and_neighbours(self, connector_service, connector_store):
        result = connector_service.get_article("civil_code", "138")
        assert result.found
        art = result.article
        assert art.text == connector_store.get_article("civil_code", "138")["content_ka"]
        assert art.previous_article.article_number == "მუხლი 137"
        assert art.next_article.article_number == "მუხლი 139"
        assert art.source_url == MATSNE + "31702#article_138"

    def test_georgian_code_name_and_article_forms(self, connector_service):
        assert connector_service.get_article("შრომის კოდექსი", "მუხლი 48").found
        assert connector_service.get_article("labour_code", "48-ე").found

    def test_requested_paragraph(self, connector_service):
        art = connector_service.get_article("labour_code", "48", paragraph="1").article
        assert art.requested_paragraph is not None
        assert art.requested_paragraph.number == "1"

    def test_missing_paragraph_is_reported(self, connector_service):
        result = connector_service.get_article("labour_code", "48", paragraph="99")
        assert result.found
        assert "Paragraph 99" in result.message

    def test_missing_first_paragraph_is_flagged(self, connector_service):
        """Art. 369 is stored without part 1 (the 14-day term): say so."""
        art = connector_service.get_article("civil_procedure_code", "369").article
        assert "starts at paragraph 2" in art.version_note

    def test_unknown_article_is_not_invented(self, connector_service):
        result = connector_service.get_article("civil_code", "99999")
        assert not result.found
        assert "do not cite it" in result.message

    def test_unknown_code_never_falls_back_to_another_code(self, connector_service):
        result = connector_service.get_article("nonexistent_code", "138")
        assert not result.found
        assert "Unknown code" in result.message


class TestBrowseCode:
    def test_lists_articles_when_no_chapters(self, connector_service):
        result = connector_service.browse_code("civil_code")
        assert result.found
        numbers = [a.article_number for a in result.articles]
        assert numbers == ["მუხლი 137", "მუხლი 138", "მუხლი 139"]

    def test_repealed_articles_are_left_out(self, connector_service):
        numbers = [a.article_number for a in connector_service.browse_code("civil_code").articles]
        assert "მუხლი 1110" not in numbers

    def test_paging(self, connector_service):
        result = connector_service.browse_code("civil_code", limit=2)
        assert len(result.articles) == 2
        assert "offset=2" in result.message

    def test_unknown_code(self, connector_service):
        assert not connector_service.browse_code("moon_code").found


class TestVerifyCitation:
    def test_exists_and_returns_actual_text(self, connector_service):
        result = connector_service.verify_citation(
            "labour_code", "48", "30 დღის ვადაში წერილობითი დასაბუთების მოთხოვნა"
        )
        assert result.exists
        assert result.text
        assert result.lexical_check.numbers_found_in_text == ["30"]

    def test_number_missing_from_text_is_shown(self, connector_service):
        result = connector_service.verify_citation(
            "civil_procedure_code", "369", "სააპელაციო საჩივრის ვადა 14 დღეა"
        )
        assert result.exists
        assert result.lexical_check.numbers_not_in_text == ["14"]
        assert "not a legal judgement" in result.lexical_check.label

    def test_invented_article(self, connector_service):
        result = connector_service.verify_citation("civil_code", "4242", "anything")
        assert not result.exists
        assert result.text is None

    def test_repealed_article(self, connector_service):
        result = connector_service.verify_citation("civil_code", "1110", "anything")
        assert result.exists
        assert result.is_repealed
        assert "repealed" in result.message

    def test_paragraph_that_does_not_exist(self, connector_service):
        result = connector_service.verify_citation("labour_code", "48", "x", paragraph="77")
        assert result.exists
        assert result.paragraph_exists is False


class TestCourtPractice:
    def test_source_unavailable_is_honest(self, connector_service):
        result = connector_service.find_court_practice("ხანდაზმულობა")
        assert result.status == "source_unavailable"
        assert result.results == []
        assert "do not cite" in result.message

    def test_finds_real_decisions_grouped_by_case(self, connector_store, tmp_path):
        service = _with_court(connector_store, tmp_path)
        result = service.find_court_practice("ხანდაზმულობის ვადის შეწყვეტა")
        assert result.status == "found"
        ids = [d.id for d in result.results]
        assert ids.count("case:court_practice:AS-664-2023") == 1
        decision = next(d for d in result.results if d.collection == "court_practice")
        assert decision.case_number == "AS-664-2023"
        assert decision.year == "2023"
        assert decision.source_url is None and "supremecourt.ge" in decision.link_note
        chamber = next(d for d in result.results if d.collection == "grand_chamber")
        assert chamber.source_url.startswith("https://www.supremecourt.ge/")

    def test_none_found(self, connector_store, tmp_path):
        service = _with_court(connector_store, tmp_path)
        result = service.find_court_practice("საავტორო უფლებები პროგრამულ უზრუნველყოფაზე")
        assert result.status == "none_found"
        assert "invent case numbers" in result.message

    def test_fetch_case_joins_chunks_in_order(self, connector_store, tmp_path):
        service = _with_court(connector_store, tmp_path)
        doc = service.fetch("case:court_practice:AS-664-2023")
        assert doc.text.index("ხანდაზმულობის") < doc.text.index("არ დაკმაყოფილდეს")


class TestSearchAndFetch:
    def test_search_returns_ids_titles_urls(self, connector_service):
        result = connector_service.search("ხანდაზმულობის ვადის დენის შეწყვეტა")
        assert result.results
        for item in result.results:
            assert item.id and item.title and item.url.startswith("https://")

    def test_fetch_article(self, connector_service):
        doc = connector_service.fetch("article:civil_code:138")
        assert "138" in doc.title
        assert doc.url == MATSNE + "31702#article_138"
        assert doc.metadata["notice"] == NOT_LEGAL_ADVICE

    def test_fetch_unknown_id(self, connector_service):
        assert connector_service.fetch("article:nope:1") is None
        assert connector_service.fetch("bogus") is None


class TestNewStoreFields:
    def test_version_fields_are_picked_up(self, tmp_path):
        store = ArticleStoreService(
            db_path=build_connector_article_store(tmp_path / "v.db", with_version_fields=True)
        )
        service = LawConnectorService(store=store)
        art = service.get_article("civil_code", "138").article
        assert art.version_date == "2026-09-30"
        assert art.in_force_since == "2024-01-01"
        assert art.version_note is None
        assert service.list_codes().codes[0].version_date == "2026-09-30"

    def test_missing_links_are_rebuilt_from_document_id(self, tmp_path):
        store = ArticleStoreService(
            db_path=build_connector_article_store(tmp_path / "n.db", without_links=True)
        )
        service = LawConnectorService(store=store)
        assert service.get_article("civil_code", "138").article.source_url == (
            MATSNE + "31702#article_138"
        )


class TestGroundedness:
    """Every item the connector returns names its source and carries the notice."""

    QUERIES = ["სააპელაციო საჩივრის ვადა", "შრომითი ხელშეკრულების შეწყვეტა", "ხანდაზმულობა"]

    def test_every_returned_item_has_a_source_link(self, connector_store, tmp_path):
        service = _with_court(connector_store, tmp_path)
        items = []
        for q in self.QUERIES:
            items += service.search_law(q).results
            items += service.find_court_practice(q).results
            for hit in service.search(q).results:
                assert hit.url.startswith("https://")
                assert service.fetch(hit.id).url.startswith("https://")
        items += [c for c in service.list_codes().codes]
        items.append(service.get_article("labour_code", "48").article)
        assert items
        for item in items:
            link = item.source_url or ("supremecourt.ge" in (getattr(item, "link_note", "") or ""))
            assert link, item
            assert item.notice == NOT_LEGAL_ADVICE
        for hit in [i for i in items if hasattr(i, "version_note") and hasattr(i, "version_date")]:
            assert hit.version_date or hit.in_force_since or hit.version_note
