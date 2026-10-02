"""
A Georgian answer contains no letters of another script.

QA, 2026-10-01 (lite model): `задნებით` (Cyrillic inside a Georgian word),
`ακριβώς` (Greek), `მიեր` (an Armenian letter). These are model errors; the
check finds them so the pipeline records them and QA/eval reject them.
"""

import pytest

from app.utils.script_purity import foreign_script_words


@pytest.mark.parametrize("text, found", [
    ("ხელშეკრულების задნებით შეწყვეტა", ["задნებით"]),
    ("ეს ακριβώς ასეა", ["ακριβώς"]),
    # "მიერ" in Georgian, then with the Armenian ե and ր QA found: მი + ե + ր
    ("\u10db\u10d8\u10d4\u10e0 დაწერილი, \u10db\u10d8\u0565\u0580 დაწერილი", ["\u10db\u10d8\u0565\u0580"]),
])
def test_foreign_letters_in_a_georgian_answer_are_found(text, found):
    assert foreign_script_words(text) == found


@pytest.mark.parametrize("text", [
    "შრომის კოდექსის 48-ე მუხლი (matsne.gov.ge) — 30 დღე.",
    "Меня уволили — ответ на русском, как и вопрос.",
    "My landlord keeps the deposit — an English answer.",
])
def test_clean_text_and_answers_in_another_language_pass(text):
    assert foreign_script_words(text) == []


def test_the_pipeline_records_an_answer_with_foreign_letters():
    from unittest.mock import MagicMock, patch

    from app.services.agent_pipeline_service import AgentPipelineService

    recorded = []
    with patch("app.services.agent_pipeline_service.record_step",
               side_effect=lambda step, **kw: recorded.append((step, kw))):
        AgentPipelineService(gemini=MagicMock())._apply_language_fixups("ხელშეკრულების задნებით შეწყვეტა")

    assert ("foreign_script_detected", {"words": ["задნებით"]}) in recorded
