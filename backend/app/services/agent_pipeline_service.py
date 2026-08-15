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

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

from google.genai import types

from app.config.constants import GEMINI_TEMPERATURE
from app.config.settings import settings
from app.integrations.vertex_ai_client import VertexAIClient, get_vertex_ai_client
from app.prompts.agent_planning import AGENT_PLANNER, CITATION_VERIFIER, FAITHFULNESS_CHECKER
from app.services.citation_service import CitationService, get_citation_service
from app.services.rag_retrieval_service import RAGRetrievalService, get_rag_service
from app.services.trace_service import record_step
from app.tools.case_tools import ALWAYS_TOOLS, CASE_CREATION_TOOLS, FULL_CASE_TOOLS
from app.utils.logger import get_logger
from app.services.model_config_service import cheap_model, strong_model

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
            record_step("direct_response_returned", response_text=plan.direct_response)
            return PipelineResult(
                response_text=plan.direct_response,
                plan=plan,
            )

        # ── Phase 2: Execute ─────────────────────────────────
        response_text, chunks, tool_results, full_code_injected = await self._phase_2_execute(
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

        # ── Generation contract (plan 2.2 / 2.3 / 2.4) ───────
        if settings.faithfulness_check:
            verified_response = await self._faithfulness_pass(verified_response, chunks)

        from app.services.citation_service import check_anchoring
        anchoring = check_anchoring(verified_response)
        record_step("anchoring_check", **anchoring)
        if (
            settings.anchoring_repair
            and anchoring["unanchored"]
            and anchoring["unanchored_rate"] >= 0.05
        ):
            verified_response = await self._anchoring_repair(
                verified_response, anchoring
            )
            anchoring = check_anchoring(verified_response)
            record_step("anchoring_check", repaired=True, **anchoring)

        verified_response = self._apply_uncertainty_policy(
            verified_response, plan, chunks, tool_results, full_code_injected
        )
        verified_response = self._apply_deadline_guard(verified_response)
        verified_response = self._repair_matsne_links(
            verified_response, chunks, verified_citations
        )
        if settings.anchoring_repair:
            verified_response = await self._practice_attribution_guard(
                verified_response, chunks
            )
        verified_response = self._apply_language_fixups(verified_response)

        record_step(
            "pipeline_result",
            response_text=verified_response,
            citations=verified_citations,
            chunk_count=len(chunks),
            verify_iterations=iterations,
            tool_calls=[t.tool_name for t in tool_results],
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
            chat = await self.gemini.create_chat(
                history=chat_history,
                system_instruction=AGENT_PLANNER.template,
                temperature=AGENT_PLANNER.temperature,
                max_output_tokens=AGENT_PLANNER.max_output_tokens,
                model_name=await cheap_model(),  # CHEAP tier
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
                plan = PipelinePlan(
                    needs_rag=result.get("needs_rag", True),
                    direct_response=result.get("direct_response"),
                    search_queries=[
                        q for q in result.get("search_queries", [])
                        if isinstance(q, str) and q.strip()
                    ],
                    legal_entities=result.get("legal_entities", []),
                    intent=result.get("intent", "legal_question"),
                )
                record_step(
                    "phase_1_plan",
                    model=await cheap_model(),
                    planner_raw_response=raw,
                    intent=plan.intent,
                    needs_rag=plan.needs_rag,
                    search_queries=plan.search_queries,
                    legal_entities=plan.legal_entities,
                    direct_response=plan.direct_response,
                )
                return plan
        except Exception as e:
            logger.warning("pipeline_phase_1_failed", error=str(e))
            record_step(
                "phase_1_plan_failed",
                error=str(e),
                fallback_queries=[user_message],
            )

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

        # Stage A2: whole-code injection (grounding mechanism C, flag-gated).
        # When the full code is in context, statute chunks are redundant —
        # court practice and threshold chunks stay.
        full_code_context = ""
        if settings.full_code_injection and plan.needs_rag:
            full_code_context = await self._build_full_code_context(user_message)
            if full_code_context:
                chunks = [
                    c for c in chunks
                    if (c.get("metadata") or {}).get("_collection") != "georgian_laws"
                    or (c.get("metadata") or {}).get("chunk_type") == "threshold"
                ]

        # Stage B: Create native chat session with history + tools
        law_context = self._format_law_context(chunks)
        tools = self._select_tools(case_file_id, is_case_chat)
        chat_history = self._history_to_contents(history)

        chat = await self.gemini.create_chat(
            history=chat_history,
            system_instruction=system_prompt,
            tools=tools,
            temperature=GEMINI_TEMPERATURE,
            model_name=await strong_model(),
        )

        # Build the user message with law context prefix
        message_parts = []
        if full_code_context:
            message_parts.append(
                "FULL LEGAL CODE (complete, authoritative — cite articles "
                f"directly from here):\n{full_code_context}\n\n"
            )
        if law_context:
            message_parts.append(f"RETRIEVED LAW ARTICLES:\n{law_context}\n\n")
        message_parts.append(user_message)
        full_message = "\n".join(message_parts)

        record_step(
            "llm_generation_request",
            model=await strong_model(),
            system_prompt=system_prompt,
            history_message_count=len(history),
            available_tools=self._tool_names(tools),
            message_with_law_context=full_message,
        )

        # Stage C: Send message and handle tool loop
        tool_results: list[ToolResultInfo] = []
        response_text = ""

        for iteration in range(MAX_TOOL_CALLS_PER_MESSAGE + 1):
            response = await chat.send_message(full_message)

            # Collect ALL function calls in this turn. Gemini emits parallel
            # function calls when multiple tools are declared; replying with a
            # single function_response when several were requested triggers a
            # 400 (mismatched call/response count), so we execute every call
            # and send all responses back together.
            parts = (
                response.candidates[0].content.parts
                if response.candidates and response.candidates[0].content.parts
                else []
            )
            function_calls = [p.function_call for p in parts if p.function_call]
            has_function_call = bool(function_calls)

            if has_function_call:
                record_step(
                    "llm_requested_tools",
                    iteration=iteration,
                    calls=[
                        {"tool": fc.name, "args": dict(fc.args) if fc.args else {}}
                        for fc in function_calls
                    ],
                )
                response_parts = []
                for fc in function_calls:
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
                    record_step(
                        "tool_executed",
                        iteration=iteration,
                        tool=fc_name,
                        args=fc_args,
                        status=tool_result.get("_status", "executed"),
                        requires_confirmation=tool_result.get("_requires_confirmation", False),
                        result={k: v for k, v in tool_result.items() if not k.startswith("_")},
                    )

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
                    response_parts.append(
                        types.Part.from_function_response(
                            name=fc_name,
                            response=clean_result,
                        )
                    )

                # Reply with all function responses for this turn at once
                full_message = response_parts

            if not has_function_call:
                # Extract text response
                if response.text:
                    response_text = response.text
                record_step("llm_response", iteration=iteration, text=response.text or "")
                break

        if not response_text and response.text:
            response_text = response.text

        return response_text, chunks, tool_results, bool(full_code_context)

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

        # Deterministic navigation tools (grounding mechanism B) — no DB needed
        if tool_name == "get_article":
            return await self._handle_get_article(args)
        if tool_name == "browse_code":
            return await self._handle_browse_code(args)

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

    async def _build_full_code_context(self, user_message: str) -> str:
        """Mechanism C: full text of the classified domain's code(s), if they fit.

        Only unambiguous domain→code mappings are injected
        (FULL_CODE_INJECTION_DOMAIN_CODES) and only when every code fully fits
        the char budget — a truncated code would defeat the guarantee.
        """
        from app.config.constants import FULL_CODE_INJECTION_DOMAIN_CODES
        from app.services.article_store_service import get_article_store_service
        from app.services.legal_classifier_service import KeywordClassifier

        classification = KeywordClassifier().classify(user_message)
        codes = FULL_CODE_INJECTION_DOMAIN_CODES.get(classification.primary, [])
        if not codes or classification.confidence <= 0.1:
            return ""

        store = get_article_store_service()
        budget = settings.full_code_injection_max_chars
        parts: list[str] = []
        injected: list[dict[str, Any]] = []
        for code in codes:
            result = await asyncio.to_thread(store.get_code_full_text, code)
            if result is None:
                continue
            text, article_count = result
            if len(text) > budget:
                logger.info(
                    "full_code_injection_skipped",
                    code=code,
                    chars=len(text),
                    budget=budget,
                )
                continue
            budget -= len(text)
            parts.append(text)
            injected.append({"code": code, "articles": article_count, "chars": len(text)})

        if not injected:
            return ""
        record_step(
            "full_code_injected",
            domain=classification.primary,
            domain_confidence=classification.confidence,
            codes=injected,
            total_chars=sum(i["chars"] for i in injected),
        )
        logger.info(
            "full_code_injected",
            domain=classification.primary,
            codes=[i["code"] for i in injected],
        )
        return "\n\n".join(parts)

    async def _handle_get_article(self, args: dict) -> dict:
        """get_article tool — deterministic full-article lookup via the article store."""
        from app.services.article_store_service import get_article_store_service

        code = args.get("code", "")
        article = args.get("article", "")
        paragraph = args.get("paragraph")

        store = get_article_store_service()
        result = await asyncio.to_thread(store.get_article, code, article, paragraph)
        if result:
            out = {
                "found": True,
                "code": result["code_name"],
                "article": result["article_number"],
                "title": result["article_title"] or "",
                "content": result["content_ka"][:8000],
                "url": result["article_url"],
                "cross_references": result["cross_references"],
                "is_repealed": result["is_repealed"],
            }
            if paragraph:
                p = result.get("paragraph")
                out["paragraph"] = (
                    {"number": p["number"], "text": p["text"]} if p else None
                )
                if p is None:
                    out["paragraph_note"] = (
                        f"Paragraph {paragraph} not found in this article."
                    )
            return out

        # Fall back to the live chroma corpus (covers store gaps)
        hit = self.citation_svc._search_corpus_exact(article, code)
        if hit:
            return {
                "found": True,
                "code": hit.get("metadata", {}).get("code_name", ""),
                "article": hit.get("metadata", {}).get("article_number", ""),
                "content": hit.get("content", "")[:8000],
                "url": hit.get("metadata", {}).get("article_url", ""),
                "source": "vector_corpus_fallback",
            }
        return {
            "found": False,
            "message": (
                f"Article '{article}' of '{code}' does not exist in the corpus. "
                "Do NOT cite it."
            ),
        }

    async def _handle_browse_code(self, args: dict) -> dict:
        """browse_code tool — list article numbers/titles of a code (navigation)."""
        from app.services.article_store_service import get_article_store_service

        code = args.get("code", "")
        chapter = args.get("chapter")

        store = get_article_store_service()
        articles = await asyncio.to_thread(store.get_code_articles, code, chapter)
        if not articles:
            known = [c["code_name"] for c in store.list_codes()]
            return {
                "found": False,
                "message": f"Code '{code}' not found in the article store.",
                "available_codes": known,
            }
        return {
            "found": True,
            "code": articles[0]["code_name"],
            "article_count": len(articles),
            "articles": [
                {
                    "article": a["article_number"],
                    "title": a["article_title"] or "",
                    "chapter": a["chapter"] or "",
                }
                for a in articles[:200]
            ],
        }

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
            verified = self.citation_svc.verify_citations(raw_citations, chunks)
            record_step(
                "citation_verification",
                skipped_corpus_check=True,
                reason="empty response" if not response_text else "no retrieved chunks",
                extracted=raw_citations,
                verified=verified,
            )
            return response_text, verified, 0

        for iteration in range(MAX_VERIFY_ITERATIONS):
            raw_citations = self.citation_svc.extract_citations(response_text)
            case_numbers = self.citation_svc.extract_case_citations(response_text)
            if not raw_citations and not case_numbers:
                record_step("citation_verification", iteration=iteration, extracted=[])
                return response_text, [], iteration

            # Active corpus verification
            verification = self.citation_svc.verify_against_corpus(raw_citations, chunks)

            not_found = verification["not_found"]
            corpus_found = verification["corpus_found"]

            record_step(
                "citation_verification",
                iteration=iteration,
                extracted=raw_citations,
                verified=verification["verified"],
                corpus_found=corpus_found,
                not_found=not_found,
            )

            # Court-case citation verification (plan 3.1)
            case_verification = self.citation_svc.verify_case_citations(case_numbers)
            hallucinated_cases = case_verification["not_found"]
            if case_numbers:
                record_step(
                    "case_citation_verification",
                    iteration=iteration,
                    extracted=case_numbers,
                    verified=case_verification["verified"],
                    not_found=hallucinated_cases,
                )

            # Sub-article (paragraph) verification (plan 3.2)
            paragraph_issues = self._verify_subarticles(
                verification["verified"] + corpus_found
            )
            if any(c.get("paragraph") for c in raw_citations):
                record_step(
                    "subarticle_verification",
                    iteration=iteration,
                    issues=paragraph_issues,
                )

            # If everything verified, we're done
            if (
                not not_found
                and not corpus_found
                and not hallucinated_cases
                and not paragraph_issues
            ):
                all_verified = verification["verified"]
                return response_text, all_verified, iteration

            # RETRIEVAL REPAIR (grounding mechanism A at generation time):
            # a citation that exists in the corpus but was NOT in the model's
            # context means the claim came from pretraining — fetch the FULL
            # article text and force a confirm/correct pass against it instead
            # of accepting the citation on faith.
            if corpus_found:
                from app.services.article_store_service import get_article_store_service
                store = get_article_store_service()
                repaired: list[dict] = []
                for cf in corpus_found:
                    full = store.get_article(
                        cf.get("corpus_code_name") or cf.get("code_name", ""),
                        cf.get("article_number", ""),
                    )
                    if full:
                        cf["content"] = full["content_ka"][:6000]
                        cf["article_url"] = full["article_url"] or cf.get("article_url", "")
                    repaired.append({
                        "code_name": cf.get("code_name", ""),
                        "article_number": cf.get("article_number", ""),
                        "full_text_from_store": full is not None,
                    })
                record_step(
                    "retrieval_repair",
                    iteration=iteration,
                    repaired=repaired,
                    hallucinated=[
                        {k: c.get(k, "") for k in ("code_name", "article_number")}
                        for c in not_found
                    ],
                )
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

            # Build correction context and ask Flash to confirm/correct
            verification_text = self._format_verification_results(verification)
            extra_issues: list[str] = []
            if hallucinated_cases:
                available_cases = sorted({
                    (c.get("metadata") or {}).get("case_id", "")
                    for c in chunks
                    if (c.get("metadata") or {}).get("_collection")
                    in ("court_practice", "grand_chamber")
                } - {""})
                for hc in hallucinated_cases:
                    extra_issues.append(
                        f"NOT_FOUND (COURT CASE): საქმე {hc['case_number']} — ❌ this case "
                        "number is NOT in our court practice database. Remove it or "
                        "replace it with one of the VERIFIED cases actually in context: "
                        f"{', '.join(available_cases) if available_cases else '(none — remove the claim or drop the case reference)'}"
                    )
            for pi in paragraph_issues:
                extra_issues.append(
                    f"PARAGRAPH_NOT_FOUND: {pi['code_name']}, {pi['article_number']} "
                    f"ნაწილი {pi['paragraph']} — ❌ the article has no such paragraph "
                    f"(existing: {pi['available_paragraphs']}). Fix the reference."
                )
            if extra_issues:
                verification_text = "\n\n".join([verification_text, *extra_issues]).strip()
            correction_prompt = (
                f"═══ AI'S ORIGINAL RESPONSE ═══\n{response_text}\n\n"
                f"═══ CITATION VERIFICATION RESULTS ═══\n{verification_text}"
            )
            try:
                corrected = await self.gemini.generate(
                    prompt=correction_prompt,
                    system_instruction=CITATION_VERIFIER.template,
                    temperature=CITATION_VERIFIER.temperature,
                    model_name=await cheap_model(),  # CHEAP tier
                )
                if corrected and corrected.strip():
                    response_text = corrected
                    logger.info(
                        "pipeline_phase_3_corrected",
                        iteration=iteration,
                        not_found=len(not_found),
                    )
                    record_step(
                        "citation_correction",
                        iteration=iteration,
                        hallucinated_citations=not_found,
                        corrected_text=corrected,
                    )
            except Exception as e:
                logger.warning("pipeline_phase_3_correction_failed", error=str(e))
                break

        # Final extraction after all iterations
        final_citations = self.citation_svc.extract_citations(response_text)
        verified = self.citation_svc.verify_citations(final_citations, chunks)
        return response_text, verified, MAX_VERIFY_ITERATIONS

    @staticmethod
    def _verify_subarticles(citations: list[dict]) -> list[dict]:
        """Plan 3.2: check cited paragraphs ("48.8") against the article store.

        Returns issues for citations whose paragraph does not exist in the
        article's paragraph list (articles without structured paragraphs are
        skipped — nothing to verify against).
        """
        from app.services.article_store_service import get_article_store_service

        issues: list[dict] = []
        store = get_article_store_service()
        for c in citations:
            paragraph = c.get("paragraph")
            if not paragraph:
                continue
            art = store.get_article(
                c.get("corpus_code_name") or c.get("code_name", ""),
                c.get("article_number", ""),
            )
            if not art or not art["paragraphs"]:
                continue
            numbers = [str(p.get("number")) for p in art["paragraphs"]]
            if str(paragraph) not in numbers:
                issues.append({
                    "code_name": c.get("code_name", ""),
                    "article_number": c.get("article_number", ""),
                    "paragraph": paragraph,
                    "available_paragraphs": numbers,
                })
        return issues

    # ── Generation contract (plan 2.3 / 2.4) ─────────────────

    async def _faithfulness_pass(
        self, response_text: str, chunks: list[dict]
    ) -> str:
        """Plan 2.3: batched Flash check that every specific claim is supported.

        Unsupported claims trigger one correction pass via the citation
        verifier prompt. Any failure leaves the response unchanged.
        """
        if not response_text or not chunks:
            return response_text
        context_digest = "\n\n".join(
            f"[{i}] {(c.get('metadata') or {}).get('code_name', '')} "
            f"{(c.get('metadata') or {}).get('article_number', '')}\n"
            f"{c.get('content', '')[:1200]}"
            for i, c in enumerate(chunks[:30], 1)
        )
        prompt = (
            f"═══ LEGAL CONTEXT ═══\n{context_digest}\n\n"
            f"═══ AI RESPONSE ═══\n{response_text}"
        )
        try:
            verdict = await self.gemini.generate_json(
                prompt=prompt,
                system_instruction=FAITHFULNESS_CHECKER.template,
                temperature=FAITHFULNESS_CHECKER.temperature,
                model_name=await cheap_model(),
            )
        except Exception as e:
            logger.warning("faithfulness_check_failed", error=str(e))
            record_step("faithfulness_check", failed=True, error=str(e))
            return response_text

        if not isinstance(verdict, dict):
            record_step("faithfulness_check", failed=True, error="non-dict verdict")
            return response_text

        unsupported = verdict.get("unsupported") or []
        record_step(
            "faithfulness_check",
            supported_count=verdict.get("supported_count"),
            general_count=verdict.get("general_count"),
            unsupported=unsupported,
        )
        if not unsupported:
            return response_text

        issues = "\n\n".join(
            f"NOT_FOUND: {u.get('statement', '')} — ❌ {u.get('reason', 'unsupported by context')}"
            for u in unsupported
        )
        correction_prompt = (
            f"═══ AI'S ORIGINAL RESPONSE ═══\n{response_text}\n\n"
            f"═══ CITATION VERIFICATION RESULTS ═══\n"
            f"The following SPECIFIC claims are NOT supported by the legal context. "
            f"Remove or soften each one (or mark it explicitly as unverified):\n\n{issues}"
        )
        try:
            corrected = await self.gemini.generate(
                prompt=correction_prompt,
                system_instruction=CITATION_VERIFIER.template,
                temperature=CITATION_VERIFIER.temperature,
                model_name=await cheap_model(),
            )
            if corrected and corrected.strip():
                record_step(
                    "faithfulness_correction",
                    unsupported_count=len(unsupported),
                    corrected_text=corrected,
                )
                return corrected
        except Exception as e:
            logger.warning("faithfulness_correction_failed", error=str(e))
        return response_text

    def _apply_uncertainty_policy(
        self,
        response_text: str,
        plan: PipelinePlan,
        chunks: list[dict],
        tool_results: list[ToolResultInfo],
        full_code_injected: bool,
    ) -> str:
        """Plan 2.4: a statute-type answer with ZERO statute grounding must
        open with an explicit disclaimer."""
        if not response_text or not plan.needs_rag:
            return response_text

        statute_chunks = any(
            (c.get("metadata") or {}).get("_collection") == "georgian_laws"
            for c in chunks
        )
        tool_grounded = any(
            t.tool_name in ("get_article", "search_law", "browse_code")
            and t.result.get("found")
            for t in tool_results
        )
        if statute_chunks or tool_grounded or full_code_injected:
            return response_text

        record_step(
            "uncertainty_disclaimer_added",
            reason="statute-type question with zero statute grounding",
        )
        from app.config.constants import UNGROUNDED_STATUTE_DISCLAIMER_KA
        return UNGROUNDED_STATUTE_DISCLAIMER_KA + response_text

    async def _anchoring_repair(
        self, response_text: str, anchoring: dict
    ) -> str:
        """Plan 2.2: anchor claim paragraphs using ONLY citations already in
        the response (no new sources may be introduced)."""
        unanchored_list = "\n".join(f"- {s}" for s in anchoring.get("unanchored_samples", []))
        prompt = (
            "You are an editor for a Georgian legal AI. The response below contains "
            "verified citations (article links), but the listed paragraphs state legal "
            "claims WITHOUT a citation in their own paragraph/section.\n"
            "Rewrite the response so every such paragraph carries the correct citation, "
            "chosen ONLY from citations ALREADY present elsewhere in this response. "
            "Do NOT invent or add any new article, case number, or link. If no existing "
            "citation supports a claim, soften it or mark it explicitly as general guidance. "
            "Keep everything else — structure, tone, language (Georgian) — unchanged. "
            "Return the full corrected response text only.\n\n"
            f"═══ UNANCHORED PARAGRAPHS ═══\n{unanchored_list}\n\n"
            f"═══ RESPONSE ═══\n{response_text}"
        )
        try:
            repaired = await self.gemini.generate(
                prompt=prompt,
                temperature=0.2,
                model_name=await cheap_model(),
            )
            if repaired and repaired.strip():
                record_step(
                    "anchoring_repair",
                    unanchored_before=anchoring.get("unanchored"),
                    repaired_text=repaired,
                )
                return repaired
        except Exception as e:
            logger.warning("anchoring_repair_failed", error=str(e))
        return response_text

    _MATSNE_LINK_RE = re.compile(
        r"\[([^\]]+)\]\((https?://matsne\.gov\.ge[^)\s]+)\)"
    )

    def _repair_matsne_links(
        self,
        response_text: str,
        chunks: list[dict],
        verified_citations: list[dict],
    ) -> str:
        """Structural link integrity: every matsne link in the response must
        byte-match a corpus/store URL. Unknown links are re-pointed at the
        article the label cites (via the article store) or downgraded to
        plain text — an invented link never reaches the user."""
        if not response_text or "matsne.gov.ge" not in response_text:
            return response_text

        from app.services.article_store_service import get_article_store_service
        store = get_article_store_service()

        known: set[str] = {
            (c.get("metadata") or {}).get("article_url", "") for c in chunks
        }
        known |= {c.get("article_url", "") for c in verified_citations}
        known.discard("")

        repaired: list[dict] = []

        def _fix(match: re.Match) -> str:
            label, url = match.group(1), match.group(2)
            clean_url = url.rstrip(".,;")
            if clean_url in known or store.has_article_url(clean_url):
                return match.group(0)
            label_citations = self.citation_svc.extract_citations(label)
            if label_citations:
                cit = label_citations[0]
                art = store.get_article(cit["code_name"], cit["article_number"])
                if art and art["article_url"]:
                    repaired.append(
                        {"label": label, "from": url, "to": art["article_url"]}
                    )
                    return f"[{label}]({art['article_url']})"
            repaired.append({"label": label, "from": url, "to": None})
            return label  # drop the invented link, keep the text

        fixed = self._MATSNE_LINK_RE.sub(_fix, response_text)
        if repaired:
            record_step("link_repair", links=repaired)
        return fixed

    # Latin fragments the model habitually mixes into Georgian text despite
    # the language rule — replaced deterministically (answer must be 100% Georgian)
    _LANGUAGE_FIXUPS = {
        " vs. ": " და ",
        " vs ": " და ",
        " etc.": " და ა.შ.",
        " e.g.": " მაგ.",
        " i.e.": " ანუ",
    }

    # Internal case-schema enum values (case_tools.py) the case-agent tends to
    # echo verbatim into Georgian responses, e.g. "(კლასიფიკაცია: *favorable*)"
    # or "(პრიორიტეტი: high)". Deterministically translated so C1 holds on the
    # tools path regardless of model tier.
    _CASE_ENUM_FIXUPS = {
        "favorable": "ხელსაყრელი",
        "unfavorable": "არახელსაყრელი",
        "neutral": "ნეიტრალური",
        "strong": "ძლიერი",
        "moderate": "ზომიერი",
        "weak": "სუსტი",
        "high": "მაღალი",
        "medium": "საშუალო",
        "low": "დაბალი",
    }
    _CASE_ENUM_RE = re.compile(
        r"\b(" + "|".join(_CASE_ENUM_FIXUPS) + r")\b", re.IGNORECASE
    )

    # Pure-ASCII parenthetical glosses the model sometimes appends, e.g. a
    # heading "საქმის მართვა (Case Agent)". The char class excludes ':' and '#'
    # so markdown/matsne URL parens — "(https://matsne.gov.ge/...#article_48)" —
    # never match and are preserved.
    _ASCII_GLOSS_RE = re.compile(r"\s*\(([A-Za-z][A-Za-z .,&/'-]*)\)")

    def _apply_language_fixups(self, response_text: str) -> str:
        fixed = response_text
        applied: list[str] = []
        for latin, georgian in self._LANGUAGE_FIXUPS.items():
            if latin in fixed:
                fixed = fixed.replace(latin, georgian)
                applied.append(latin.strip())
        # Translate internal English case-schema enum values (C1, tools path).
        enum_hits = {m.group(0).lower() for m in self._CASE_ENUM_RE.finditer(fixed)}
        if enum_hits:
            fixed = self._CASE_ENUM_RE.sub(
                lambda m: self._CASE_ENUM_FIXUPS[m.group(0).lower()], fixed
            )
            applied.extend(sorted(enum_hits))
        # Strip stray English parenthetical glosses (Georgian-only policy, C1).
        glosses = self._ASCII_GLOSS_RE.findall(fixed)
        if glosses:
            fixed = self._ASCII_GLOSS_RE.sub("", fixed)
            applied.extend(f"({g})" for g in glosses)
        if applied:
            record_step("language_purity_fixups", replaced=applied)
        return fixed

    _PRACTICE_CLAIM_RE = re.compile(
        r"სასამართლო პრაქტიკ|პრაქტიკის (?:თანახმად|მიხედვით)|პრაქტიკით დადგენილ"
        r"|უზენაესმა|უზენაესი სასამართლოს განმარტ"
    )

    async def _practice_attribution_guard(
        self, response_text: str, chunks: list[dict]
    ) -> str:
        """Court-practice claims must name their case or stop claiming practice.

        When the response asserts "სასამართლო პრაქტიკის თანახმად…" without any
        case number while court decisions ARE in context, one Flash pass either
        attaches the supporting case №s from context (only if they truly
        support the claim) or rephrases the claim without practice attribution.
        """
        if not response_text or not self._PRACTICE_CLAIM_RE.search(response_text):
            return response_text
        from app.services.citation_service import CASE_NUMBER_PATTERN
        if CASE_NUMBER_PATTERN.search(response_text):
            return response_text
        court_cases = sorted({
            (c.get("metadata") or {}).get("case_id", "")
            for c in chunks
            if (c.get("metadata") or {}).get("_collection")
            in ("court_practice", "grand_chamber")
        } - {""})
        if not court_cases:
            return response_text

        prompt = (
            "You are an editor for a Georgian legal AI. The response below claims court "
            "practice (e.g. „სასამართლო პრაქტიკის თანახმად…\") WITHOUT citing any case "
            "number. The court decisions actually available in its context are: "
            f"{', '.join(court_cases)}.\n"
            "For every practice-based claim: if one of these cases genuinely supports it "
            "(you saw its text in the response's reasoning), attach that case number "
            "(e.g. „(საქმე №ას-543-2020)\"); otherwise rephrase the sentence so it does "
            "NOT claim court practice (state it as a general legal principle or drop it). "
            "NEVER invent a case number. Keep everything else unchanged, respond in "
            "Georgian, return the full corrected response text only.\n\n"
            f"═══ RESPONSE ═══\n{response_text}"
        )
        try:
            repaired = await self.gemini.generate(
                prompt=prompt,
                temperature=0.2,
                model_name=await cheap_model(),
            )
            if repaired and repaired.strip():
                record_step(
                    "practice_attribution_guard",
                    available_cases=court_cases,
                    corrected_text=repaired,
                )
                return repaired
        except Exception as e:
            logger.warning("practice_attribution_guard_failed", error=str(e))
        return response_text

    _ACTION_ADVICE_RE = re.compile(
        r"სასამართლო|საჩივ|სარჩელ|გაასაჩივრ|იჩივლ|მიმართ"
    )
    _DEADLINE_MENTION_RE = re.compile(
        r"ვადა|ვადაში|ვადის|დღის განმავლობაში|გადაამოწმ|დაუყოვნებლ"
    )

    def _apply_deadline_guard(self, response_text: str) -> str:
        """Plan 0.2, enforced structurally: legal-action advice without any
        deadline mention gets an explicit verify-the-deadline warning."""
        if not response_text:
            return response_text
        if self._ACTION_ADVICE_RE.search(response_text) and not self._DEADLINE_MENTION_RE.search(response_text):
            record_step("deadline_guard_added")
            from app.config.constants import DEADLINE_GUARD_KA
            return response_text + DEADLINE_GUARD_KA
        return response_text

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _format_law_context(chunks: list[dict]) -> str:
        """Format retrieved chunks into a context block for Gemini."""
        if not chunks:
            return ""
        parts: list[str] = []
        for i, chunk in enumerate(chunks[:30], 1):  # Cap at 30
            meta = chunk.get("metadata", {})
            url = meta.get("article_url", "")
            content = chunk.get("content", "")
            if meta.get("_collection") in ("court_practice", "grand_chamber"):
                # court chunks identify by case number — the model must SEE it
                # to be able to cite it (audit finding 3)
                court = "დიდი პალატა" if meta.get("_collection") == "grand_chamber" else "უზენაესი სასამართლო"
                header = (
                    f"[{i}] საქმე №{meta.get('case_id', '?')} "
                    f"({court}, {meta.get('year', '?')})"
                )
            else:
                header = f"[{i}] {meta.get('code_name', '')}, {meta.get('article_number', '')}"
            parts.append(
                f"{header}\n"
                f"   URL: {url}\n"
                f"   {content[:2000]}\n"
            )
        return "\n".join(parts)

    @staticmethod
    def _tool_names(tools: list[types.Tool]) -> list[str]:
        """Extract declared function names from Gemini Tool objects."""
        try:
            return [
                fd.name
                for tool in tools
                for fd in (tool.function_declarations or [])
            ]
        except Exception:
            return []

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
                f"FOUND_NOT_IN_CONTEXT: {item.get('code_name', '')}, {item.get('article_number', '')} — "
                f"Found in database as: {item.get('corpus_code_name', '')}. "
                f"ACTUAL ARTICLE TEXT:\n{item.get('content', '')[:2000]}"
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
