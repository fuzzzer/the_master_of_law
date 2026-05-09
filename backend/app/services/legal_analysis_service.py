"""
Legal Analysis Service — Gemini-powered legal reasoning.

Constructs the system prompt, builds context from retrieved law chunks,
sends to Gemini 2.5 Pro, and returns a structured legal analysis.

Supports multi-source context: georgian_laws, court_practice, grand_chamber.
Injects source-specific instructions when court/GC chunks are present.
"""

from __future__ import annotations

from typing import Any

from app.config.constants import LEGAL_DISCLAIMER_KA
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts import PromptTemplate
from app.prompts.legal_analysis import LEGAL_ANALYSIS_SYSTEM
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Source-specific RAG instructions ─────────────────────────
# Injected into the system prompt when chunks from these sources
# appear in the retrieved context.

_RAG_INSTRUCTIONS: dict[str, str] = {
    "court_practice": (
        "\n[სასამართლო პრაქტიკა / Court Practice]\n"
        "When citing retrieved COURT PRACTICE chunks:\n"
        "- Always cite the full case number (e.g., \"ბს-245-242(კ-24)\")\n"
        "- Specify the category: criminal/civil/administrative\n"
        "- Note the decision year — more recent decisions carry more weight\n"
        "- These are INTERPRETIVE — they show how courts APPLY the law\n"
        "- They are NOT formally binding precedent (unlike Grand Chamber)\n"
        "- Use to strengthen arguments: \"სასამართლო პრაქტიკის მიხედვით...\"\n"
        "- If a court interpretation differs from the literal text, present BOTH\n"
        "- Connect court practice back to the specific law articles being interpreted\n"
    ),
    "grand_chamber": (
        "\n[დიდი პალატა / Grand Chamber (Binding)]\n"
        "When citing retrieved GRAND CHAMBER chunks:\n"
        "- ⚠️ These are BINDING decisions — they override ALL lower court interpretations\n"
        "- Always cite as: \"დიდი პალატის გადაწყვეტილება, [case_number]\"\n"
        "- Grand Chamber carries the HIGHEST judicial authority in Georgia\n"
        "- If a GC decision interprets a specific article, that IS the authoritative meaning\n"
        "- If GC contradicts regular court practice, GC ALWAYS prevails\n"
        "- Present the binding rule from the resolution (სარეზოლუციო) section\n"
        "- When supporting the user: \"დიდი პალატის სავალდებულო განმარტებით...\"\n"
    ),
}

_THRESHOLD_INSTRUCTIONS = (
    "\n[იურიდიული ზღვრები / Legal Thresholds]\n"
    "When threshold chunks are present in the context:\n"
    "- Use EXACT values from threshold data (quantities, time periods, amounts)\n"
    "- NEVER approximate or round threshold values — precision is critical\n"
    "- Cite the specific article and paragraph for each threshold\n"
    "- If the user asks about quantities/amounts, present ALL relevant thresholds\n"
    "- Compare the user's situation against the exact threshold values\n"
    "- If no threshold data exists for a query, say \"ამ ინფორმაციას ჩვენს "
    "მონაცემთა ბაზაში ვერ ვპოულობ\" — NEVER invent numbers\n"
)


