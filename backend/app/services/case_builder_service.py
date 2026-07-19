"""
Defense Case Builder service — generates structured defense case files.

The core differentiator: transforms chat into a full legal defense preparation system.
Sends entire conversation + retrieved law chunks to Gemini, which generates
a structured defense case file using the 8-section template.

Credit cost: 3 credits per case file build.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.constants import LEGAL_DISCLAIMER_KA
from app.config.settings import settings
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.case_builder import CASE_BUILDER
from app.prompts.chat import CASE_FULL_ANALYSIS
from app.repositories.case_file_repository import CaseFileRepository
from app.repositories.user_repository import UserRepository
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
        CaseFileRenderer._render_unclear(lines, data.get("unclear_items", []))
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
            lines.append(
                f"   🟢 {law.get('code', '')}, {law.get('article', '')} — {law.get('explanation', '')}"
            )
        for law in laws.get("against", []):
            lines.append(
                f"   🔴 {law.get('code', '')}, {law.get('article', '')} — {law.get('explanation', '')}"
            )
        for law in laws.get("neutral", []):
            lines.append(
                f"   🟡 {law.get('code', '')}, {law.get('article', '')} — {law.get('explanation', '')}"
            )
        lines.append("")

    @staticmethod
    def _render_strategies(lines: list[str], strategies: list[dict[str, Any]]) -> None:
        if not strategies:
            return
        lines.append("🛡️ 4. DEFENSE STRATEGIES")
        for i, s in enumerate(strategies, 1):
            lines.append(
                f"   Strategy {i}: {s.get('name', '')} — Success: {s.get('success_likelihood', '?')}, Risk: {s.get('risk_level', '?')}"
            )
            lines.append(f"      How: {s.get('how_it_works', '')}")
        lines.append("")

    @staticmethod
    def _render_prosecution(lines: list[str], args: list[dict[str, Any]]) -> None:
        if not args:
            return
        lines.append("⚔️ 5. PROSECUTION'S EXPECTED ARGUMENTS")
        for p in args:
            lines.append(
                f"   Argument: {p.get('argument', '')} → Counter: {p.get('counter', '')}"
            )
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
    def _render_unclear(lines: list[str], items: list[str]) -> None:
        if not items:
            return
        lines.append("❓ დასაზუსტებელი ინფორმაცია")
        for item in items:
            lines.append(f"   • {item}")
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
            lines.append(
                f"   {c.get('code', '')}, {c.get('article', '')} — {c.get('url', '')}"
            )
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
            parts.append(
                f"[{i}] {code}, {article}\n   URL: {url}\n   {content[:2000]}\n"
            )
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

        Three-stage pipeline:
        1. Load conversation + auto-retrieve law chunks via RAG
        2. CASE_FULL_ANALYSIS: generate comprehensive legal analysis text
        3. CASE_BUILDER: convert analysis into structured JSON
        """
        logger.info("case_build_start", conversation_id=conversation_id)

        history = await self._load_conversation(db, conversation_id)
        conv_text = self._format_conversation(history)

        if not retrieved_chunks:
            retrieved_chunks = await self._auto_retrieve_chunks(history)

        law_context = self._law_formatter.format(retrieved_chunks or [])

        # Stage 1: Rich legal analysis from conversation
        full_analysis = await self._generate_full_analysis(conv_text, law_context)
        logger.info("case_analysis_done", analysis_length=len(full_analysis))
        
        # Save the full analysis as an assistant message so it persists in chat
        conv_svc = ConversationService(db)
        await conv_svc.save_assistant_message(
            conversation_id=conversation_id,
            content=full_analysis,
            citations=[],
            retrieved_chunk_ids=[],
            credit_cost=0,
        )

        case_data = await self._generate_case_data(full_analysis, law_context)
        rendered = self._renderer.render(case_data)

        cf = await self._persist(
            db, user_id, conversation_id, case_data, rendered, retrieved_chunks
        )

        logger.info("case_build_done", case_file_id=str(cf.id))
        result = self._to_dict(cf, rendered)
        result["full_analysis_text"] = full_analysis
        return result

    async def update_case_file(
        self,
        db: AsyncSession,
        case_file_id: uuid.UUID,
        conversation_id: str,
        retrieved_chunks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Build a full defense case file from a conversation and UPDATE an existing case file.
        Used by the case agent to populate an empty case after intake.
        """
        logger.info("case_update_start", case_file_id=str(case_file_id))

        history = await self._load_conversation(db, conversation_id)
        conv_text = self._format_conversation(history)

        if not retrieved_chunks:
            retrieved_chunks = await self._auto_retrieve_chunks(history)

        law_context = self._law_formatter.format(retrieved_chunks or [])

        # Stage 1: Rich legal analysis from conversation
        full_analysis = await self._generate_full_analysis(conv_text, law_context)
        logger.info("case_analysis_done", analysis_length=len(full_analysis))
        
        # Save the full analysis as an assistant message so it persists in chat
        conv_svc = ConversationService(db)
        await conv_svc.save_assistant_message(
            conversation_id=conversation_id,
            content=full_analysis,
            citations=[],
            retrieved_chunk_ids=[],
            credit_cost=0,
        )

        case_data = await self._generate_case_data(full_analysis, law_context)
        rendered = self._renderer.render(case_data)

        # Update the existing case file
        cf_repo = CaseFileRepository(db)
        cf = await cf_repo.update(
            case_file_id,
            title=case_data.get("title", "Defense Case File"),
            facts=case_data.get("facts"),
            evidence=case_data.get("evidence"),
            applicable_laws=case_data.get("applicable_laws"),
            defense_strategies=case_data.get("defense_strategies"),
            prosecution_args=case_data.get("prosecution_args"),
            action_checklist=case_data.get("action_checklist"),
            unclear_items=case_data.get("unclear_items"),
            lawyer_brief=case_data.get("lawyer_brief"),
            citations=case_data.get("citations"),
            retrieved_chunks=retrieved_chunks,
            rendered_text=rendered,
            status="active",
        )

        logger.info("case_update_done", case_file_id=str(cf.id))
        result = self._to_dict(cf, rendered)
        result["full_analysis_text"] = full_analysis
        return result

    async def _load_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
    ) -> list[dict[str, str]]:
        """Load conversation history from DB."""
        conv_svc = ConversationService(db)
        history = await conv_svc.get_conversation_history(
            conversation_id, max_messages=50
        )
        if not history:
            raise ValueError("No conversation messages found")
        return history

    @staticmethod
    def _format_conversation(history: list[dict[str, str]]) -> str:
        """Format conversation messages into a labeled text block."""
        return "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in history)

    async def _generate_full_analysis(
        self, conv_text: str, law_context: str
    ) -> str:
        """Stage 1: Generate comprehensive legal analysis text via Gemini."""
        prompt = CASE_FULL_ANALYSIS.render(
            conversation_text=conv_text,
            law_context=law_context,
        )
        analysis = await self.gemini.generate(
            prompt=prompt,
            temperature=CASE_FULL_ANALYSIS.temperature,
            model_name=settings.gemini_model,
        )
        return analysis

    async def _generate_case_data(
        self, analysis_text: str, law_context: str
    ) -> dict[str, Any]:
        """Stage 2: Convert analysis into structured JSON via CASE_BUILDER."""
        prompt = CASE_BUILDER.render(
            conversation_text=analysis_text,
            law_context=law_context,
        )
        case_data = await self.gemini.generate_json(
            prompt=prompt,
            temperature=CASE_BUILDER.temperature,
            model_name=settings.gemini_model,
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
        retrieved_chunks: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Persist the case file to the database."""
        cf_repo = CaseFileRepository(db)
        # `user_id` arrives as the Firebase UID (string); case_files.user_id is a
        # UUID FK to users.id. Resolve it — inserting the raw firebase_uid raises
        # asyncpg DatatypeMismatchError (uuid column vs varchar value).
        user = await UserRepository(db).get_by_firebase_uid(user_id)
        if user is None:
            raise ValueError(f"No user found for firebase_uid={user_id!r}")
        return await cf_repo.create(
            user_id=user.id,
            conversation_id=uuid.UUID(conversation_id),
            title=case_data.get("title", "Defense Case File"),
            facts=case_data.get("facts"),
            evidence=case_data.get("evidence"),
            applicable_laws=case_data.get("applicable_laws"),
            defense_strategies=case_data.get("defense_strategies"),
            prosecution_args=case_data.get("prosecution_args"),
            action_checklist=case_data.get("action_checklist"),
            unclear_items=case_data.get("unclear_items"),
            lawyer_brief=case_data.get("lawyer_brief"),
            citations=case_data.get("citations"),
            retrieved_chunks=retrieved_chunks,
            rendered_text=rendered,
            status="draft",
        )

    async def _auto_retrieve_chunks(
        self,
        history: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Expand user messages into legal terms (flash), then RAG retrieve.

        Users often use colloquial language. Flash model reformulates into
        proper legal search queries before hitting the RAG pipeline.
        """
        from app.services.rag_retrieval_service import get_rag_service

        user_messages = [m["content"] for m in history if m["role"] == "user"]
        if not user_messages:
            return []

        combined = " ".join(user_messages)[:2000]

        # Step 1: Flash model expands raw user language into legal search queries
        expanded_queries = await self._expand_for_rag(combined)

        # Step 2: RAG retrieve with each expanded query, merge results in parallel
        rag = get_rag_service()
        all_chunks: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        
        tasks = [rag.retrieve(query) for query in expanded_queries]
        results = await asyncio.gather(*tasks)
        
        for chunks in results:
            for chunk in chunks:
                cid = chunk.get("chunk_id", "")
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    all_chunks.append(chunk)

        logger.info(
            "case_build_auto_rag",
            user_messages=len(user_messages),
            expanded_queries=len(expanded_queries),
            chunks_retrieved=len(all_chunks),
        )
        return all_chunks

    async def _expand_for_rag(self, user_text: str) -> list[str]:
        """Use flash model to expand colloquial text into legal search queries."""
        prompt = (
            "You are a Georgian legal search expert. The user described their situation "
            "in everyday language. Generate 3-5 precise legal search queries in Georgian "
            "that would find the most relevant law articles for their case.\n\n"
            "Include:\n"
            "- Specific legal code names (სისხლის სამართლის კოდექსი, სამოქალაქო კოდექსი, etc.)\n"
            "- Relevant article topics and legal terms\n"
            "- Both broad and narrow queries\n\n"
            f"User's situation:\n{user_text}\n\n"
            "Return a JSON array of search query strings."
        )
        try:
            queries = await self.gemini.generate_json(
                prompt=prompt,
                temperature=0.3,
                model_name=settings.gemini_chat_model,  # gemini-3-flash-preview (fast)
            )
            if isinstance(queries, list):
                result = [q for q in queries if isinstance(q, str) and q.strip()]
                if result:
                    return result
        except Exception as e:
            logger.warning("case_build_query_expansion_failed", error=str(e))

        # Fallback: use raw text
        return [user_text]

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
            "unclear_items": cf.unclear_items,
            "lawyer_brief": cf.lawyer_brief,
            "citations": cf.citations,
            "retrieved_chunks": cf.retrieved_chunks,
            "created_at": cf.created_at.isoformat() if cf.created_at else "",
        }


_case_builder: CaseBuilderService | None = None


def get_case_builder_service() -> CaseBuilderService:
    global _case_builder
    if _case_builder is None:
        _case_builder = CaseBuilderService()
    return _case_builder
