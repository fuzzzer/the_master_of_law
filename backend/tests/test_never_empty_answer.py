"""
A chat turn never ends with an empty answer.

The bug this pins: in the 2026-10-24/25 evaluations two answers came back
empty. The model spent all its lookup turns calling get_article and never
wrote a reply, and the pipeline returned "" (each cost about USD 0.40).
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.constants import COULD_NOT_COMPLETE_KA
from app.services import agent_pipeline_service as aps
from app.services.agent_pipeline_service import AgentPipelineService, PipelinePlan

ARTICLE = {
    "found": True,
    "code": "საქართველოს სამოქალაქო კოდექსი",
    "article": "მუხლი 1158",
    "content": "მეუღლეთა მიერ ქორწინების განმავლობაში შეძენილი ქონება მათი თანასაკუთრებაა.",
    "url": "https://matsne.gov.ge/ka/document/view/31702#article_1158",
}


def _tool_call_response():
    fc = MagicMock()
    fc.name = "get_article"
    fc.args = {"code": "civil_code", "article": "1158"}
    part = MagicMock()
    part.function_call = fc
    response = MagicMock()
    response.candidates = [MagicMock()]
    response.candidates[0].content.parts = [part]
    response.text = None
    return response


def _empty_response():
    response = MagicMock()
    response.candidates = []
    response.text = None
    return response


def _service(chat_response, forced_text):
    gemini = AsyncMock()
    chat = MagicMock()
    chat.send_message = AsyncMock(return_value=chat_response)
    gemini.create_chat = AsyncMock(return_value=chat)
    gemini.generate = AsyncMock(return_value=forced_text)
    rag = AsyncMock()
    rag.retrieve = AsyncMock(return_value=[{
        "chunk_id": "c1", "content": "კანონის ტექსტი",
        "metadata": {"_collection": "georgian_laws", "code_name": "სამოქალაქო კოდექსი",
                     "article_number": "მუხლი 1168"},
    }])
    svc = AgentPipelineService(gemini=gemini, rag=rag, citation_svc=MagicMock())
    svc._handle_get_article = AsyncMock(return_value=dict(ARTICLE))
    return svc, gemini, chat


async def _execute(svc):
    with patch.object(aps.settings, "full_code_injection", False):
        return await svc._phase_2_execute(
            plan=PipelinePlan(search_queries=["ქონების გაყოფა"]),
            user_message="ბინის ნახევარი მეკუთვნის?",
            system_prompt="SYSTEM",
            history=[],
            collections=None,
            case_file_id=None,
            user_id=None,
            conversation_id=None,
            db=None,
            redis_client=None,
            is_case_chat=False,
        )


@pytest.mark.asyncio
async def test_lookup_loop_running_out_forces_an_answer_from_gathered_sources():
    svc, gemini, chat = _service(_tool_call_response(), "საბოლოო პასუხი")

    text, _chunks, tool_results, _ = await _execute(svc)

    assert text == "საბოლოო პასუხი"
    assert chat.send_message.await_count == aps.MAX_TOOL_CALLS_PER_MESSAGE + 1
    prompt = gemini.generate.await_args.kwargs["prompt"]
    assert ARTICLE["content"] in prompt, "articles fetched by tools are the sources"
    assert "მუხლი 1168" in prompt, "retrieved articles are the sources too"
    assert "ბინის ნახევარი მეკუთვნის?" in prompt
    assert gemini.generate.await_args.kwargs["system_instruction"] == "SYSTEM"
    assert len(tool_results) == aps.MAX_TOOL_CALLS_PER_MESSAGE + 1


@pytest.mark.asyncio
async def test_model_returning_no_text_forces_an_answer():
    svc, gemini, _chat = _service(_empty_response(), "პასუხი")

    text, *_ = await _execute(svc)

    assert text == "პასუხი"
    gemini.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_a_normal_answer_makes_no_extra_call():
    response = _empty_response()
    response.text = "ჩვეულებრივი პასუხი"
    svc, gemini, _chat = _service(response, "unused")

    text, *_ = await _execute(svc)

    assert text == "ჩვეულებრივი პასუხი"
    gemini.generate.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("forced", ["", "   ", None])
async def test_nothing_at_all_returns_a_clear_could_not_complete_message(forced):
    svc, gemini, _chat = _service(_tool_call_response(), forced)
    plan = MagicMock()
    plan.text = json.dumps({"needs_rag": True, "search_queries": ["q"]})
    planner = MagicMock()
    planner.send_message = AsyncMock(return_value=plan)
    executor = await gemini.create_chat()
    gemini.create_chat = AsyncMock(side_effect=[planner, executor])

    with patch.object(aps.settings, "full_code_injection", False):
        result = await svc.run(user_message="ბინის ნახევარი მეკუთვნის?")

    assert result.response_text == COULD_NOT_COMPLETE_KA
    assert "ადვოკატ" in result.response_text


@pytest.mark.asyncio
async def test_a_provider_failure_on_the_forced_answer_keeps_its_own_message():
    """Quota or overload says more than "could not complete"; it propagates."""
    svc, gemini, _chat = _service(_tool_call_response(), "")
    gemini.generate = AsyncMock(side_effect=RuntimeError("429 RESOURCE_EXHAUSTED"))

    with pytest.raises(RuntimeError, match="RESOURCE_EXHAUSTED"):
        await _execute(svc)
