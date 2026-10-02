"""
Immediate danger gets 112 without waiting for — or depending on — a model.

Production, 2026-10-01: "ქმარი მცემს, ახლა სახლშია და მემუქრება. რა ვქნა?"
was answered with two quota errors and nothing about 112.
"""

import pytest

from app.utils.emergency import DangerKind, detect_immediate_danger


@pytest.mark.parametrize("message", [
    "ქმარი მცემს, ახლა სახლშია და მემუქრება. რა ვქნა?",      # the production message
    "ყოფილი ქმარი მემუქრება რომ მომკლავს",
    "მამა ისევ მირტყამს, სახლიდან ვერ გავდივარ",
    "ახლა კარს მიმტვრევს და ვშიშობ",
    "ქმარი ძალადობს ჩემზე და ბავშვებზე",
    "QMARI MCEMS ra vqna",                                    # Latin-script Georgian
    "qmari memuqreba rom momklavs",
    "My husband is beating me right now",
    "Муж бьёт меня, что делать?",
])
def test_violence_happening_now_gets_112_and_the_hotline(message):
    e = detect_immediate_danger(message)
    assert e is not None and e.kind is DangerKind.VIOLENCE
    assert "112" in e.reply_ka and "116 006" in e.reply_ka


@pytest.mark.parametrize("message", [
    "აღარ შემიძლია, თავს მოვიკლავ",
    "სიცოცხლე აღარ მინდა",
    "tavs moviklav",
    "I want to die",
])
def test_self_harm_gets_112(message):
    e = detect_immediate_danger(message)
    assert e is not None and e.kind is DangerKind.SELF_HARM
    assert "112" in e.reply_ka


@pytest.mark.parametrize("message", [
    "ქმარი მცემდა, როგორ განვქორწინდე?",                      # used to beat — past
    "ორი წლის წინ მცემა, შემიძლია ახლა ვუჩივლო?",             # beat me once — past
    "მემუქრებოდა სამსახურში, რა ვქნა?",                       # was threatening — past
    "რა სასჯელია ცემისთვის სისხლის სამართლის კოდექსით?",       # the offence, as a noun
    "რას ითვალისწინებს კანონი ოჯახში ძალადობის შესახებ?",
    "მუქარა დანაშაულია?",
    "ძმამ თავი მოიკლა, ვინ იღებს მემკვიდრეობას?",              # someone else, past — an inheritance question
])
def test_ordinary_legal_questions_are_not_emergencies(message):
    assert detect_immediate_danger(message) is None


def test_a_threat_to_sue_also_shows_the_numbers_which_is_the_safe_mistake():
    """'Threatens me' cannot be told apart from 'threatens to sue me' by a
    word list. Showing 112 under a debt question costs one paragraph; missing
    a real threat costs far more. The answer to the question still follows."""
    assert detect_immediate_danger("მეზობელი მემუქრება სასამართლოთი ვალის გამო") is not None


def test_every_reply_is_georgian_and_formal():
    for message in ("მცემს", "თავს მოვიკლავ"):
        reply = detect_immediate_danger(message).reply_ka
        assert any("ა" <= ch <= "ჰ" for ch in reply)
        assert "შენ " not in reply, "formal თქვენ, as everywhere else in the app"
