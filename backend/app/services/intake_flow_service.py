"""
Intake flow service — guided question flow to extract facts before legal analysis.

A structured question flow that gathers all necessary information
before triggering the RAG pipeline. The service is smart enough to
skip questions already answered in the initial description.
"""

from __future__ import annotations

from typing import Any

from app.config.constants import ConversationPhase
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Structured intake questions in Georgian with English translations
INTAKE_QUESTIONS: list[dict[str, str]] = [
    {
        "id": "what_happened",
        "question_ka": "რა მოხდა? მოკლედ აღწერეთ სიტუაცია.",
        "question_en": "What happened? Briefly describe the situation.",
        "key_topics": ["event", "incident", "action", "problem"],
    },
    {
        "id": "when",
        "question_ka": "როდის მოხდა ეს? (თარიღი ან მიახლოებითი დრო)",
        "question_en": "When did this happen? (date or approximate time)",
        "key_topics": ["date", "time", "when", "ago"],
    },
    {
        "id": "where",
        "question_ka": "სად მოხდა? (ქალაქი, რეგიონი)",
        "question_en": "Where did it happen? (city, region)",
        "key_topics": ["location", "city", "place", "address"],
    },
    {
        "id": "who",
        "question_ka": "ვინ არის ჩართული? (მხარეები, ორგანიზაციები)",
        "question_en": "Who is involved? (parties, organizations)",
        "key_topics": ["person", "party", "company", "organization", "police"],
    },
    {
        "id": "documents",
        "question_ka": "არის თუ არა რაიმე დოკუმენტი ან ხელშეკრულება?",
        "question_en": "Is there any document or contract involved?",
        "key_topics": ["document", "contract", "agreement", "paper", "evidence"],
    },
    {
        "id": "desired_outcome",
        "question_ka": "რა შედეგს ელოდებით? რა გინდათ რომ მოხდეს?",
        "question_en": "What outcome do you expect? What do you want to happen?",
        "key_topics": ["want", "expect", "outcome", "goal", "result"],
    },
]


class IntakeFlowService:
    """
    Manages the structured intake question flow.

    Tracks which questions have been asked/answered and determines
    the next question to ask or whether intake is complete.
    """

    def get_intake_questions(self) -> list[dict[str, str]]:
        """Return the list of intake questions."""
        return INTAKE_QUESTIONS

    def get_next_question(
        self,
        answered_ids: list[str],
        user_message: str = "",
    ) -> dict[str, str] | None:
        """
        Determine the next intake question to ask.

        Skips questions that have already been answered or that appear
        to be addressed in the user's initial description.

        Returns None when all questions have been asked.
        """
        for q in INTAKE_QUESTIONS:
            if q["id"] in answered_ids:
                continue

            # Simple heuristic: if the user's message seems to cover this topic,
            # mark it as implicitly answered
            if user_message and self._message_covers_topic(user_message, q):
                continue

            return q

        return None  # All questions covered

    def is_intake_complete(
        self,
        answered_ids: list[str],
        user_message: str = "",
    ) -> bool:
        """Check if enough information has been gathered for analysis."""
        # At minimum, we need the situation description (what_happened)
        if "what_happened" not in answered_ids and not user_message:
            return False

        # Check how many questions are effectively answered
        answered_count = len(answered_ids)
        if user_message:
            for q in INTAKE_QUESTIONS:
                if q["id"] not in answered_ids and self._message_covers_topic(user_message, q):
                    answered_count += 1

        # Consider intake complete when at least 3 questions are covered
        # (what happened + 2 details), or user has provided a detailed description
        return answered_count >= 3 or len(user_message) > 200

    def build_intake_summary(
        self,
        answers: dict[str, str],
    ) -> str:
        """
        Build a structured summary from intake answers.

        Used as context for the RAG pipeline and Gemini analysis.
        """
        parts = []
        for q in INTAKE_QUESTIONS:
            answer = answers.get(q["id"])
            if answer:
                parts.append(f"**{q['question_en']}**\n{answer}")

        return "\n\n".join(parts) if parts else ""

    def format_question_for_user(
        self,
        question: dict[str, str],
        language: str = "ka",
    ) -> str:
        """Format a question for display to the user."""
        if language == "en":
            return question.get("question_en", "")
        return question.get("question_ka", "")

    @staticmethod
    def _message_covers_topic(message: str, question: dict[str, str]) -> bool:
        """
        Simple heuristic to check if a message covers a question's topic.

        This is a basic keyword check — in production, this could use
        Gemini to make smarter determinations.
        """
        msg_lower = message.lower()
        key_topics = question.get("key_topics", [])

        # Check if any key topic words appear in the message
        matches = sum(1 for topic in key_topics if topic in msg_lower)
        return matches >= 1
