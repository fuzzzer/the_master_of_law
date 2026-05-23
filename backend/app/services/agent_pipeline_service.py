"""
Agent Pipeline Service — unified 3-phase agentic pipeline.

Replaces the inline pipeline logic in chat_router, ws_chat_router, and
case_agent_router. One service, one pipeline, all tools.

Phase 1: PLAN (Flash) — intent analysis, query planning, direct response
Phase 2: EXECUTE (Gemini Pro + tools) — RAG + legal analysis + tool loop
Phase 3: VERIFY (Flash) — citation self-correction against corpus

Usage:
    pipeline = get_agent_pipeline_service()
    result = await pipeline.run(
        user_message="...",
        conversation_history=[...],
        system_prompt="...",
        rag_collections=["georgian_laws", "court_practice"],
    )
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from google.genai import types

from app.config.constants import GEMINI_TEMPERATURE
from app.config.settings import settings
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.agent_planning import AGENT_PLANNER, CITATION_VERIFIER
from app.services.citation_service import CitationService, get_citation_service
from app.services.rag_retrieval_service import RAGRetrievalService, get_rag_service
from app.tools.case_tools import ALWAYS_TOOLS, CASE_CREATION_TOOLS, FULL_CASE_TOOLS
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Configurable constants ───────────────────────────────────

MAX_VERIFY_ITERATIONS = 2
MAX_TOOL_CALLS_PER_MESSAGE = 5
PLANNER_HISTORY_WINDOW = 6  # last N messages for planning


# ── Data classes ─────────────────────────────────────────────

@dataclass
class PipelinePlan:
    """Output of Phase 1 — the agent's plan for this message."""
    needs_rag: bool = True
    direct_response: str | None = None
    search_queries: list[str] = field(default_factory=list)
    legal_entities: list[dict] = field(default_factory=list)
    intent: str = "legal_question"


@dataclass
class ToolResultInfo:
    """Lightweight record of a tool call for the final result."""
    tool_name: str
    status: str
    result: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_id: str | None = None
    description: str | None = None


@dataclass
class PipelineResult:
    """Final output of the full pipeline."""
    response_text: str
    chunks: list[dict[str, Any]] = field(default_factory=list)
    verified_citations: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    plan: PipelinePlan = field(default_factory=PipelinePlan)
    tool_results: list[ToolResultInfo] = field(default_factory=list)


# ── Service ──────────────────────────────────────────────────

