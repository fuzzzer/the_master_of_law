"""
Immediate-danger detection — the one answer that must not depend on a model.

WHY: production, 2026-10-01. "ქმარი მცემს, ახლა სახლშია და მემუქრება. რა
ვქნა?" got two quota errors and nothing else. Whether a person in danger
learned to call 112 depended on a model call succeeding on their free key.

This is deliberately a phrase list, not a classifier: it runs before every
model call, costs nothing, and cannot fail. It matches PRESENT-tense,
first-person danger ("მცემს" — he is beating me) and leaves the past alone
("მცემდა", "მცემა" — he used to / he beat me), because a legal question about
something that happened is not an emergency and must not be answered as one.

Numbers verified 2026-10-02 against the State's emergency service,
https://112.gov.ge/?page_id=7650&lang=en — "Call emergency center 112";
"24 hours hotline number – 116006 (24/7). (You can stay anonymous)".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class DangerKind(str, Enum):
    VIOLENCE = "violence"      # violence or threats happening now
    SELF_HARM = "self_harm"    # the writer may harm themselves


@dataclass(frozen=True)
class Emergency:
    kind: DangerKind
    reply_ka: str


_VIOLENCE_REPLY_KA = (
    "თუ ახლა საფრთხეში ხართ, დაუყოვნებლივ დარეკეთ 112-ზე — ზარი უფასოა და "
    "სამსახური მუშაობს 24 საათის განმავლობაში. ოჯახში ძალადობის შემთხვევაში "
    "კონსულტაციას გაგიწევენ ცხელ ხაზზე 116 006 — უფასოდ, ანონიმურად, "
    "დღე-ღამის ნებისმიერ დროს."
)
_SELF_HARM_REPLY_KA = (
    "თუ საკუთარი თავისთვის ზიანის მიყენებაზე ფიქრობთ, ახლავე დარეკეთ 112-ზე — "
    "ზარი უფასოა და სამსახური მუშაობს 24 საათის განმავლობაში — ან დაუკავშირდით "
    "ადამიანს, ვისაც ენდობით. თქვენ მარტო არ ხართ."
)

# Whole words or phrases, matched case-insensitively on word boundaries.
# Georgian first, then Latin-script Georgian as people type it, then the
# other languages the app is asked in.
_VIOLENCE_PHRASES = (
    # he/she is beating / hitting / choking me, threatens me, will kill me
    "მცემს", "მირტყამს", "მახრჩობს", "მემუქრება", "გვემუქრება",
    "მომკლავს", "მოგვკლავს", "მკლავს", "მეძალადება", "ძალადობს ჩემზე",
    "დანით დამდევს", "იარაღით მემუქრება", "კარს მიმტვრევს",
    "mcems", "mtsems", "mirtyams", "makhrchobs", "maxrchobs",
    "memuqreba", "memukreba", "momklavs", "medzaladeba",
    "is beating me", "is hitting me", "is choking me", "threatening to kill",
    "going to kill me", "will kill me",
    "бьёт меня", "бьет меня", "избивает меня", "душит меня",
    "угрожает убить", "убьёт меня", "убьет меня",
)
_SELF_HARM_PHRASES = (
    # I will kill myself, I want to die, I don't want to live any more
    "თავს მოვიკლავ", "თავს ვიკლავ", "თავის მოკვლა მინდა", "მინდა მოვკვდე",
    "სიცოცხლე აღარ მინდა", "აღარ მინდა ცხოვრება",
    "tavs moviklav", "minda movkvde", "sicocxle agar minda",
    "kill myself", "want to die", "end my life",
    "убью себя", "покончу с собой", "хочу умереть", "не хочу жить",
)


def _compile(phrases: tuple[str, ...]) -> re.Pattern[str]:
    alternatives = "|".join(
        r"\s+".join(map(re.escape, p.split())) for p in sorted(phrases, key=len, reverse=True)
    )
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)


_VIOLENCE_RE = _compile(_VIOLENCE_PHRASES)
_SELF_HARM_RE = _compile(_SELF_HARM_PHRASES)


def detect_immediate_danger(message: str) -> Emergency | None:
    """The emergency reply for a message that signals danger now, else None."""
    if _SELF_HARM_RE.search(message):
        return Emergency(DangerKind.SELF_HARM, _SELF_HARM_REPLY_KA)
    if _VIOLENCE_RE.search(message):
        return Emergency(DangerKind.VIOLENCE, _VIOLENCE_REPLY_KA)
    return None
