"""
Questionnaire service — AI-powered question generation for pre-analysis intake.

Generates domain-specific questions using Gemini, manages questionnaire lifecycle,
and builds enriched context from answers for the legal analysis pipeline.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.questionnaire_templates import get_domain_template
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.questionnaire import QUESTIONNAIRE_GENERATOR, NARRATIVE_EXTRACTOR
from app.repositories.questionnaire_repository import QuestionnaireRepository
from app.services.legal_classifier_service import LEGAL_DOMAINS
from app.utils.logger import get_logger

logger = get_logger(__name__)

_QUESTION_TYPES = {"text", "boolean", "choice", "date", "number"}
_MIN_QUESTIONS = 3
_MAX_QUESTIONS = 12


class QuestionnaireService:
    """Generates and manages AI-powered questionnaires per conversation."""

    def __init__(self, db: AsyncSession, gemini: VertexAIClient | None = None) -> None:
        self._repo = QuestionnaireRepository(db)
        self._gemini = gemini

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def generate_questionnaire(
        self,
        conversation_id: uuid.UUID,
        domain: str,
        user_description: str,
    ) -> dict[str, Any]:
        """Generate a questionnaire for a conversation using Gemini."""
        # Clear any previous questions (for regeneration)
        await self._repo.delete_questions(conversation_id)

        domain_name = LEGAL_DOMAINS.get(domain, domain)
        domain_template = get_domain_template(domain)

        prompt = QUESTIONNAIRE_GENERATOR.render(
            legal_domain=f"{domain} ({domain_name})",
            user_description=user_description,
            domain_template=domain_template,
        )

        raw_questions = await self.gemini.generate_json(
            prompt=prompt,
            temperature=QUESTIONNAIRE_GENERATOR.temperature,
        )

        questions = self._validate_questions(raw_questions)

        await self._repo.save_questions(conversation_id, questions)
        required_count = sum(1 for q in questions if q.get("required", True))

        logger.info(
            "questionnaire_generated",
            conversation_id=str(conversation_id),
            domain=domain,
            total=len(questions),
            required=required_count,
        )

        return {
            "questions": questions,
            "total": len(questions),
            "required_count": required_count,
        }

    async def get_questionnaire(
        self, conversation_id: uuid.UUID
    ) -> dict[str, Any]:
        """Get the current questionnaire state — questions, answers, progress."""
        questions = await self._repo.get_questions(conversation_id)
        answers = await self._repo.get_answers(conversation_id)

        answered_ids = {a.question_id for a in answers}

        question_list = []
        for q in questions:
            question_list.append({
                "question_id": q.question_id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "required": q.required,
                "purpose": q.purpose,
                "legal_relevance": q.legal_relevance,
            })

        answer_list = []
        for a in answers:
            answer_list.append({
                "question_id": a.question_id,
                "question_text": a.question_text,
                "answer_value": a.answer_value,
                "answer_type": a.answer_type,
                "skipped": a.skipped,
                "answered_at": a.answered_at.isoformat() if a.answered_at else "",
            })

        total = len(questions)
        answered = len([a for a in answers if not a.skipped])
        skipped = len([a for a in answers if a.skipped])

        return {
            "questions": question_list,
            "answers": answer_list,
            "progress": {
                "answered": answered,
                "skipped": skipped,
                "total": total,
                "remaining": total - len(answered_ids),
            },
        }

    async def process_answer(
        self,
        conversation_id: uuid.UUID,
        question_id: str,
        answer_value: str,
    ) -> dict[str, Any]:
        """Process a user's answer and return the next unanswered question."""
        questions = await self._repo.get_questions(conversation_id)
        question_map = {q.question_id: q for q in questions}

        target = question_map.get(question_id)
        if not target:
            return {"accepted": False, "error": "Question not found"}

        await self._repo.save_answer(
            conversation_id=conversation_id,
            question_id=question_id,
            question_text=target.question_text,
            answer_value=answer_value,
            answer_type=target.question_type,
        )

        # Find the next unanswered question
        answers = await self._repo.get_answers(conversation_id)
        answered_ids = {a.question_id for a in answers}

        next_question = None
        for q in questions:
            if q.question_id not in answered_ids:
                next_question = {
                    "question_id": q.question_id,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "options": q.options,
                    "required": q.required,
                    "purpose": q.purpose,
                    "legal_relevance": q.legal_relevance,
                }
                break

        return {
            "accepted": True,
            "next_question": next_question,
            "follow_ups": [],
        }

    async def skip_remaining(
        self, conversation_id: uuid.UUID
    ) -> dict[str, Any]:
        """Skip all remaining optional questions."""
        skipped_count = await self._repo.skip_remaining(conversation_id)
        all_required_answered = await self._all_required_answered(conversation_id)
        return {
            "skipped_count": skipped_count,
            "ready_for_analysis": all_required_answered,
        }

    async def should_ask_more(self, conversation_id: uuid.UUID) -> bool:
        """Check if there are critical unanswered required questions."""
        return not await self._all_required_answered(conversation_id)

    async def build_enriched_context(self, conversation_id: uuid.UUID) -> str:
        """Build a structured context string from answered questions for analysis."""
        answers = await self._repo.get_answers(conversation_id)
        parts = []
        for a in answers:
            if a.skipped or not a.answer_value:
                continue
            parts.append(f"**{a.question_text}**\n{a.answer_value}")
        return "\n\n".join(parts)

    async def extract_from_narrative(
        self,
        conversation_id: uuid.UUID,
        domain: str,
        narrative: str,
    ) -> dict[str, Any]:
        """Extract structured answers from a free-text narrative using Gemini.

        Generates question templates, then asks Gemini to find answers
        in the user's narrative. Saves whatever it can extract.
        """
        await self._repo.delete_questions(conversation_id)

        domain_name = LEGAL_DOMAINS.get(domain, domain)
        domain_template = get_domain_template(domain)

        # First generate the questions (reuse existing logic)
        gen_prompt = QUESTIONNAIRE_GENERATOR.render(
            legal_domain=f"{domain} ({domain_name})",
            user_description=narrative,
            domain_template=domain_template,
        )
        raw_questions = await self.gemini.generate_json(
            prompt=gen_prompt,
            temperature=QUESTIONNAIRE_GENERATOR.temperature,
        )
        questions = self._validate_questions(raw_questions)
        await self._repo.save_questions(conversation_id, questions)

        # Now extract answers from the narrative
        extract_prompt = NARRATIVE_EXTRACTOR.render(
            legal_domain=f"{domain} ({domain_name})",
            narrative=narrative,
            domain_template=domain_template,
        )
        raw_extracted = await self.gemini.generate_json(
            prompt=extract_prompt,
            temperature=NARRATIVE_EXTRACTOR.temperature,
        )

        extracted_answers = self._process_extracted(raw_extracted, questions)

        # Save extracted answers
        for ans in extracted_answers:
            await self._repo.save_answer(
                conversation_id=conversation_id,
                question_id=ans["question_id"],
                question_text=ans["question_text"],
                answer_value=ans["answer_value"],
                answer_type=ans["answer_type"],
            )

        extracted_count = len(extracted_answers)
        total = len(questions)

        logger.info(
            "narrative_extracted",
            conversation_id=str(conversation_id),
            domain=domain,
            extracted=extracted_count,
            total=total,
        )

        return {
            "extracted_count": extracted_count,
            "total_questions": total,
            "questions": questions,
            "extracted_answers": extracted_answers,
        }

    async def _all_required_answered(self, conversation_id: uuid.UUID) -> bool:
        questions = await self._repo.get_questions(conversation_id)
        answers = await self._repo.get_answers(conversation_id)
        answered_ids = {a.question_id for a in answers if not a.skipped}

        for q in questions:
            if q.required and q.question_id not in answered_ids:
                return False
        return True

    @staticmethod
    def _validate_questions(raw: Any) -> list[dict]:
        """Validate and sanitize Gemini-generated questions."""
        if not isinstance(raw, list):
            raw = [raw] if isinstance(raw, dict) else []

        validated = []
        for q in raw:
            if not isinstance(q, dict):
                continue
            if "question_id" not in q or "question_text" not in q:
                continue

            q_type = q.get("question_type", "text")
            if q_type not in _QUESTION_TYPES:
                q_type = "text"

            validated.append({
                "question_id": str(q["question_id"]),
                "question_text": str(q["question_text"]),
                "question_type": q_type,
                "options": q.get("options") if q_type == "choice" else None,
                "required": bool(q.get("required", True)),
                "purpose": q.get("purpose"),
                "legal_relevance": q.get("legal_relevance"),
            })

        # Enforce min/max bounds
        if len(validated) < _MIN_QUESTIONS:
            logger.warning("questionnaire_too_few_questions", count=len(validated))
        validated = validated[:_MAX_QUESTIONS]

        return validated

    @staticmethod
    def _process_extracted(raw: Any, questions: list[dict]) -> list[dict]:
        """Validate extracted answers against the question list."""
        if not isinstance(raw, list):
            raw = [raw] if isinstance(raw, dict) else []

        question_map = {q["question_id"]: q for q in questions}
        extracted = []

        for item in raw:
            if not isinstance(item, dict):
                continue
            q_id = item.get("question_id")
            answer = item.get("answer_value")
            if not q_id or answer is None or str(answer).lower() == "null":
                continue
            if q_id not in question_map:
                continue

            q = question_map[q_id]
            extracted.append({
                "question_id": q_id,
                "question_text": q["question_text"],
                "answer_value": str(answer),
                "answer_type": q.get("question_type", "text"),
            })

        return extracted
