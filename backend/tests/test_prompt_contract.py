"""
What the prompts ask for is what the answers say.

QA, 2026-10-01: "success likelihood 85–90 %" / "95 %" in the case file and
case chat; English headings "SITUATION SUMMARY", "PROSECUTION'S LIKELY
ARGUMENTS" (in a civil labour case); "მზად ვარ საქმე გადავცე საქმის აგენტს";
თქვენ and შენ in one answer; a court-fee exemption the law does not grant.
Each traced to a prompt that asked for it — or never said otherwise.
"""

import re

import pytest

from app.prompts.advocate import compose_advocate_prompt
from app.prompts.case_builder import CASE_BUILDER
from app.prompts.chat import CASE_FULL_ANALYSIS, CASE_INTAKE_SYSTEM, CHAT_SYSTEM
from app.prompts.legal_analysis import LEGAL_ANALYSIS_SYSTEM

USER_FACING = {
    "chat": CHAT_SYSTEM.template,
    "case_intake": CASE_INTAKE_SYSTEM.template,
    "case_full_analysis": CASE_FULL_ANALYSIS.template,
    "legal_analysis": LEGAL_ANALYSIS_SYSTEM.template,
    "case_builder": CASE_BUILDER.template,
    "advocate": compose_advocate_prompt(case_file=None, is_case_chat=False),
}


@pytest.mark.parametrize("name", USER_FACING)
def test_no_prompt_asks_for_odds_and_each_forbids_invented_figures(name):
    text = USER_FACING[name]
    assert not re.search(r"success likelihood,", text), "asks for a success likelihood"
    assert "Never give a percentage" in text


@pytest.mark.parametrize("name", USER_FACING)
def test_every_prompt_fixes_the_formal_address(name):
    assert "თქვენ" in USER_FACING[name] and "never switch to შენ" in USER_FACING[name]


def test_the_case_file_strength_is_a_label_the_app_reads_not_a_percentage():
    field = re.search(r'"success_likelihood": "([^"]*)"', CASE_BUILDER.template).group(1)
    assert "მაღალი" in field and "საშუალო" in field and "დაბალი" in field
    assert "%" not in field


@pytest.mark.parametrize("template", [CASE_FULL_ANALYSIS.template, LEGAL_ANALYSIS_SYSTEM.template],
                         ids=["case_full_analysis", "legal_analysis"])
def test_section_headings_are_georgian_and_name_the_other_side(template):
    structure = template.split("RESPONSE STRUCTURE", 1)[1].split("FIGURES AND ODDS", 1)[0]
    headings = [line for line in structure.splitlines() if re.match(r"\s*\d+\.", line)]
    assert headings
    for h in headings:
        title = h.split("—")[0]
        assert not re.search(r"[A-Z]{3,}", title), h
    assert "PROSECUTION" not in template


def test_the_intake_never_tells_the_user_about_agents():
    assert "Agent" not in CASE_INTAKE_SYSTEM.template.replace("never mention agents", "")
    assert "never mention agents" in CASE_INTAKE_SYSTEM.template