class LawContextFormatter:
    """Formats retrieved chunks into context for Gemini prompts.

    Handles multiple source types: georgian_laws, court_practice, grand_chamber.
    Groups chunks by source and formats each with source-appropriate headers.
    """

    @staticmethod
    def format(chunks: list[dict[str, Any]]) -> str:
        """Format retrieved chunks into a numbered, source-grouped context block."""
        if not chunks:
            return "No relevant legal context was found."

        # Group by source collection
        by_source: dict[str, list[tuple[int, dict]]] = {}
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("metadata", {}).get("_collection", "georgian_laws")
            by_source.setdefault(source, []).append((i, chunk))

        parts = []

        # Format georgian_laws chunks
        if "georgian_laws" in by_source:
            parts.append("RELEVANT GEORGIAN LAW ARTICLES:\n")
            for i, chunk in by_source["georgian_laws"]:
                meta = chunk.get("metadata", {})
                code = meta.get("code_name", "Unknown")
                article = meta.get("article_number", "")
                title = meta.get("article_title", "")
                citation = meta.get("citation_text", "")
                url = meta.get("article_url", "")
                content = chunk.get("content", "")

                header = f"[{i}] {code}, {article}"
                if title:
                    header += f" — {title}"
                parts.append(header)
                if citation:
                    parts.append(f"   Citation: {citation}")
                if url:
                    parts.append(f"   URL: {url}")
                parts.append(f"   Text: {content[:2000]}")
                parts.append("")

        # Format court_practice chunks
        if "court_practice" in by_source:
            parts.append("\nRELEVANT COURT PRACTICE (სასამართლო პრაქტიკა):\n")
            for i, chunk in by_source["court_practice"]:
                meta = chunk.get("metadata", {})
                case_id = meta.get("case_id", "Unknown")
                category = meta.get("category", "")
                year = meta.get("year", "")
                section = meta.get("section", "")
                content = chunk.get("content", "")

                header = f"[{i}] Case {case_id}"
                if category:
                    header += f" ({category})"
                if year:
                    header += f" [{year}]"
                if section and section != "general":
                    header += f" — {section}"
                parts.append(header)
                parts.append(f"   Text: {content[:2000]}")
                parts.append("")

        # Format grand_chamber chunks
        if "grand_chamber" in by_source:
            parts.append("\nBINDING GRAND CHAMBER DECISIONS (დიდი პალატა — სავალდებულო):\n")
            for i, chunk in by_source["grand_chamber"]:
                meta = chunk.get("metadata", {})
                case_id = meta.get("case_id", "Unknown")
                category = meta.get("category", "")
                year = meta.get("year", "")
                norm = meta.get("norm_interpreted", "")
                binding_rule = meta.get("binding_rule", "")
                content = chunk.get("content", "")

                header = f"[{i}] ⚠️ Grand Chamber: {case_id}"
                if category:
                    header += f" ({category})"
                if year:
                    header += f" [{year}]"
                parts.append(header)
                if norm:
                    parts.append(f"   Norm interpreted: {norm}")
                if binding_rule:
                    parts.append(f"   Binding rule: {binding_rule}")
                parts.append(f"   Text: {content[:2000]}")
                parts.append("")

        return "\n".join(parts)

    @staticmethod
    def get_source_types(chunks: list[dict[str, Any]]) -> set[str]:
        """Return the set of source collections present in the chunks."""
        return {
            chunk.get("metadata", {}).get("_collection", "georgian_laws")
            for chunk in chunks
        }


class ConversationHistoryFormatter:
    """Formats conversation history for multi-turn Gemini context."""

    @staticmethod
    def format(history: list[dict[str, str]], max_turns: int = 10) -> str:
        """Format conversation history into a labeled text block."""
        if not history:
            return ""

        parts = ["CONVERSATION HISTORY:\n"]
        for msg in history[-max_turns:]:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            parts.append(f"{role.upper()}: {text}\n")
        parts.append("\n---\n")
        return "\n".join(parts)


