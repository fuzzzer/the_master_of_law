"""
Tests for the Phase 2 generation contract:
- 2.1 retrieval-repair loop (citation outside context → full-text confirm/correct)
- 2.2 anchored-claims check
- 2.3 faithfulness pass (flag-gated)
- 2.4 uncertainty policy (zero statute grounding → disclaimer)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.constants import UNGROUNDED_STATUTE_DISCLAIMER_KA
from app.services.agent_pipeline_service import (
    AgentPipelineService,
    PipelinePlan,
    ToolResultInfo,
)
from app.services.citation_service import check_anchoring


def _law_chunk(cid="law_1"):
    return {
        "chunk_id": cid,
        "content": "მუხლი 48 ტექსტი",
        "metadata": {"_collection": "georgian_laws", "code_name": "საქართველოს შრომის კოდექსი",
                     "article_number": "მუხლი 48"},
    }


class TestRetrievalRepair:
    """2.1: a citation found in corpus but NOT in context must trigger a
    full-text confirm/correct pass, not silent acceptance."""

    @pytest.mark.asyncio
    async def test_corpus_found_triggers_repair_and_correction(self):
        gemini = MagicMock()
        gemini.generate = AsyncMock(return_value="გასწორებული პასუხი მუხლი 48")
        citation_svc = MagicMock()
        citation_svc.extract_case_citations = MagicMock(return_value=[])
        citation_svc.verify_case_citations = MagicMock(return_value={"verified": [], "not_found": []})
        citation_svc.extract_citations = MagicMock(
            side_effect=[
                [{"article_number": "მუხლი 48", "paragraph": "", "code_name": "შრომის კოდექსი", "raw_text": "x"}],
                [{"article_number": "მუხლი 48", "paragraph": "", "code_name": "შრომის კოდექსი", "raw_text": "x"}],
            ]
        )
        corpus_found_item = {
            "article_number": "მუხლი 48", "code_name": "შრომის კოდექსი",
            "verified": True, "content": "snippet", "article_url": "u",
            "corpus_code_name": "საქართველოს შრომის კოდექსი",
        }
        citation_svc.verify_against_corpus = MagicMock(
            side_effect=[
                {"verified": [], "corpus_found": [corpus_found_item], "not_found": []},
                {"verified": [corpus_found_item], "corpus_found": [], "not_found": []},
            ]
        )
        svc = AgentPipelineService(gemini=gemini, citation_svc=citation_svc)

        store = MagicMock()
        store.get_article = MagicMock(return_value={
            "content_ka": "სრული ტექსტი 48-ე მუხლის",
            "article_url": "https://matsne.gov.ge/x#article_48",
        })
        recorded = []
        with patch(
            "app.services.article_store_service.get_article_store_service",
            return_value=store,
        ), patch(
            "app.services.agent_pipeline_service.record_step",
            side_effect=lambda step, **kw: recorded.append((step, kw)),
        ):
            text, citations, iterations = await svc._phase_3_verify(
                "პასუხი მუხლი 48", [_law_chunk()]
            )

        step_names = [s for s, _ in recorded]
        assert "retrieval_repair" in step_names
        repair = dict(recorded)[
            "retrieval_repair"
        ] if step_names.count("retrieval_repair") == 1 else None
        assert repair["repaired"][0]["full_text_from_store"] is True
        # correction model call happened (previously corpus_found was accepted silently)
        gemini.generate.assert_awaited()
        assert text == "გასწორებული პასუხი მუხლი 48"

    @pytest.mark.asyncio
    async def test_all_verified_no_repair(self):
        gemini = MagicMock()
        gemini.generate = AsyncMock()
        citation_svc = MagicMock()
        citation_svc.extract_case_citations = MagicMock(return_value=[])
        citation_svc.verify_case_citations = MagicMock(return_value={"verified": [], "not_found": []})
        citation_svc.extract_citations = MagicMock(return_value=[{"article_number": "მუხლი 48", "paragraph": "", "code_name": "შრომის კოდექსი", "raw_text": "x"}])
        citation_svc.verify_against_corpus = MagicMock(return_value={
            "verified": [{"article_number": "მუხლი 48"}], "corpus_found": [], "not_found": [],
        })
        svc = AgentPipelineService(gemini=gemini, citation_svc=citation_svc)
        recorded = []
        with patch(
            "app.services.agent_pipeline_service.record_step",
            side_effect=lambda step, **kw: recorded.append(step),
        ):
            text, _, _ = await svc._phase_3_verify("პასუხი", [_law_chunk()])
        assert "retrieval_repair" not in recorded
        gemini.generate.assert_not_awaited()


class TestAnchoringCheck:
    """2.2: unanchored legal-claim rate."""

    def test_anchored_claims_pass(self):
        text = (
            "დამსაქმებელი ვალდებულია გაგაფრთხილოთ 30 დღით ადრე "
            "([შრომის კოდექსი, მუხლი 48](https://matsne.gov.ge/x)).\n\n"
            "თქვენ გაქვთ უფლება მოითხოვოთ კომპენსაცია (მუხლი 48.8)."
        )
        r = check_anchoring(text)
        assert r["claim_paragraphs"] == 2
        assert r["unanchored"] == 0

    def test_unanchored_claim_flagged(self):
        text = "დამსაქმებელი ვალდებულია გადაგიხადოთ კომპენსაცია სამი თვის ხელფასის ოდენობით."
        r = check_anchoring(text)
        assert r["claim_paragraphs"] == 1
        assert r["unanchored"] == 1
        assert r["unanchored_rate"] == 1.0
        assert len(r["unanchored_samples"]) == 1

    def test_non_claim_text_ignored(self):
        r = check_anchoring("გამარჯობა! როგორ შემიძლია დაგეხმაროთ დღეს?")
        assert r["claim_paragraphs"] == 0
        assert r["unanchored_rate"] == 0.0


class TestUncertaintyPolicy:
    """2.4: zero statute grounding → explicit disclaimer prefix."""

    def _svc(self):
        return AgentPipelineService(gemini=MagicMock(), citation_svc=MagicMock())

    def test_disclaimer_added_when_ungrounded(self):
        plan = PipelinePlan(needs_rag=True)
        court_only = [{"chunk_id": "c", "metadata": {"_collection": "court_practice"}}]
        out = self._svc()._apply_uncertainty_policy("პასუხი", plan, court_only, [], False)
        assert out.startswith(UNGROUNDED_STATUTE_DISCLAIMER_KA)

    def test_no_disclaimer_with_statute_chunk(self):
        plan = PipelinePlan(needs_rag=True)
        out = self._svc()._apply_uncertainty_policy("პასუხი", plan, [_law_chunk()], [], False)
        assert out == "პასუხი"

    def test_no_disclaimer_with_tool_grounding(self):
        plan = PipelinePlan(needs_rag=True)
        tools = [ToolResultInfo(tool_name="get_article", status="executed", result={"found": True})]
        out = self._svc()._apply_uncertainty_policy("პასუხი", plan, [], tools, False)
        assert out == "პასუხი"

    def test_no_disclaimer_with_full_code_injection(self):
        plan = PipelinePlan(needs_rag=True)
        out = self._svc()._apply_uncertainty_policy("პასუხი", plan, [], [], True)
        assert out == "პასუხი"

    def test_no_disclaimer_when_rag_not_needed(self):
        plan = PipelinePlan(needs_rag=False)
        out = self._svc()._apply_uncertainty_policy("გამარჯობა!", plan, [], [], False)
        assert out == "გამარჯობა!"


class TestDeadlineGuard:
    """0.2 enforced structurally: action advice without deadlines gets a warning."""

    def _svc(self):
        return AgentPipelineService(gemini=MagicMock(), citation_svc=MagicMock())

    def test_guard_appended_when_action_without_deadline(self):
        with patch("app.services.agent_pipeline_service.record_step"):
            out = self._svc()._apply_deadline_guard("შეგიძლიათ მიმართოთ სასამართლოს.")
        assert "გადაამოწმეთ" in out

    def test_untouched_when_deadline_present(self):
        text = "მიმართეთ სასამართლოს 30 დღის ვადაში."
        assert self._svc()._apply_deadline_guard(text) == text

    def test_untouched_without_action_advice(self):
        text = "ჯარიმა შეადგენს 50 ლარს."
        assert self._svc()._apply_deadline_guard(text) == text


class TestLaborClassification:
    """0.3 support: everyday labor phrasing must classify as labor."""

    def test_overtime_phrasing(self):
        from app.services.legal_classifier_service import KeywordClassifier
        r = KeywordClassifier().classify(
            "ყოველდღე ვმუშაობ 10 საათს, მაგრამ ზეგანაკვეთურს არ მიხდიან"
        )
        assert r.primary == "labor"
        assert r.confidence > 0.1

    def test_genitive_code_reference_phrasing(self):
        """Regression (agent-flow A2): genitive 'შრომის კოდექსის' must match
        labor. Before stemming 'შრომა'→'შრომ' this fell back to civil@0.1, which
        disabled the threshold domain gate and let criminal thresholds pollute a
        labor prompt (C8 fail)."""
        from app.services.legal_classifier_service import KeywordClassifier
        r = KeywordClassifier().classify(
            "მაინტერესებს შრომის კოდექსის მუხლი 48-ის ზუსტი ტექსტი — "
            "რას ამბობს კომპენსაციისა და სასამართლოსთვის მიმართვის ვადის შესახებ?"
        )
        assert r.primary == "labor"
        assert r.confidence > 0.1

    def test_locative_workplace_phrasing(self):
        """Stemmed roots match locative/genitive inflections ('სამსახურში',
        'ხელფასის', 'დამსაქმებელმა')."""
        from app.services.legal_classifier_service import KeywordClassifier
        r = KeywordClassifier().classify(
            "სამსახურში დამსაქმებელმა ხელფასის გადახდა შემიწყვიტა"
        )
        assert r.primary == "labor"


class TestLanguageFixups:
    def _svc(self):
        return AgentPipelineService(gemini=MagicMock(), citation_svc=MagicMock())

    def test_vs_replaced(self):
        with patch("app.services.agent_pipeline_service.record_step"):
            out = self._svc()._apply_language_fixups("კრიტიკა vs ცილისწამება")
        assert "vs" not in out

    def test_clean_text_untouched(self):
        text = "სუფთა ქართული ტექსტი."
        assert self._svc()._apply_language_fixups(text) == text

    def test_ascii_gloss_stripped(self):
        """Regression (agent-flow A1): model appended an English gloss
        '(Case Agent)' to a Georgian heading — C1 fail. The backstop strips
        pure-ASCII parenthetical glosses."""
        with patch("app.services.agent_pipeline_service.record_step"):
            out = self._svc()._apply_language_fixups(
                "### თქვენი საქმის მართვა (Case Agent)"
            )
        assert "Case" not in out and "Agent" not in out
        assert out.strip() == "### თქვენი საქმის მართვა"

    def test_matsne_url_paren_preserved(self):
        """The gloss stripper must NOT eat markdown/URL parentheticals."""
        text = "იხ. მუხლი 48 (https://matsne.gov.ge/ka/document/view/1155567#article_48)"
        assert self._svc()._apply_language_fixups(text) == text

    def test_georgian_paren_preserved(self):
        text = "კომპენსაცია 2000 (ორი ათასი) ლარი."
        assert self._svc()._apply_language_fixups(text) == text

    def test_case_enum_values_translated(self):
        """Regression (agent-flow A1): the case-agent echoes internal English
        enum values (favorable/high/…) into Georgian responses — C1 fail. The
        backstop translates them deterministically."""
        with patch("app.services.agent_pipeline_service.record_step"):
            out = self._svc()._apply_language_fixups(
                "დავამატე ფაქტი (კლასიფიკაცია: *favorable*), პრიორიტეტი: high."
            )
        assert "favorable" not in out and "high" not in out
        assert "ხელსაყრელი" in out and "მაღალი" in out

    def test_enum_substring_not_over_matched(self):
        """Word-boundary matching must not corrupt Georgian text or substrings."""
        text = "მოწმის ჩვენება მნიშვნელოვანია."  # no ASCII enum tokens
        assert self._svc()._apply_language_fixups(text) == text


class TestPracticeAttributionGuard:
    @pytest.mark.asyncio
    async def test_unattributed_practice_claim_corrected(self):
        gemini = MagicMock()
        gemini.generate = AsyncMock(return_value="პრაქტიკის თანახმად (საქმე №ას-543-2020) ...")
        svc = AgentPipelineService(gemini=gemini, citation_svc=MagicMock())
        chunks = [{"metadata": {"_collection": "court_practice", "case_id": "ას-543-2020"}}]
        with patch("app.services.agent_pipeline_service.record_step"):
            out = await svc._practice_attribution_guard(
                "სასამართლო პრაქტიკის თანახმად, ეს დაუშვებელია.", chunks
            )
        assert "ას-543-2020" in out

    @pytest.mark.asyncio
    async def test_already_attributed_untouched(self):
        gemini = MagicMock()
        gemini.generate = AsyncMock()
        svc = AgentPipelineService(gemini=gemini, citation_svc=MagicMock())
        text = "სასამართლო პრაქტიკის თანახმად (ას-543-2020), ეს დაუშვებელია."
        out = await svc._practice_attribution_guard(text, [])
        assert out == text
        gemini.generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_court_context_untouched(self):
        gemini = MagicMock()
        gemini.generate = AsyncMock()
        svc = AgentPipelineService(gemini=gemini, citation_svc=MagicMock())
        text = "სასამართლო პრაქტიკის თანახმად, ეს დაუშვებელია."
        out = await svc._practice_attribution_guard(text, [])
        assert out == text
        gemini.generate.assert_not_awaited()


class TestFaithfulnessPass:
    """2.3: seeded hallucination → flagged and corrected."""

    @pytest.mark.asyncio
    async def test_unsupported_claim_corrected(self):
        gemini = MagicMock()
        gemini.generate_json = AsyncMock(return_value={
            "supported_count": 3,
            "general_count": 1,
            "unsupported": [{"statement": "ჯარიმა არის 5000 ლარი", "reason": "amount not in context"}],
        })
        gemini.generate = AsyncMock(return_value="გასწორებული პასუხი")
        svc = AgentPipelineService(gemini=gemini, citation_svc=MagicMock())
        recorded = []
        with patch(
            "app.services.agent_pipeline_service.record_step",
            side_effect=lambda step, **kw: recorded.append((step, kw)),
        ):
            out = await svc._faithfulness_pass("ჯარიმა არის 5000 ლარი", [_law_chunk()])
        assert out == "გასწორებული პასუხი"
        steps = [s for s, _ in recorded]
        assert "faithfulness_check" in steps
        assert "faithfulness_correction" in steps

    @pytest.mark.asyncio
    async def test_all_supported_untouched(self):
        gemini = MagicMock()
        gemini.generate_json = AsyncMock(return_value={
            "supported_count": 4, "general_count": 2, "unsupported": [],
        })
        gemini.generate = AsyncMock()
        svc = AgentPipelineService(gemini=gemini, citation_svc=MagicMock())
        with patch("app.services.agent_pipeline_service.record_step"):
            out = await svc._faithfulness_pass("პასუხი", [_law_chunk()])
        assert out == "პასუხი"
        gemini.generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_check_failure_leaves_response(self):
        gemini = MagicMock()
        gemini.generate_json = AsyncMock(side_effect=RuntimeError("429"))
        svc = AgentPipelineService(gemini=gemini, citation_svc=MagicMock())
        with patch("app.services.agent_pipeline_service.record_step"):
            out = await svc._faithfulness_pass("პასუხი", [_law_chunk()])
        assert out == "პასუხი"
