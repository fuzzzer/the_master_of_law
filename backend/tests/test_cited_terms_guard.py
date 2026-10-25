"""
A deadline or amount in a cited article must reach the answer.

The bug this pins: answers that named the governing article and then left
its number out ("check the deadline in the decision") — the user asked "by
when?" and the article held the answer (2026-10-24 and 2026-10-25 runs).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_pipeline_service import AgentPipelineService
from app.services.citation_service import CitationService

ARTICLE = {
    "code_name": "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "article_number": "მუხლი 369",
    "content_ka": "1. სააპელაციო საჩივრის შეტანის ვადა არის 14 დღე. "
                  "2. ვადის დენა იწყება მხარისთვის დასაბუთებული გადაწყვეტილების ჩაბარების დღიდან.",
}
ANSWER = ("გადაწყვეტილება შეგიძლიათ გაასაჩივროთ სააპელაციო სასამართლოში "
          "(საქართველოს სამოქალაქო საპროცესო კოდექსი, მუხლი 369). ვადა გადაამოწმეთ გადაწყვეტილებაში.")


def _svc(repaired="გაასაჩივრეთ 14 დღის ვადაში (საქართველოს სამოქალაქო საპროცესო კოდექსი, მუხლი 369)."):
    gemini = MagicMock()
    gemini.generate = AsyncMock(return_value=repaired)
    return AgentPipelineService(gemini=gemini, citation_svc=CitationService()), gemini


def _store(article=ARTICLE):
    store = MagicMock()
    store.get_article = MagicMock(return_value=article)
    return store


async def _guard(svc, answer, question, store=None):
    with patch("app.services.article_store_service.get_article_store_service",
               return_value=store or _store()), \
         patch("app.services.agent_pipeline_service.record_step"):
        return await svc._cited_terms_guard(answer, question)


class TestTerms:
    def test_number_words_and_digits_are_the_same_term(self):
        terms = AgentPipelineService._terms_in
        assert terms("ერთი თვის ვადაში") == terms("1 თვე")
        assert terms("3 წლის") == terms("სამი წელი") == {("3", "წ")}
        assert terms("14-დღიანი") == {("14", "დღ")}
        assert terms("500 ლარი და 5%") == {("500", "ლარ"), ("5", "%")}


@pytest.mark.asyncio
async def test_a_missing_deadline_of_the_cited_article_is_added():
    svc, gemini = _svc()
    out = await _guard(svc, ANSWER, "რა ვადაში უნდა შევიტანო საჩივარი?")
    assert "14 დღის" in out
    prompt = gemini.generate.await_args.kwargs["prompt"]
    assert "„14 დღე\"" in prompt and "მუხლი 369" in prompt


@pytest.mark.asyncio
async def test_an_answer_that_states_the_term_is_left_alone():
    svc, gemini = _svc()
    answer = ANSWER + " საჩივრის ვადა თოთხმეტი დღეა."
    assert await _guard(svc, answer, "რა ვადაში?") == answer
    gemini.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_no_question_about_terms_and_no_advised_step_means_no_call():
    svc, gemini = _svc()
    answer = "ქონება თანასაკუთრებაა (საქართველოს სამოქალაქო საპროცესო კოდექსი, მუხლი 369)."
    assert await _guard(svc, answer, "ვისია ბინა?") == answer
    gemini.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_cited_article_without_terms_means_no_call():
    svc, gemini = _svc()
    no_terms = dict(ARTICLE, content_ka="საჩივარი შეიტანება წერილობით.")
    assert await _guard(svc, ANSWER, "რა ვადაში?", _store(no_terms)) == ANSWER
    gemini.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_an_editor_failure_keeps_the_answer():
    svc, gemini = _svc()
    gemini.generate = AsyncMock(side_effect=RuntimeError("503 UNAVAILABLE"))
    assert await _guard(svc, ANSWER, "რა ვადაში?") == ANSWER