class AgentPipelineService:
    """Unified 3-phase agentic pipeline for all chat modes."""

    def __init__(
        self,
        gemini: VertexAIClient | None = None,
        rag: RAGRetrievalService | None = None,
        citation_svc: CitationService | None = None,
    ) -> None:
        self._gemini = gemini
        self._rag = rag
        self._citation_svc = citation_svc

    @property
    def gemini(self) -> VertexAIClient:
        if self._gemini is None:
            self._gemini = get_vertex_ai_client()
        return self._gemini

    @property
    def rag(self) -> RAGRetrievalService:
        if self._rag is None:
            self._rag = get_rag_service()
        return self._rag

    @property
    def citation_svc(self) -> CitationService:
        if self._citation_svc is None:
            self._citation_svc = get_citation_service()
        return self._citation_svc

    # ── Main entry point (non-streaming) ─────────────────────

    async def run(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        system_prompt: str = "",
        rag_collections: list[str] | None = None,
        case_file_id: str | None = None,
        user_id: str | None = None,
        conversation_id: str | None = None,
        db: Any = None,
        redis_client: Any = None,
        is_case_chat: bool = False,
    ) -> PipelineResult:
        """Run the full 3-phase pipeline (non-streaming).

        Parameters
        ----------
        user_message : str
            The user's current message.
        conversation_history : list[dict] | None
            Previous messages in [{"role": "user"|"assistant", "content": "..."}] format.
        system_prompt : str
            System instruction for Gemini.
        rag_collections : list[str] | None
            ChromaDB collections to search. None = all.
        case_file_id : str | None
            Active case file ID. Enables case tools.
        user_id : str | None
            User ID for case creation.
        conversation_id : str | None
            Conversation ID for case creation.
        db : AsyncSession | None
            Database session for case tool execution.
        redis_client : Any | None
            Redis client for tool confirmation tracking.
        is_case_chat : bool
            Whether this is a case intake conversation.
        """
        history = conversation_history or []

        # ── Phase 1: Plan ────────────────────────────────────
        plan = await self._phase_1_plan(user_message, history)
        logger.info(
            "pipeline_phase_1_done",
            intent=plan.intent,
            needs_rag=plan.needs_rag,
            direct=plan.direct_response is not None,
            queries=len(plan.search_queries),
        )

        # Direct response — skip everything
        if plan.direct_response is not None:
            return PipelineResult(
                response_text=plan.direct_response,
                plan=plan,
            )

        # ── Phase 2: Execute ─────────────────────────────────
        response_text, chunks, tool_results = await self._phase_2_execute(
            plan=plan,
            user_message=user_message,
            system_prompt=system_prompt,
            history=history,
            collections=rag_collections,
            case_file_id=case_file_id,
            user_id=user_id,
            conversation_id=conversation_id,
            db=db,
            redis_client=redis_client,
            is_case_chat=is_case_chat,
        )

        # ── Phase 3: Verify ──────────────────────────────────
        verified_response, verified_citations, iterations = await self._phase_3_verify(
            response_text, chunks
        )

        return PipelineResult(
            response_text=verified_response,
            chunks=chunks,
            verified_citations=verified_citations,
            iterations=iterations,
            plan=plan,
            tool_results=tool_results,
        )

    # ── Phase 1: Plan ────────────────────────────────────────

    async def _phase_1_plan(
        self,
        user_message: str,
        history: list[dict[str, str]],
    ) -> PipelinePlan:
        """Use Flash model with native chat history to classify intent.

        Creates a chat session seeded with recent conversation, then sends
        the user's message. The model sees actual conversation turns
        natively — not as a serialized string.
        """
        recent = history[-PLANNER_HISTORY_WINDOW:] if history else []
        chat_history = self._history_to_contents(recent)

        try:
            chat = self.gemini.create_chat(
                history=chat_history,
                system_instruction=AGENT_PLANNER.template,
                temperature=AGENT_PLANNER.temperature,
                max_output_tokens=AGENT_PLANNER.max_output_tokens,
                model_name=settings.gemini_chat_model,  # Flash
                response_mime_type="application/json",
            )
            response = await chat.send_message(user_message)
            raw = response.text

            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                if "```json" in raw:
                    start = raw.index("```json") + 7
                    end = raw.index("```", start)
                    result = json.loads(raw[start:end].strip())
                elif "```" in raw:
                    start = raw.index("```") + 3
                    end = raw.index("```", start)
                    result = json.loads(raw[start:end].strip())
                else:
                    result = json.loads(raw.strip())

            if isinstance(result, dict):
                return PipelinePlan(
                    needs_rag=result.get("needs_rag", True),
                    direct_response=result.get("direct_response"),
                    search_queries=[
                        q for q in result.get("search_queries", [])
                        if isinstance(q, str) and q.strip()
                    ],
                    legal_entities=result.get("legal_entities", []),
                    intent=result.get("intent", "legal_question"),
                )
        except Exception as e:
            logger.warning("pipeline_phase_1_failed", error=str(e))

        # Fallback: always do RAG with raw message
        return PipelinePlan(needs_rag=True, search_queries=[user_message])


    async def _phase_2_execute(
        self,
        plan: PipelinePlan,
        user_message: str,
        system_prompt: str,
        history: list[dict[str, str]],
        collections: list[str] | None,
        case_file_id: str | None,
        user_id: str | None,
        conversation_id: str | None,
        db: Any,
        redis_client: Any,
        is_case_chat: bool,
    ) -> tuple[str, list[dict], list[ToolResultInfo]]:
        """RAG retrieval + Gemini generation with native chat session."""
        # Stage A: RAG retrieval
        chunks: list[dict] = []
        if plan.needs_rag and plan.search_queries:
            chunks = await self.rag.retrieve(
                user_message=user_message,
                collections=collections,
                pre_expanded_queries=plan.search_queries,
            )
            logger.info("pipeline_phase_2_rag_done", chunks=len(chunks))

        # Stage B: Create native chat session with history + tools
        law_context = self._format_law_context(chunks)
        tools = self._select_tools(case_file_id, is_case_chat)
        chat_history = self._history_to_contents(history)

        chat = self.gemini.create_chat(
            history=chat_history,
            system_instruction=system_prompt,
            tools=tools,
            temperature=GEMINI_TEMPERATURE,
            model_name=settings.gemini_model,
        )

        # Build the user message with law context prefix
        message_parts = []
        if law_context:
            message_parts.append(f"RETRIEVED LAW ARTICLES:\n{law_context}\n\n")
        message_parts.append(user_message)
        full_message = "\n".join(message_parts)

        # Stage C: Send message and handle tool loop
        tool_results: list[ToolResultInfo] = []
        response_text = ""

        for iteration in range(MAX_TOOL_CALLS_PER_MESSAGE + 1):
            response = await chat.send_message(full_message)

            # Check for function calls
            has_function_call = False
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        has_function_call = True
                        fc = part.function_call
                        fc_name = fc.name
                        fc_args = dict(fc.args) if fc.args else {}

                        logger.info("pipeline_tool_call", tool=fc_name, args_keys=list(fc_args.keys()))

                        # Execute the tool
                        tool_result = await self._execute_tool(
                            tool_name=fc_name,
                            args=fc_args,
                            case_file_id=case_file_id,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            db=db,
                            redis_client=redis_client,
                            chunks=chunks,
                        )

                        tool_results.append(ToolResultInfo(
                            tool_name=fc_name,
                            status=tool_result.get("_status", "executed"),
                            result={k: v for k, v in tool_result.items() if not k.startswith("_")},
                            requires_confirmation=tool_result.get("_requires_confirmation", False),
                            confirmation_id=tool_result.get("_confirmation_id"),
                            description=tool_result.get("_description"),
                        ))

                        # If create_case returned a new case_file_id, use it
                        if fc_name == "create_case" and "case_file_id" in tool_result:
                            case_file_id = tool_result["case_file_id"]
                            # Note: can't change tools mid-chat, but the next
                            # message in this conversation will get full tools

                        # Send function response back to the chat — SDK
                        # appends both the model's function_call and our
                        # function_response to history automatically.
                        clean_result = {
                            k: v for k, v in tool_result.items()
                            if not k.startswith("_")
                        }
                        full_message = types.Part.from_function_response(
                            name=fc_name,
                            response=clean_result,
                        )
                        break  # Process one tool call at a time

            if not has_function_call:
                # Extract text response
                if response.text:
                    response_text = response.text
                break

        if not response_text and response.text:
            response_text = response.text

        return response_text, chunks, tool_results

    async def _execute_tool(
        self,
        tool_name: str,
        args: dict,
        case_file_id: str | None,
        user_id: str | None,
        conversation_id: str | None,
        db: Any,
        redis_client: Any,
        chunks: list[dict],
    ) -> dict:
        """Execute a single tool call and return the result."""
        # search_law — always available, no DB needed
        if tool_name == "search_law":
            return await self._handle_search_law(args, chunks)

        # Case tools — need DB
        if db is None:
            return {"error": f"Tool {tool_name} requires a database session"}

        from app.services.case_tool_executor import CaseToolExecutor
        executor = CaseToolExecutor(
            db=db,
            redis_client=redis_client,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        result = await executor.execute(
            tool_name=tool_name,
            args=args,
            case_file_id=case_file_id or "",
            user_id=user_id or "",
        )
        out = result.result.copy()
        out["_status"] = result.status
        out["_requires_confirmation"] = result.requires_confirmation
        if result.confirmation_id:
            out["_confirmation_id"] = result.confirmation_id
        if result.description:
            out["_description"] = result.description
        return out

    async def _handle_search_law(
        self, args: dict, existing_chunks: list[dict]
    ) -> dict:
        """Handle the search_law tool — search the corpus for specific articles."""
        query = args.get("query", "")
        article_number = args.get("article_number")
        code_name = args.get("code_name")

        # If exact article is specified, try metadata search first
        if article_number:
            citation_svc = self.citation_svc
            hit = citation_svc._search_corpus_exact(article_number, code_name or "")
            if hit:
                return {
                    "found": True,
                    "article": hit.get("metadata", {}).get("article_number", ""),
                    "code": hit.get("metadata", {}).get("code_name", ""),
                    "content": hit.get("content", "")[:2000],
                    "url": hit.get("metadata", {}).get("article_url", ""),
                }

        # Fall back to RAG search
        if query:
            results = await self.rag.retrieve(
                user_message=query,
                collections=["georgian_laws"],
            )
            if results:
                top = results[0]
                return {
                    "found": True,
                    "article": top.get("metadata", {}).get("article_number", ""),
                    "code": top.get("metadata", {}).get("code_name", ""),
                    "content": top.get("content", "")[:2000],
                    "url": top.get("metadata", {}).get("article_url", ""),
                    "total_results": len(results),
                }

        return {"found": False, "message": "No matching law articles found."}

    # ── Phase 3: Verify ──────────────────────────────────────

    async def _phase_3_verify(
        self,
        response_text: str,
        chunks: list[dict],
    ) -> tuple[str, list[dict], int]:
        """Extract citations, verify against corpus, iterate if needed.

        Returns (corrected_text, verified_citations, iterations).
        """
        if not response_text or not chunks:
            # Nothing to verify — extract what we can and return
            raw_citations = self.citation_svc.extract_citations(response_text)
            return response_text, self.citation_svc.verify_citations(raw_citations, chunks), 0

        for iteration in range(MAX_VERIFY_ITERATIONS):
            raw_citations = self.citation_svc.extract_citations(response_text)
            if not raw_citations:
                return response_text, [], iteration

            # Active corpus verification
            verification = self.citation_svc.verify_against_corpus(raw_citations, chunks)

            not_found = verification["not_found"]
            corpus_found = verification["corpus_found"]

            # If everything verified, we're done
            if not not_found and not corpus_found:
                all_verified = verification["verified"]
                return response_text, all_verified, iteration

            # If there are corpus_found items, they're now verified — add to chunks for next pass
            for cf in corpus_found:
                chunks.append({
                    "chunk_id": f"corpus_verified_{len(chunks)}",
                    "content": cf.get("content", ""),
                    "metadata": {
                        "code_name": cf.get("corpus_code_name", cf.get("code_name", "")),
                        "article_number": cf.get("article_number", ""),
                        "article_url": cf.get("article_url", ""),
                    },
                })

            # If nothing is truly hallucinated, we're done
            if not not_found:
                all_citations = verification["verified"] + corpus_found
                return response_text, all_citations, iteration

            # Build correction context and ask Flash to fix
            verification_text = self._format_verification_results(verification)
            correction_prompt = (
                f"═══ AI'S ORIGINAL RESPONSE ═══\n{response_text}\n\n"
                f"═══ CITATION VERIFICATION RESULTS ═══\n{verification_text}"
            )
            try:
                corrected = await self.gemini.generate(
                    prompt=correction_prompt,
                    system_instruction=CITATION_VERIFIER.template,
                    temperature=CITATION_VERIFIER.temperature,
                    model_name=settings.gemini_chat_model,  # Flash
                )
                if corrected and corrected.strip():
                    response_text = corrected
                    logger.info(
                        "pipeline_phase_3_corrected",
                        iteration=iteration,
                        not_found=len(not_found),
                    )
            except Exception as e:
                logger.warning("pipeline_phase_3_correction_failed", error=str(e))
                break

        # Final extraction after all iterations
        final_citations = self.citation_svc.extract_citations(response_text)
        verified = self.citation_svc.verify_citations(final_citations, chunks)
        return response_text, verified, MAX_VERIFY_ITERATIONS

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _format_law_context(chunks: list[dict]) -> str:
        """Format retrieved chunks into a context block for Gemini."""
        if not chunks:
            return ""
        parts: list[str] = []
        for i, chunk in enumerate(chunks[:30], 1):  # Cap at 30
            meta = chunk.get("metadata", {})
            code = meta.get("code_name", "")
            article = meta.get("article_number", "")
            url = meta.get("article_url", "")
            content = chunk.get("content", "")
            parts.append(
                f"[{i}] {code}, {article}\n"
                f"   URL: {url}\n"
                f"   {content[:2000]}\n"
            )
        return "\n".join(parts)

    @staticmethod
    def _select_tools(
        case_file_id: str | None,
        is_case_chat: bool,
    ) -> list[types.Tool]:
        """Select which tools to make available based on context."""
        if case_file_id:
            return FULL_CASE_TOOLS
        if is_case_chat:
            return CASE_CREATION_TOOLS
        return ALWAYS_TOOLS

    @staticmethod
    def _history_to_contents(
        history: list[dict[str, str]],
    ) -> list[types.Content]:
        """Convert DB history dicts to Gemini Content objects for chat seeding.

        Handles consecutive same-role messages by merging them (Gemini
        requires strictly alternating user/model roles).
        """
        if not history:
            return []

        raw = []
        for msg in history[-20:]:
            role = "user" if msg.get("role") == "user" else "model"
            raw.append({"role": role, "content": msg.get("content", "")})

        # Merge consecutive same-role messages
        merged: list[dict[str, str]] = []
        for msg in raw:
            if merged and merged[-1]["role"] == msg["role"]:
                merged[-1]["content"] += "\n\n" + msg["content"]
            else:
                merged.append(msg.copy())

        # History must start with "user" for Gemini
        if merged and merged[0]["role"] == "model":
            merged.pop(0)

        return [
            types.Content(
                role=m["role"],
                parts=[types.Part(text=m["content"])],
            )
            for m in merged
        ]

    @staticmethod
    def _format_verification_results(verification: dict) -> str:
        """Format verification results for the citation corrector prompt."""
        parts: list[str] = []

        for item in verification.get("verified", []):
            parts.append(
                f"VERIFIED: {item.get('code_name', '')}, {item.get('article_number', '')} — ✅ Correct"
            )

        for item in verification.get("corpus_found", []):
            parts.append(
                f"FOUND_DIFFERENT: {item.get('code_name', '')}, {item.get('article_number', '')} — "
                f"Found in database as: {item.get('corpus_code_name', '')}. "
                f"Content: {item.get('content', '')[:300]}"
            )

        for item in verification.get("not_found", []):
            parts.append(
                f"NOT_FOUND: {item.get('code_name', '')}, {item.get('article_number', '')} — "
                f"❌ This article was NOT found in our database. It may be hallucinated."
            )

        return "\n\n".join(parts)


# ── Singleton ────────────────────────────────────────────────

_pipeline_service: AgentPipelineService | None = None


def get_agent_pipeline_service() -> AgentPipelineService:
    """Return the singleton AgentPipelineService."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = AgentPipelineService()
    return _pipeline_service
