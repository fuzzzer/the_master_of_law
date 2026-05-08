"""
Questionnaire service — dynamic, AI-generated intake questions.

Replaces the static IntakeFlowService with domain-specific question
 generation powered by Gemini.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import GEMINI_MAX_OUTPUT_TOKENS
from app.config.questionnaire_templates import get_domain_template
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.questionnaire import FOLLOW_UP_GENERATOR, QUESTIONNAIRE_GENERATOR
from app.repositories.questionnaire_repository import QuestionnaireRepository
from app.services.conversation_service import ConversationService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Limits per spec
MIN_QUESTIONS = 3
MAX_QUESTIONS = 12
DEFAULT_REQUIRED_COUNT = 5


class QuestionnaireService:
    """
    Generates and manages dynamic questionnaires for legal intake.

    - generate_questionnaire: creates domain-specific questions via Gemini
    - process_answers: stores answers and optionally generates follow-ups
    - should_ask_more: determines if the questionnaire is complete
    """

    def __init__(
        self,
        db: AsyncSession,
        gemini_client: VertexAIClient | None = None,
    ) -> None:
        self._db = db
        self._repo = QuestionnaireRepository(db)
        self._gemini = gemini_client

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    # ── Public API ──────────────────────────────────────────────

    async def generate_questionnaire(
        self,
        conversation_id: str,
        domain: str,
        context: str = "",
    ) -> list[dict[str, Any]]:
        """
        Generate a domain-specific questionnaire for a conversation.

        1. Fetches conversation history for context.
        2. Loads the baseline template for the domain.
        3. Calls Gemini to generate adapted questions.
        4. Validates and stores questions in DB.
        5. Returns the ordered list of questions.
        """
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            raise ValueError(f"Invalid conversation_id: {conversation_id}")

        # Clear any existing questionnaire items for this conversation
        await self._repo.delete_items_for_conversation(conv_uuid)

        # Fetch conversation history
        conv_svc = ConversationService(self._db)
        history = await conv_svc.get_conversation_history(conversation_id, max_messages=10)
        history_text = self._format_history(history)

        # Load baseline template
        template = get_domain_template(domain)
        if template is None:
            template = get_domain_template("civil")  # fallback

        template_questions_text = self._format_template_questions(template.questions if template else [])
        domain_name_ka = template.domain_name_ka if template else "სამოქალაქო სამართალი"

        # Build Gemini prompt
        prompt = QUESTIONNAIRE_GENERATOR.render(
            domain_key=domain,
            domain_name_ka=domain_name_ka,
            user_description=context,
            conversation_history=history_text,
            template_questions=template_questions_text,
            max_questions=MAX_QUESTIONS,
            required_count=DEFAULT_REQUIRED_COUNT,
        )

        # Call Gemini
        try:
            raw_questions = await self.gemini.generate_json(
                prompt=prompt,
                temperature=QUESTIONNAIRE_GENERATOR.temperature,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            )
        except Exception as e:
            logger.error("questionnaire_generation_failed", error=str(e), conversation_id=conversation_id)
            # Fallback to baseline template
            raw_questions = [q.to_dict() for q in (template.questions if template else [])]

        # Validate and normalize
        questions = self._normalize_questions(raw_questions)
        if len(questions) < MIN_QUESTIONS:
            # Pad with template questions if Gemini returned too few
            existing_ids = {q["question_id"] for q in questions}
            if template:
                for tq in template.questions:
                    if tq.question_id not in existing_ids:
                        questions.append(tq.to_dict())
                    if len(questions) >= MIN_QUESTIONS:
                        break

        # Enforce max
        questions = questions[:MAX_QUESTIONS]

        # Store in DB
        await self._repo.create_items(conv_uuid, questions)

        logger.info(
            "questionnaire_generated",
            conversation_id=conversation_id,
            domain=domain,
            question_count=len(questions),
        )
        return questions

    async def process_answer(
        self,
        conversation_id: str,
        question_id: str,
        answer: str,
    ) -> dict[str, Any]:
        """
        Store a user's answer and determine next steps.

        Returns:
            {
                "accepted": bool,
                "next_question": QuestionSchema | None,
                "follow_ups": list[QuestionSchema],
                "progress": {"answered": int, "total": int},
            }
        """
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            raise ValueError(f"Invalid conversation_id: {conversation_id}")

        # Save answer
        item = await self._repo.save_answer(conv_uuid, question_id, answer)
        if item is None:
            raise ValueError(f"Question {question_id} not found in conversation {conversation_id}")

        # Get current progress
        answered, total = await self._repo.count_answered(conv_uuid)
        progress = {"answered": answered, "total": total}

        # Determine next unanswered question
        items = await self._repo.get_items_for_conversation(conv_uuid)
        next_q = None
        for it in items:
            if it.answer_value is None and not it.skipped:
                next_q = it.to_dict()
                break

        # Generate follow-ups if this answer reveals new info
        follow_ups: list[dict] = []
        if next_q is None or len(items) < MAX_QUESTIONS:
            follow_ups = await self._maybe_generate_follow_ups(
                conversation_id=conversation_id,
                question_id=question_id,
                answer=answer,
                items=items,
            )
            if follow_ups:
                # Append follow-ups to DB
                await self._repo.create_items(conv_uuid, follow_ups)
                total += len(follow_ups)
                progress["total"] = total
                # Re-evaluate next question
                if next_q is None:
                    items = await self._repo.get_items_for_conversation(conv_uuid)
                    for it in items:
                        if it.answer_value is None and not it.skipped:
                            next_q = it.to_dict()
                            break

        logger.info(
            "questionnaire_answer_processed",
            conversation_id=conversation_id,
            question_id=question_id,
            progress=progress,
        )

        return {
            "accepted": True,
            "next_question": next_q,
            "follow_ups": follow_ups,
            "progress": progress,
        }

    async def skip_question(
        self,
        conversation_id: str,
        question_id: str,
    ) -> dict[str, Any]:
        """
        Mark a question as skipped (only allowed for non-required questions).

        Returns progress and whether questionnaire is complete.
        """
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            raise ValueError(f"Invalid conversation_id: {conversation_id}")

        item = await self._repo.get_item_by_question_id(conv_uuid, question_id)
        if item is None:
            raise ValueError(f"Question {question_id} not found")
        if item.required:
            raise ValueError("Cannot skip a required question")

        await self._repo.skip_question(conv_uuid, question_id)
        answered, total = await self._repo.count_answered(conv_uuid)

        ready = self._is_complete(answered, total)
        return {
            "skipped_count": 1,
            "ready_for_analysis": ready,
            "progress": {"answered": answered, "total": total},
        }

    async def should_ask_more(self, conversation_id: str) -> bool:
        """Return True if there are unanswered questions remaining."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return False

        items = await self._repo.get_items_for_conversation(conv_uuid)
        if not items:
            return True  # No questionnaire generated yet

        answered, total = await self._repo.count_answered(conv_uuid)
        return not self._is_complete(answered, total)

    async def get_questionnaire_state(
        self,
        conversation_id: str,
    ) -> dict[str, Any]:
        """Get the full questionnaire state for a conversation."""
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            raise ValueError(f"Invalid conversation_id: {conversation_id}")

        items = await self._repo.get_items_for_conversation(conv_uuid)
        questions = [it.to_dict() for it in items]
        answers = [
            {"question_id": it.question_id, "answer": it.answer_value}
            for it in items
            if it.answer_value is not None
        ]
        answered, total = await self._repo.count_answered(conv_uuid)

        return {
            "questions": questions,
            "answers": answers,
            "progress": {"answered": answered, "total": total},
        }

    async def build_enriched_context(self, conversation_id: str) -> str:
        """
        Build a structured summary from questionnaire answers.

        This summary is injected into the RAG pipeline and legal analysis.
        """
        conv_uuid = self._parse_uuid(conversation_id)
        if not conv_uuid:
            return ""

        items = await self._repo.get_items_for_conversation(conv_uuid)
        parts = []
        for it in items:
            if it.answer_value:
                parts.append(f"**{it.question_text_ka}**\n{it.answer_value}")

        return "\n\n".join(parts) if parts else ""

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _parse_uuid(value: str) -> uuid.UUID | None:
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _format_history(history: list[dict[str, str]]) -> str:
        if not history:
            return "(საუბარი არ არის)"
        lines = []
        for msg in history:
            role = "მომხმარებელი" if msg.get("role") == "user" else "AI"
            lines.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(lines)

    @staticmethod
    def _format_template_questions(questions: tuple) -> str:
        if not questions:
            return "(შაბლონი არ არის)"
        lines = []
        for q in questions:
            lines.append(f"- [{q.question_type}] {q.question_text_ka}")
        return "\n".join(lines)

    @staticmethod
    def _normalize_questions(raw: Any) -> list[dict[str, Any]]:
        """Validate and normalize raw Gemini output into a clean list."""
        if not isinstance(raw, list):
            if isinstance(raw, dict) and "questions" in raw:
                raw = raw["questions"]
            else:
                return []

        valid_types = {"text", "boolean", "choice", "date", "number"}
        normalized = []
        for idx, q in enumerate(raw):
            if not isinstance(q, dict):
                continue
            qid = str(q.get("question_id", f"q_{idx}"))
            qtext = str(q.get("question_text_ka", q.get("question_text", q.get("text", ""))))
            qtype = str(q.get("question_type", q.get("type", "text")))
            if qtype not in valid_types:
                qtype = "text"
            options = q.get("options", [])
            if isinstance(options, str):
                options = [options]
            elif not isinstance(options, list):
                options = []
            normalized.append({
                "id": qid,
                "question_id": qid,
                "question_text_ka": qtext,
                "question_type": qtype,
                "options": [str(o) for o in options if o],
                "required": bool(q.get("required", True)),
                "purpose": str(q.get("purpose", "")),
                "legal_relevance": str(q.get("legal_relevance", "")),
                "sort_order": idx,
            })
        return normalized

    async def _maybe_generate_follow_ups(
        self,
        conversation_id: str,
        question_id: str,
        answer: str,
        items: list,
    ) -> list[dict[str, Any]]:
        """Optionally generate follow-up questions based on an answer."""
        # Simple heuristic: only generate follow-ups if the answer is substantial
        if len(answer) < 20:
            return []

        # Build context summary from answered questions
        context_parts = []
        for it in items:
            if it.answer_value:
                context_parts.append(f"Q: {it.question_text_ka}\nA: {it.answer_value}")
        context_summary = "\n\n".join(context_parts) if context_parts else "(ჯერ არ არის პასუხები)"

        # Find the question text
        previous_question = ""
        for it in items:
            if it.question_id == question_id:
                previous_question = it.question_text_ka
                break

        # Determine domain from items or fallback
        domain_name_ka = "სამართლებრივი დარგი"
        conv_svc = ConversationService(self._db)
        conv = await conv_svc.get_conversation(conversation_id)
        if conv:
            domain = conv.get("legal_domain", "")
            template = get_domain_template(domain)
            if template:
                domain_name_ka = template.domain_name_ka

        prompt = FOLLOW_UP_GENERATOR.render(
            domain_name_ka=domain_name_ka,
            previous_question=previous_question,
            user_answer=answer,
            context_summary=context_summary,
        )

        try:
            raw = await self.gemini.generate_json(
                prompt=prompt,
                temperature=FOLLOW_UP_GENERATOR.temperature,
                max_output_tokens=2048,
            )
            follow_ups = self._normalize_questions(raw)
            # Cap follow-ups to 2
            return follow_ups[:2]
        except Exception as e:
            logger.warning("follow_up_generation_failed", error=str(e), conversation_id=conversation_id)
            return []

    @staticmethod
    def _is_complete(answered: int, total: int) -> bool:
        """Determine if the questionnaire is sufficiently complete."""
        if total == 0:
            return False
        # Complete if all required questions are answered, or at least 3 answered
        return answered >= total or answered >= max(MIN_QUESTIONS, total - 2)


_questionnaire_service: QuestionnaireService | None = None


def get_questionnaire_service(db: AsyncSession) -> QuestionnaireService:
    """Return a QuestionnaireService instance (not a singleton — per-request)."""
    return QuestionnaireService(db)
