"""
Tests for the Phase 3 verification net:
- 3.1 court-case citation extraction + verification
- 3.2 sub-article (paragraph) verification against the article store
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_pipeline_service import AgentPipelineService
from app.services.citation_service import CitationService

STORE_PATH = Path(__file__).parent.parent.parent / "law_corpus" / "data" / "georgian_laws" / "article_store.db"
needs_store = pytest.mark.skipif(not STORE_PATH.exists(), reason="article_store.db not built")


class TestCaseCitationExtraction:
    def setup_method(self):
        self.svc = CitationService(chroma=MagicMock())

    def test_extracts_all_supported_forms(self):
        text = (
            "იხ. საქმე №ას-1280-2019, ასევე ბს-922 და ას-449-431-2016; "
            "სისხლის სამართლის საქმე 814აპ-23 და 2აგ-22."
        )
        cases = self.svc.extract_case_citations(text)
        assert cases == ["ას-1280-2019", "ბს-922", "ას-449-431-2016", "814აპ-23", "2აგ-22"]

    def test_deduplicates(self):
        cases = self.svc.extract_case_citations("ას-175-2022 ... კვლავ ას-175-2022")
        assert cases == ["ას-175-2022"]

    def test_plain_text_no_matches(self):
        assert self.svc.extract_case_citations("გამარჯობა, მუხლი 48") == []


class TestCaseCitationVerification:
    def test_found_and_not_found(self):
        chroma = MagicMock()
        def fake_search(where, collections, limit):
            if where["case_id"]["$eq"] == "ას-1280-2019":
                return [{"chunk_id": "x", "metadata": {
                    "_collection": "court_practice", "court": "supreme_court",
                    "year": 2019, "category": "civil"}}]
            return []
        chroma.search_by_metadata = MagicMock(side_effect=fake_search)
        svc = CitationService(chroma=chroma)
        result = svc.verify_case_citations(["ას-1280-2019", "ას-792-2019"])
        assert [v["case_number"] for v in result["verified"]] == ["ას-1280-2019"]
        assert [v["case_number"] for v in result["not_found"]] == ["ას-792-2019"]

    def test_empty_input(self):
        svc = CitationService(chroma=MagicMock())
        assert svc.verify_case_citations([]) == {"verified": [], "not_found": []}


@needs_store
class TestSubArticleVerification:
    def test_valid_paragraph_passes(self):
        issues = AgentPipelineService._verify_subarticles([
            {"code_name": "შრომის კოდექსი", "article_number": "მუხლი 48", "paragraph": "8"},
        ])
        assert issues == []

    def test_invalid_paragraph_flagged(self):
        issues = AgentPipelineService._verify_subarticles([
            {"code_name": "შრომის კოდექსი", "article_number": "მუხლი 48", "paragraph": "99"},
        ])
        assert len(issues) == 1
        assert issues[0]["paragraph"] == "99"
        assert "9" in issues[0]["available_paragraphs"]

    def test_citation_without_paragraph_skipped(self):
        issues = AgentPipelineService._verify_subarticles([
            {"code_name": "შრომის კოდექსი", "article_number": "მუხლი 48", "paragraph": ""},
        ])
        assert issues == []


class TestCourtChunkContextHeader:
    """The model must see case numbers in its context to be able to cite them."""

    def test_court_chunk_shows_case_id(self):
        ctx = AgentPipelineService._format_law_context([{
            "chunk_id": "court_practice:ას-1280-2019:chunk_1:x",
            "content": "text",
            "metadata": {"_collection": "court_practice", "case_id": "ას-1280-2019",
                         "year": 2019, "article_url": ""},
        }])
        assert "საქმე №ას-1280-2019" in ctx

    def test_statute_chunk_unchanged(self):
        ctx = AgentPipelineService._format_law_context([{
            "chunk_id": "labour_code.article_48.chunk_0",
            "content": "text",
            "metadata": {"_collection": "georgian_laws",
                         "code_name": "საქართველოს შრომის კოდექსი",
                         "article_number": "მუხლი 48", "article_url": "u"},
        }])
        assert "საქართველოს შრომის კოდექსი, მუხლი 48" in ctx


class TestLinkRepair:
    """Invented matsne links never reach the user."""

    def _svc(self):
        return AgentPipelineService(gemini=MagicMock(), citation_svc=MagicMock())

    @pytest.mark.asyncio
    async def test_known_link_kept(self):
        svc = AgentPipelineService(gemini=MagicMock(), citation_svc=MagicMock())
        chunks = [{"metadata": {"article_url": "https://matsne.gov.ge/ka/document/view/1#article_5"}}]
        text = "იხ. [მუხლი 5](https://matsne.gov.ge/ka/document/view/1#article_5)."
        with patch("app.services.agent_pipeline_service.record_step"):
            out = svc._repair_matsne_links(text, chunks, [])
        assert out == text

    @needs_store
    @pytest.mark.asyncio
    async def test_invented_link_repointed_via_store(self):
        svc = AgentPipelineService(gemini=MagicMock(), citation_svc=None)
        text = ("[შრომის კოდექსი, მუხლი 48](https://matsne.gov.ge/ka/document/view/99999#article_48)")
        with patch("app.services.agent_pipeline_service.record_step"):
            out = svc._repair_matsne_links(text, [], [])
        assert "1155567#article_48" in out
        assert "99999" not in out

    @pytest.mark.asyncio
    async def test_unresolvable_link_stripped(self):
        citation_svc = MagicMock()
        citation_svc.extract_citations = MagicMock(return_value=[])
        svc = AgentPipelineService(gemini=MagicMock(), citation_svc=citation_svc)
        text = "[დანართი 2](https://matsne.gov.ge/ka/document/view/31634#article_danarti_2)"
        with patch("app.services.agent_pipeline_service.record_step"):
            out = svc._repair_matsne_links(text, [], [])
        assert out == "დანართი 2"


class TestHallucinatedCaseTriggersCorrection:
    @pytest.mark.asyncio
    async def test_correction_invoked_for_fake_case(self):
        gemini = MagicMock()
        gemini.generate = AsyncMock(return_value="გასწორებული პასუხი (ას-1280-2019)")
        citation_svc = MagicMock()
        citation_svc.extract_citations = MagicMock(return_value=[])
        citation_svc.extract_case_citations = MagicMock(
            side_effect=[["ას-792-2019"], ["ას-1280-2019"]]
        )
        citation_svc.verify_against_corpus = MagicMock(return_value={
            "verified": [], "corpus_found": [], "not_found": [],
        })
        citation_svc.verify_case_citations = MagicMock(side_effect=[
            {"verified": [], "not_found": [{"case_number": "ას-792-2019"}]},
            {"verified": [{"case_number": "ას-1280-2019"}], "not_found": []},
        ])
        citation_svc.verify_citations = MagicMock(return_value=[])
        svc = AgentPipelineService(gemini=gemini, citation_svc=citation_svc)
        recorded = []
        with patch(
            "app.services.agent_pipeline_service.record_step",
            side_effect=lambda step, **kw: recorded.append((step, kw)),
        ):
            text, _, _ = await svc._phase_3_verify(
                "პრაქტიკის მიხედვით (ას-792-2019) ...",
                [{"chunk_id": "c", "content": "x", "metadata": {}}],
            )
        gemini.generate.assert_awaited()
        assert text == "გასწორებული პასუხი (ას-1280-2019)"
        steps = [s for s, _ in recorded]
        assert "case_citation_verification" in steps