class LegalAnalysisService:
    """Generates grounded legal analysis using Gemini + retrieved law chunks."""

    def __init__(self, gemini_client: VertexAIClient | None = None):
        self._gemini = gemini_client
        self._law_formatter = LawContextFormatter()
        self._history_formatter = ConversationHistoryFormatter()

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    async def analyze(
        self,
        user_message: str,
        retrieved_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: PromptTemplate | None = None,
        model_name: str | None = None,
    ) -> str:
        """
        Generate a legal analysis response.

        Args:
            user_message: The user's current message.
            retrieved_chunks: Law chunks from the RAG pipeline.
            conversation_history: Previous messages for context.

        Returns:
            The AI-generated legal analysis text.
        """
        user_prompt = self._build_user_prompt(
            user_message, retrieved_chunks, conversation_history,
        )

        prompt_tpl = system_prompt or LEGAL_ANALYSIS_SYSTEM

        # Build system prompt with source-specific RAG instructions
        system_prompt_text = self._build_system_prompt(retrieved_chunks, prompt_tpl)

        logger.info(
            "legal_analysis_start",
            chunks_count=len(retrieved_chunks),
            prompt_length=len(user_prompt),
            sources=list(self._law_formatter.get_source_types(retrieved_chunks)),
        )

        response = await self.gemini.generate(
            prompt=user_prompt,
            system_instruction=system_prompt_text,
            temperature=prompt_tpl.temperature,
            max_output_tokens=prompt_tpl.max_output_tokens,
            model_name=model_name,
        )

        response += f"\n\n---\n⚠️ {LEGAL_DISCLAIMER_KA}"

        logger.info("legal_analysis_done", response_length=len(response))
        return response

    async def analyze_stream(
        self,
        user_message: str,
        retrieved_chunks: list[dict[str, Any]],
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: PromptTemplate | None = None,
        model_name: str | None = None,
    ):
        """
        Generate a legal analysis response in a stream.
        """
        user_prompt = self._build_user_prompt(
            user_message, retrieved_chunks, conversation_history,
        )

        prompt_tpl = system_prompt or LEGAL_ANALYSIS_SYSTEM

        # Build system prompt with source-specific RAG instructions
        system_prompt_text = self._build_system_prompt(retrieved_chunks, prompt_tpl)

        logger.info(
            "legal_analysis_stream_start",
            chunks_count=len(retrieved_chunks),
            prompt_length=len(user_prompt),
            sources=list(self._law_formatter.get_source_types(retrieved_chunks)),
        )

        async for chunk in self.gemini.generate_stream(
            prompt=user_prompt,
            system_instruction=system_prompt_text,
            temperature=prompt_tpl.temperature,
            max_output_tokens=prompt_tpl.max_output_tokens,
            model_name=model_name,
        ):
            yield chunk

        # Yield the disclaimer at the end
        yield f"\n\n---\n⚠️ {LEGAL_DISCLAIMER_KA}"
        logger.info("legal_analysis_stream_done")

    def _build_system_prompt(
        self,
        chunks: list[dict[str, Any]],
        prompt_tpl: PromptTemplate,
    ) -> str:
        """Build system prompt with dynamic source-specific instructions.

        When only georgian_laws chunks are present, this returns the base
        system prompt unchanged (fully backward compatible). When court_practice
        or grand_chamber chunks are present, source-specific instructions
        are appended. When threshold chunks are present, threshold usage
        instructions are appended.
        """
        base = prompt_tpl.template
        sources = self._law_formatter.get_source_types(chunks)

        extra = []
        for source in sorted(sources):
            if source in _RAG_INSTRUCTIONS:
                extra.append(_RAG_INSTRUCTIONS[source])

        has_thresholds = any(
            c.get("metadata", {}).get("chunk_type") == "threshold" for c in chunks
        )
        if has_thresholds:
            extra.append(_THRESHOLD_INSTRUCTIONS)

        if not extra:
            return base

        return (
            base
            + "\n\nSOURCE-SPECIFIC INSTRUCTIONS FOR RETRIEVED CONTEXT:\n"
            + "\n".join(extra)
        )

    def _build_user_prompt(
        self,
        user_message: str,
        chunks: list[dict[str, Any]],
        history: list[dict[str, str]] | None,
    ) -> str:
        """Assemble the full user prompt from law context + history + message."""
        parts = [self._law_formatter.format(chunks), "\n---\n"]

        if history:
            parts.append(self._history_formatter.format(history))

        parts.append(f"USER'S CURRENT MESSAGE:\n{user_message}")
        return "\n".join(parts)


_analysis_service: LegalAnalysisService | None = None

def get_legal_analysis_service() -> LegalAnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = LegalAnalysisService()
    return _analysis_service
