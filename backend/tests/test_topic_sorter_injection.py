"""
A mention of work must not turn a question into a Labour Code question.

The bug this pins: a divorcing couple's flat "bought with our salaries" was
sorted as labour law because of the words for work and salary. The whole
Labour Code (about 75k tokens) was injected, every other retrieved law was
dropped, the model looped on lookups with the code resent each round, and the
answer came back empty at a cost of about USD 0.40.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import agent_pipeline_service as aps
from app.services.agent_pipeline_service import AgentPipelineService, PipelinePlan
from app.services.legal_classifier_service import KeywordClassifier

LABOUR_URL = "https://matsne.gov.ge/ka/document/view/1155567#article_47"
CIVIL_URL = "https://matsne.gov.ge/ka/document/view/31702#article_1158"
FAKE_LABOUR_CODE = f"მუხლი 47. შრომითი ხელშეკრულების შეწყვეტა\nURL: {LABOUR_URL}\nტექსტი"


def _fake_store():
    store = MagicMock()
    store.get_code_full_text = MagicMock(return_value=(FAKE_LABOUR_CODE, 1))
    return store


class TestClassifier:
    def test_family_words_match_in_their_inflected_forms(self):
        r = KeywordClassifier().classify("ქმრის სახელზეა ბინა, ქორწინების დროს ვიყიდეთ")
        assert r.primary == "family"

    def test_work_and_family_together_is_not_labour_only(self):
        r = KeywordClassifier().classify(
            "მე და ჩემი მეუღლე ორივე ვმუშაობდით და ხელფასით ბინა ვიყიდეთ, ახლა ვშორდებით"
        )
        assert "family" in {r.primary, *r.secondary}


class TestInjection:
    @pytest.mark.asyncio
    async def test_mixed_family_and_work_question_injects_no_code(self, monkeypatch):
        monkeypatch.setattr(aps.settings, "full_code_injection", True)
        store = _fake_store()
        with patch("app.services.article_store_service.get_article_store_service",
                   return_value=store):
            text = await AgentPipelineService()._build_full_code_context(
                "ქორწინების დროს ორივე ვმუშაობდით, ხელფასით ბინა ვიყიდეთ, ქმრის სახელზეა"
            )
        assert text == ""
        store.get_code_full_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_plain_labour_question_still_gets_the_labour_code(self, monkeypatch):
        monkeypatch.setattr(aps.settings, "full_code_injection", True)
        with patch("app.services.article_store_service.get_article_store_service",
                   return_value=_fake_store()):
            text = await AgentPipelineService()._build_full_code_context(
                "დამსაქმებელმა სამსახურიდან გამათავისუფლა და ხელფასი არ მომცა"
            )
        assert text == FAKE_LABOUR_CODE

    def test_only_the_injected_codes_chunks_are_dropped(self):
        def chunk(url, collection="georgian_laws"):
            return {"metadata": {"_collection": collection, "article_url": url}}

        drop = AgentPipelineService._chunk_in_injected_code
        assert drop(chunk(LABOUR_URL), FAKE_LABOUR_CODE)
        assert not drop(chunk(CIVIL_URL), FAKE_LABOUR_CODE)
        assert not drop(chunk(""), FAKE_LABOUR_CODE)
        assert not drop(chunk(LABOUR_URL, "court_practice"), FAKE_LABOUR_CODE)


@pytest.mark.asyncio
async def test_with_a_whole_code_injected_lookups_are_capped(monkeypatch):
    """Each lookup round resends the whole code; two rounds, then answer."""
    monkeypatch.setattr(aps.settings, "full_code_injection", True)
    fc = MagicMock()
    fc.name = "get_article"
    fc.args = {"code": "labour_code", "article": "47"}
    part = MagicMock()
    part.function_call = fc
    looping = MagicMock()
    looping.candidates = [MagicMock()]
    looping.candidates[0].content.parts = [part]
    looping.text = None

    gemini = AsyncMock()
    chat = MagicMock()
    chat.send_message = AsyncMock(return_value=looping)
    gemini.create_chat = AsyncMock(return_value=chat)
    gemini.generate = AsyncMock(return_value="პასუხი")
    rag = AsyncMock()
    rag.retrieve = AsyncMock(return_value=[
        {"chunk_id": "l", "content": "შრომის", "metadata": {"_collection": "georgian_laws", "article_url": LABOUR_URL}},
        {"chunk_id": "c", "content": "სამოქალაქო", "metadata": {"_collection": "georgian_laws", "article_url": CIVIL_URL}},
    ])
    svc = AgentPipelineService(gemini=gemini, rag=rag, citation_svc=MagicMock())
    svc._handle_get_article = AsyncMock(return_value={"found": True, "content": "x"})

    with patch("app.services.article_store_service.get_article_store_service",
               return_value=_fake_store()):
        text, chunks, _tools, injected = await svc._phase_2_execute(
            plan=PipelinePlan(search_queries=["q"]),
            user_message="დამსაქმებელმა სამსახურიდან გამათავისუფლა",
            system_prompt="", history=[], collections=None, case_file_id=None,
            user_id=None, conversation_id=None, db=None, redis_client=None,
            is_case_chat=False,
        )

    assert injected is True
    assert chat.send_message.await_count == aps.MAX_TOOL_CALLS_WITH_FULL_CODE + 1
    assert [c["chunk_id"] for c in chunks] == ["c"], "the Civil Code chunk stays"
    assert text == "პასუხი"
