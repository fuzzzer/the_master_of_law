"""
"Court practice says" must name a real case from the retrieved rulings.

The bug this pins: in the 2026-10-24 evaluation 11 of 39 court answers said
"according to court practice" with no case named, one of them contradicting
Civil Code art. 138. The old guard ran only when rulings were in context and
let any case number anywhere in the answer excuse every sentence.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.constants import PRACTICE_CLAIM_REMOVED_KA
from app.services.agent_pipeline_service import AgentPipelineService

A = AgentPipelineService
COURT = [{"metadata": {"_collection": "court_practice", "case_id": "ას-543-2020"}}]


class TestDetection:
    @pytest.mark.parametrize("sentence", [
        "სასამართლო პრაქტიკის თანახმად, ასეთი განცხადება ვადას არ წყვეტს.",
        "საქართველოს უზენაესი სასამართლოს დამკვიდრებული განმარტებით, ვადა არ წყდება.",
        "უზენაესმა სასამართლომ არაერთხელ განმარტა, რომ ასეთი ქმედება არაკეთილსინდისიერია.",
        "ასეთი დაყოვნება სასამართლო პრაქტიკაში განიხილება არაკეთილსინდისიერ ქმედებად.",
        "საკასაციო პალატის მიდგომით, მტკიცების ტვირთი მოსარჩელეზეა.",
    ])
    def test_unnamed_practice_claims_are_found(self, sentence):
        assert A._unsourced_practice_sentences(f"შესავალი. {sentence} დასკვნა.", []) == [sentence]

    def test_a_case_in_context_named_in_the_same_sentence_sources_it(self):
        text = "სასამართლო პრაქტიკის თანახმად (საქმე №ას-543-2020), ეს დაუშვებელია."
        assert A._unsourced_practice_sentences(text, ["ას-543-2020"]) == []

    def test_a_case_elsewhere_in_the_answer_does_not_excuse_the_sentence(self):
        text = ("საქმე №ას-543-2020 ეხება სხვა საკითხს. "
                "სასამართლო პრაქტიკის თანახმად, ეს დაუშვებელია.")
        assert A._unsourced_practice_sentences(text, ["ას-543-2020"]) == [
            "სასამართლო პრაქტიკის თანახმად, ეს დაუშვებელია."
        ]

    def test_a_case_number_not_in_the_retrieved_rulings_is_not_a_source(self):
        text = "სასამართლო პრაქტიკის თანახმად (ას-999-2021), ეს დაუშვებელია."
        assert A._unsourced_practice_sentences(text, ["ას-543-2020"]) == [text]

    def test_quoting_the_cassation_grounds_is_not_a_claim(self):
        text = "საჩივარი დასაშვებია, თუ საქმე ერთგვაროვანი სასამართლო პრაქტიკის ჩამოყალიბებისთვისაა მნიშვნელოვანი."
        assert A._unsourced_practice_sentences(text, []) == []

    def test_predicting_the_users_own_case_is_not_a_practice_claim(self):
        text = "უზენაესი სასამართლო სავარაუდოდ არ დააკმაყოფილებს საჩივარს."
        assert A._unsourced_practice_sentences(text, []) == []

    def test_links_do_not_split_sentences(self):
        text = ("[მუხლი 138](https://matsne.gov.ge/ka/document/view/31702#article_138) "
                "და სასამართლო პრაქტიკის თანახმად ვადა წყდება.")
        assert A._unsourced_practice_sentences(text, []) == [text]


class TestGuard:
    def _svc(self, repaired):
        gemini = MagicMock()
        gemini.generate = AsyncMock(return_value=repaired)
        return AgentPipelineService(gemini=gemini, citation_svc=MagicMock()), gemini

    @pytest.mark.asyncio
    async def test_claim_left_unsourced_after_repair_is_removed_and_flagged(self):
        text = ("მუხლი 138 ამბობს, რომ სახელმწიფო ორგანოსთვის მიმართვა ვადას წყვეტს.\n"
                "- სასამართლო პრაქტიკის თანახმად, პროკურატურაში განცხადება ვადას არ წყვეტს.\n"
                "დასკვნა: ვადა შეწყვეტილია.")
        svc, _ = self._svc(text)  # the editor pass changed nothing
        with patch("app.services.agent_pipeline_service.record_step"):
            out = await svc._practice_attribution_guard(text, [])
        assert "პრაქტიკ" not in out.replace(PRACTICE_CLAIM_REMOVED_KA, "")
        assert out.endswith(PRACTICE_CLAIM_REMOVED_KA)
        assert "მუხლი 138 ამბობს" in out and "დასკვნა: ვადა შეწყვეტილია." in out
        assert "\n- \n" not in out and "\n-\n" not in out
        assert A._unsourced_practice_sentences(out, []) == [], "the note makes no claim itself"

    @pytest.mark.asyncio
    async def test_editor_failure_still_removes_the_claim(self):
        svc, gemini = self._svc("")
        gemini.generate = AsyncMock(side_effect=RuntimeError("503 UNAVAILABLE"))
        text = "პასუხი. სასამართლო პრაქტიკის თანახმად, ეს დაუშვებელია."
        with patch("app.services.agent_pipeline_service.record_step"):
            out = await svc._practice_attribution_guard(text, COURT)
        assert out == "პასუხი." + PRACTICE_CLAIM_REMOVED_KA

    @pytest.mark.asyncio
    async def test_no_claim_means_no_model_call(self):
        svc, gemini = self._svc("unused")
        text = "მუხლი 138-ის თანახმად, ვადა წყდება."
        assert await svc._practice_attribution_guard(text, []) == text
        gemini.generate.assert_not_awaited()
