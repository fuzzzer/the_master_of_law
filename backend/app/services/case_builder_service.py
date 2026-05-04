"""
Defense Case Builder service — generates structured defense case files.

The core differentiator: transforms chat into a full legal defense preparation system.
Sends entire conversation + retrieved law chunks to Gemini, which generates
a structured defense case file using the 8-section template.

Credit cost: 3 credits per case file build.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import LEGAL_DISCLAIMER_KA
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.case_builder import CASE_BUILDER
from app.repositories.case_file_repository import CaseFileRepository
from app.services.conversation_service import ConversationService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CaseFileRenderer:
    """Renders a case file dict into human-readable text."""

    @staticmethod
    def render(data: dict[str, Any]) -> str:
        """Render the case file as human-readable text with emoji sections."""
        lines = [
            "═" * 50,
            "  📁 DEFENSE CASE FILE",
            f"  Case: {data.get('title', 'Untitled')}",
            "═" * 50,
            "",
        ]

        CaseFileRenderer._render_facts(lines, data.get("facts", {}))
        CaseFileRenderer._render_evidence(lines, data.get("evidence", {}))
        CaseFileRenderer._render_laws(lines, data.get("applicable_laws", {}))
        CaseFileRenderer._render_strategies(lines, data.get("defense_strategies", []))
        CaseFileRenderer._render_prosecution(lines, data.get("prosecution_args", []))
        CaseFileRenderer._render_checklist(lines, data.get("action_checklist", []))
        CaseFileRenderer._render_brief(lines, data.get("lawyer_brief", {}))
        CaseFileRenderer._render_citations(lines, data.get("citations", []))

        lines.append(f"⚠️ {LEGAL_DISCLAIMER_KA}")
        return "\n".join(lines)

    @staticmethod
    def _render_facts(lines: list[str], facts: dict[str, Any]) -> None:
        if not facts:
            return
        lines.append("📋 1. FACTS & SITUATION")
        for k, v in facts.items():
            lines.append(f"   {k}: {v}")
        lines.append("")

    @staticmethod
    def _render_evidence(lines: list[str], evidence: dict[str, Any]) -> None:
        if not evidence:
            return
        lines.append("🔍 2. EVIDENCE INVENTORY")
        for item in evidence.get("has", []):
            lines.append(f"   ✅ {item}")
        for item in evidence.get("needs", []):
            lines.append(f"   ⚠️ {item}")
        for item in evidence.get("deadlines", []):
            lines.append(f"   ⏰ {item}")
        lines.append("")

    @staticmethod
    def _render_laws(lines: list[str], laws: dict[str, Any]) -> None:
        if not laws:
            return
        lines.append("⚖️ 3. APPLICABLE LAWS")
        for law in laws.get("favorable", []):
            lines.append(f"   🟢 {law.get('code', '')}, {law.get('article', '')} — {law.get('explanation', '')}")
        for law in laws.get("against", []):
            lines.append(f"   🔴 {law.get('code', '')}, {law.get('article', '')} — {law.get('explanation', '')}")
        for law in laws.get("neutral", []):
            lines.append(f"   🟡 {law.get('code', '')}, {law.get('article', '')} — {law.get('explanation', '')}")
        lines.append("")

    @staticmethod
    def _render_strategies(lines: list[str], strategies: list[dict[str, Any]]) -> None:
        if not strategies:
            return
        lines.append("🛡️ 4. DEFENSE STRATEGIES")
        for i, s in enumerate(strategies, 1):
            lines.append(f"   Strategy {i}: {s.get('name', '')} — Success: {s.get('success_likelihood', '?')}, Risk: {s.get('risk_level', '?')}")
            lines.append(f"      How: {s.get('how_it_works', '')}")
        lines.append("")

    @staticmethod
    def _render_prosecution(lines: list[str], args: list[dict[str, Any]]) -> None:
        if not args:
            return
        lines.append("⚔️ 5. PROSECUTION'S EXPECTED ARGUMENTS")
        for p in args:
            lines.append(f"   Argument: {p.get('argument', '')} → Counter: {p.get('counter', '')}")
        lines.append("")

    @staticmethod
    def _render_checklist(lines: list[str], actions: list[dict[str, Any]]) -> None:
        if not actions:
            return
        lines.append("📅 6. ACTION CHECKLIST")
        for a in actions:
            done = "☑" if a.get("done") else "□"
            lines.append(f"   {done} [{a.get('deadline', '')}] {a.get('action', '')}")
        lines.append("")

    @staticmethod
    def _render_brief(lines: list[str], brief: dict[str, Any]) -> None:
        if not brief:
            return
        lines.append("👤 7. IF YOU HIRE A LAWYER — BRIEF")
        for point in brief.get("key_points", []):
            lines.append(f"   • {point}")
        lines.append("")

    @staticmethod
    def _render_citations(lines: list[str], cites: list[dict[str, Any]]) -> None:
        if not cites:
            return
        lines.append("📚 8. FULL LAW CITATIONS")
        for c in cites:
            lines.append(f"   {c.get('code', '')}, {c.get('article', '')} — {c.get('url', '')}")
        lines.append("")


class LawContextFormatter:
    """Formats law chunks for case builder prompts."""

    @staticmethod
    def format(chunks: list[dict[str, Any]]) -> str:
        if not chunks:
            return "No law articles retrieved."
        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            code = meta.get("code_name", "")
            article = meta.get("article_number", "")
            url = meta.get("article_url", "")
            content = chunk.get("content", "")
            parts.append(f"[{i}] {code}, {article}\n   URL: {url}\n   {content[:2000]}\n")
        return "\n".join(parts)


class CaseBuilderService:
    """Generates structured defense case files using Gemini."""

    def __init__(self, gemini_client: VertexAIClient | None = None) -> None:
        self._gemini = gemini_client
        self._renderer = CaseFileRenderer()
        self._law_formatter = LawContextFormatter()

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def build_case_file(
        self,
        db: AsyncSession,
        user_id: str,
        conversation_id: str,
        retrieved_chunks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Build a full defense case file from a conversation.

        Steps:
        1. Load conversation messages
        2. Format them + law context for Gemini
        3. Generate the structured case file via CASE_BUILDER prompt
        4. Persist to database
        5. Return the case file data
        """
        logger.info("case_build_start", conversation_id=conversation_id)

        history = await self._load_conversation(db, conversation_id)
        conv_text = self._format_conversation(history)
        law_context = self._law_formatter.format(retrieved_chunks or [])

        case_data = await self._generate_case_data(conv_text, law_context)
        rendered = self._renderer.render(case_data)

        cf = await self._persist(db, user_id, conversation_id, case_data, rendered)

        logger.info("case_build_done", case_file_id=str(cf.id))
        return self._to_dict(cf, rendered)

    async def _load_conversation(
        self, db: AsyncSession, conversation_id: str,
    ) -> list[dict[str, str]]:
        """Load conversation history from DB."""
        conv_svc = ConversationService(db)
        history = await conv_svc.get_conversation_history(conversation_id, max_messages=50)
        if not history:
            raise ValueError("No conversation messages found")
        return history

    @staticmethod
    def _format_conversation(history: list[dict[str, str]]) -> str:
        """Format conversation messages into a labeled text block."""
        return "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in history)

    async def _generate_case_data(self, conv_text: str, law_context: str) -> dict[str, Any]:
        """Generate structured case file via Gemini using the CASE_BUILDER prompt."""
        prompt = CASE_BUILDER.render(
            conversation_text=conv_text,
            law_context=law_context,
        )
        case_data = await self.gemini.generate_json(
            prompt=prompt,
            temperature=CASE_BUILDER.temperature,
        )
        if not isinstance(case_data, dict):
            raise ValueError("Gemini returned invalid case file format")
        return case_data

    async def _persist(
        self,
        db: AsyncSession,
        user_id: str,
        conversation_id: str,
        case_data: dict[str, Any],
        rendered: str,
    ) -> Any:
        """Persist the case file to the database."""
        cf_repo = CaseFileRepository(db)
        return await cf_repo.create(
            user_id=user_id,
            conversation_id=uuid.UUID(conversation_id),
            title=case_data.get("title", "Defense Case File"),
            facts=case_data.get("facts"),
            evidence=case_data.get("evidence"),
            applicable_laws=case_data.get("applicable_laws"),
            defense_strategies=case_data.get("defense_strategies"),
            prosecution_args=case_data.get("prosecution_args"),
            action_checklist=case_data.get("action_checklist"),
            lawyer_brief=case_data.get("lawyer_brief"),
            citations=case_data.get("citations"),
            rendered_text=rendered,
            status="draft",
        )

    @staticmethod
    def _to_dict(cf: Any, rendered: str) -> dict[str, Any]:
        """Convert a CaseFile ORM instance to a dict for the response."""
        return {
            "id": str(cf.id),
            "title": cf.title,
            "status": cf.status,
            "rendered_text": rendered,
            "facts": cf.facts,
            "evidence": cf.evidence,
            "applicable_laws": cf.applicable_laws,
            "defense_strategies": cf.defense_strategies,
            "prosecution_args": cf.prosecution_args,
            "action_checklist": cf.action_checklist,
            "lawyer_brief": cf.lawyer_brief,
            "citations": cf.citations,
            "created_at": cf.created_at.isoformat() if cf.created_at else "",
        }


_case_builder: CaseBuilderService | None = None

def get_case_builder_service() -> CaseBuilderService:
    global _case_builder
    if _case_builder is None:
        _case_builder = CaseBuilderService()
    return _case_builder
