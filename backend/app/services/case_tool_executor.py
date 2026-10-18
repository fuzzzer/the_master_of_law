"""
Case tool executor — maps Gemini function calls to case file DB operations.

Handles tool execution, confirmation tracking via Redis, and audit logging.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.case_file_repository import CaseFileRepository
from app.tools.case_tools import DESTRUCTIVE_TOOLS
from app.utils.logger import get_logger

logger = get_logger(__name__)

CONFIRMATION_TTL_SECONDS = 600
MAX_TOOL_CALLS_PER_MESSAGE = 5


class ToolResult:
    """Result of a single tool execution."""

    def __init__(
        self,
        tool_name: str,
        status: str,
        result: dict[str, Any] | None = None,
        confirmation_id: str | None = None,
        description: str | None = None,
        requires_confirmation: bool = False,
    ):
        self.tool_name = tool_name
        self.status = status
        self.result = result or {}
        self.confirmation_id = confirmation_id
        self.description = description
        self.requires_confirmation = requires_confirmation

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "tool_name": self.tool_name,
            "status": self.status,
            "result": self.result,
            "requires_confirmation": self.requires_confirmation,
        }
        if self.confirmation_id:
            d["confirmation_id"] = self.confirmation_id
        if self.description:
            d["description"] = self.description
        return d


class CaseToolExecutor:
    """Executes case modification tools called by Gemini."""

    def __init__(
        self,
        db: AsyncSession,
        redis_client: Any = None,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ):
        self._db = db
        self._repo = CaseFileRepository(db)
        self._redis = redis_client
        self._user_id = user_id
        self._conversation_id = conversation_id

    async def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
        case_file_id: str,
        user_id: str,
    ) -> ToolResult:
        """Execute a tool call or defer it for confirmation."""
        if tool_name in DESTRUCTIVE_TOOLS:
            return await self._defer_for_confirmation(
                tool_name, args, case_file_id, user_id,
            )

        handler = self._get_handler(tool_name)
        if not handler:
            return ToolResult(
                tool_name=tool_name,
                status="error",
                result={"error": f"Unknown tool: {tool_name}"},
            )

        try:
            result = await handler(case_file_id, args)
            self._log_execution(user_id, tool_name, args, "executed")
            return ToolResult(
                tool_name=tool_name,
                status="executed",
                result=result,
            )
        except Exception as e:
            logger.error("tool_execution_failed", tool=tool_name, error=str(e))
            return ToolResult(
                tool_name=tool_name,
                status="error",
                result={"error": str(e)},
            )

    async def confirm_pending(
        self,
        confirmation_id: str,
        user_id: str,
        confirmed: bool,
    ) -> ToolResult:
        """Execute or reject a pending destructive action."""
        pending = await self._load_pending(confirmation_id)
        if not pending:
            return ToolResult(
                tool_name="unknown",
                status="error",
                result={"error": "Confirmation expired or not found"},
            )

        if pending["user_id"] != user_id:
            return ToolResult(
                tool_name=pending["tool_name"],
                status="error",
                result={"error": "User mismatch"},
            )

        if not confirmed:
            await self._clear_pending(confirmation_id)
            return ToolResult(
                tool_name=pending["tool_name"],
                status="rejected",
            )

        handler = self._get_handler(pending["tool_name"])
        if not handler:
            return ToolResult(
                tool_name=pending["tool_name"],
                status="error",
                result={"error": "Handler not found"},
            )

        try:
            result = await handler(pending["case_file_id"], pending["args"])
            await self._clear_pending(confirmation_id)
            self._log_execution(user_id, pending["tool_name"], pending["args"], "confirmed_executed")
            return ToolResult(
                tool_name=pending["tool_name"],
                status="executed",
                result=result,
            )
        except Exception as e:
            return ToolResult(
                tool_name=pending["tool_name"],
                status="error",
                result={"error": str(e)},
            )

    def _get_handler(self, tool_name: str):
        handlers = {
            "get_case_summary": self._handle_get_case_summary,
            "add_fact": self._handle_add_fact,
            "edit_fact": self._handle_edit_fact,
            "delete_fact": self._handle_delete_fact,
            "add_argument": self._handle_add_argument,
            "delete_argument": self._handle_delete_argument,
            "link_article": self._handle_link_article,
            "unlink_article": self._handle_unlink_article,
            "set_strategy": self._handle_set_strategy,
            "add_action_item": self._handle_add_action_item,
            "complete_action_item": self._handle_complete_action_item,
            "delete_action_item": self._handle_delete_action_item,
            "add_risk": self._handle_add_risk,
            "create_case": self._handle_create_case,
            "build_case_analysis": self._handle_build_case_analysis,
        }
        return handlers.get(tool_name)

    # ── Tool Handlers ────────────────────────────────────────

    async def _handle_get_case_summary(self, case_file_id: str, _args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        return {
            "title": cf.title,
            "status": cf.status,
            "facts": cf.facts,
            "evidence": cf.evidence,
            "applicable_laws": cf.applicable_laws,
            "defense_strategies": cf.defense_strategies,
            "prosecution_args": cf.prosecution_args,
            "action_checklist": cf.action_checklist,
            "unclear_items": cf.unclear_items,
        }

    async def _handle_add_fact(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        facts = cf.facts or {}
        fact_id = f"ai_fact_{uuid.uuid4().hex[:8]}"
        classification = args.get("classification", "neutral")
        text = args["text"]

        if "items" not in facts:
            facts["items"] = []
        facts["items"].append({
            "id": fact_id,
            "text": text,
            "classification": classification,
        })
        await self._repo.update(uuid.UUID(case_file_id), facts=facts)
        return {"fact_id": fact_id, "text": text, "classification": classification}

    async def _handle_edit_fact(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        facts = cf.facts or {}
        items = facts.get("items", [])
        fact_id = args["fact_id"]
        for item in items:
            if item.get("id") == fact_id:
                if "text" in args:
                    item["text"] = args["text"]
                if "classification" in args:
                    item["classification"] = args["classification"]
                await self._repo.update(uuid.UUID(case_file_id), facts=facts)
                return {"fact_id": fact_id, "updated": True}
        return {"error": f"Fact {fact_id} not found"}

    async def _handle_delete_fact(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        facts = cf.facts or {}
        items = facts.get("items", [])
        fact_id = args["fact_id"]
        original_len = len(items)
        facts["items"] = [i for i in items if i.get("id") != fact_id]
        if len(facts["items"]) == original_len:
            return {"error": f"Fact {fact_id} not found"}
        await self._repo.update(uuid.UUID(case_file_id), facts=facts)
        return {"deleted_id": fact_id}

    async def _handle_add_argument(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        pros_args = cf.prosecution_args or []
        arg_id = f"ai_arg_{uuid.uuid4().hex[:8]}"
        new_arg = {
            "id": arg_id,
            "title": args["title"],
            "explanation": args["explanation"],
            "strength": args.get("strength", "moderate"),
        }
        pros_args.append(new_arg)
        await self._repo.update(uuid.UUID(case_file_id), prosecution_args=pros_args)
        return {"argument_id": arg_id, "title": args["title"]}

    async def _handle_delete_argument(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        pros_args = cf.prosecution_args or []
        arg_id = args["argument_id"]
        original_len = len(pros_args)
        new_args = [a for a in pros_args if a.get("id") != arg_id]
        if len(new_args) == original_len:
            return {"error": f"Argument {arg_id} not found"}
        await self._repo.update(uuid.UUID(case_file_id), prosecution_args=new_args)
        return {"deleted_id": arg_id}

    async def _handle_link_article(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        laws = cf.applicable_laws or {}
        if "linked" not in laws:
            laws["linked"] = []
        article_id = f"ai_art_{uuid.uuid4().hex[:8]}"
        laws["linked"].append({
            "id": article_id,
            "code_name": args["code_name"],
            "article_number": args["article_number"],
            "snippet": args.get("snippet", ""),
        })
        await self._repo.update(uuid.UUID(case_file_id), applicable_laws=laws)
        return {
            "article_id": article_id,
            "code_name": args["code_name"],
            "article_number": args["article_number"],
        }

    async def _handle_unlink_article(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        laws = cf.applicable_laws or {}
        linked = laws.get("linked", [])
        article_id = args["article_id"]
        original_len = len(linked)
        laws["linked"] = [a for a in linked if a.get("id") != article_id]
        if len(laws["linked"]) == original_len:
            return {"error": f"Article {article_id} not found"}
        await self._repo.update(uuid.UUID(case_file_id), applicable_laws=laws)
        return {"deleted_id": article_id}

    async def _handle_set_strategy(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        strategies = cf.defense_strategies or []
        new_strategy = {
            "name": args["primary"],
            "backup": args.get("backup"),
            "confidence": args.get("confidence", 50),
            "ai_generated": True,
        }
        strategies.insert(0, new_strategy)
        await self._repo.update(uuid.UUID(case_file_id), defense_strategies=strategies)
        return {"strategy": args["primary"], "confidence": args.get("confidence", 50)}

    async def _handle_add_action_item(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        checklist = cf.action_checklist or []
        item_id = f"ai_action_{uuid.uuid4().hex[:8]}"
        new_item = {
            "id": item_id,
            "action": args["task"],
            "priority": args.get("priority", "medium"),
            "deadline": args.get("deadline"),
            "done": False,
        }
        checklist.append(new_item)
        await self._repo.update(uuid.UUID(case_file_id), action_checklist=checklist)
        return {"item_id": item_id, "task": args["task"]}

    async def _handle_complete_action_item(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        checklist = cf.action_checklist or []
        item_id = args["item_id"]
        for item in checklist:
            if item.get("id") == item_id:
                item["done"] = True
                await self._repo.update(uuid.UUID(case_file_id), action_checklist=checklist)
                return {"item_id": item_id, "completed": True}
        return {"error": f"Action item {item_id} not found"}

    async def _handle_delete_action_item(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        checklist = cf.action_checklist or []
        item_id = args["item_id"]
        original_len = len(checklist)
        new_checklist = [i for i in checklist if i.get("id") != item_id]
        if len(new_checklist) == original_len:
            return {"error": f"Action item {item_id} not found"}
        await self._repo.update(uuid.UUID(case_file_id), action_checklist=new_checklist)
        return {"deleted_id": item_id}

    async def _handle_add_risk(self, case_file_id: str, args: dict) -> dict:
        cf = await self._repo.get_by_id(uuid.UUID(case_file_id))
        if not cf:
            return {"error": "Case file not found"}
        unclear = cf.unclear_items or []
        risk_id = f"ai_risk_{uuid.uuid4().hex[:8]}"
        unclear.append({
            "id": risk_id,
            "description": args["description"],
            "severity": args.get("severity", "medium"),
            "mitigation": args.get("mitigation"),
        })
        await self._repo.update(uuid.UUID(case_file_id), unclear_items=unclear)
        return {
            "risk_id": risk_id,
            "description": args["description"],
            "severity": args.get("severity", "medium"),
        }

    async def _handle_create_case(self, _case_file_id: str, args: dict) -> dict:
        """Create a new case file. _case_file_id is ignored (we create a new one)."""
        if not self._user_id or not self._conversation_id:
            return {"error": "Cannot create case: missing user_id or conversation_id"}
        title = args.get("title", "ახალი საქმე")
        initial_facts = args.get("initial_facts", [])
        facts = {"items": []}
        for f in initial_facts:
            if isinstance(f, dict) and "text" in f:
                facts["items"].append({
                    "id": f"ai_fact_{uuid.uuid4().hex[:8]}",
                    "text": f["text"],
                    "classification": f.get("classification", "neutral"),
                })
        cf = await self._repo.create(
            user_id=self._user_id,
            conversation_id=uuid.UUID(self._conversation_id),
            title=title,
            facts=facts,
            status="draft",
        )
        logger.info("case_created_by_agent", case_file_id=str(cf.id), title=title)
        return {"case_file_id": str(cf.id), "title": cf.title, "status": "draft"}

    async def _handle_build_case_analysis(self, case_file_id: str, _args: dict) -> dict:
        """Trigger full case analysis via CaseBuilderService."""
        if not self._conversation_id:
            return {"error": "Cannot build case: missing conversation_id"}
        from app.services.case_builder_service import get_case_builder_service
        builder = get_case_builder_service()
        try:
            result = await builder.update_case_file(
                db=self._db,
                case_file_id=uuid.UUID(case_file_id),
                conversation_id=self._conversation_id,
            )
            logger.info("case_analysis_built_by_agent", case_file_id=case_file_id)
            return {
                "status": "analysis_complete",
                "case_file_id": case_file_id,
                "title": result.get("title", ""),
            }
        except Exception as e:
            logger.error("case_analysis_build_failed", error=str(e))
            return {"error": f"Case analysis failed: {str(e)}"}

    # ── Confirmation tracking ────────────────────────────────

    async def _defer_for_confirmation(
        self,
        tool_name: str,
        args: dict[str, Any],
        case_file_id: str,
        user_id: str,
    ) -> ToolResult:
        confirmation_id = f"conf_{uuid.uuid4().hex[:12]}"
        pending_data = {
            "tool_name": tool_name,
            "args": args,
            "case_file_id": case_file_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await self._store_pending(confirmation_id, pending_data)

        description = self._build_confirmation_description(tool_name, args)

        self._log_execution(user_id, tool_name, args, "pending_confirmation")

        return ToolResult(
            tool_name=tool_name,
            status="pending_confirmation",
            confirmation_id=confirmation_id,
            description=description,
            requires_confirmation=True,
        )

    def _build_confirmation_description(self, tool_name: str, args: dict) -> str:
        descriptions = {
            "delete_fact": lambda a: f"წაშალოთ ფაქტი: '{a.get('fact_id', '')}'?",
            "delete_argument": lambda a: f"წაშალოთ არგუმენტი: '{a.get('argument_id', '')}'?",
            "unlink_article": lambda a: f"მოხსნათ მუხლი: '{a.get('article_id', '')}'?",
            "delete_action_item": lambda a: f"წაშალოთ დავალება: '{a.get('item_id', '')}'?",
        }
        builder = descriptions.get(tool_name)
        return builder(args) if builder else f"Execute {tool_name}?"

    async def _store_pending(self, confirmation_id: str, data: dict) -> None:
        if self._redis:
            key = f"tool_confirm:{confirmation_id}"
            await self._redis.set(key, json.dumps(data), ex=CONFIRMATION_TTL_SECONDS)
        else:
            if not hasattr(self, "_pending_store"):
                self._pending_store: dict[str, dict] = {}
            self._pending_store[confirmation_id] = data

    async def _load_pending(self, confirmation_id: str) -> dict | None:
        if self._redis:
            key = f"tool_confirm:{confirmation_id}"
            raw = await self._redis.get(key)
            return json.loads(raw) if raw else None
        store = getattr(self, "_pending_store", {})
        return store.get(confirmation_id)

    async def _clear_pending(self, confirmation_id: str) -> None:
        if self._redis:
            await self._redis.delete(f"tool_confirm:{confirmation_id}")
        else:
            store = getattr(self, "_pending_store", {})
            store.pop(confirmation_id, None)

    def _log_execution(self, user_id: str, tool_name: str, args: dict, status: str) -> None:
        logger.info(
            "case_tool_execution",
            user_id=user_id,
            tool_name=tool_name,
            status=status,
            args_keys=list(args.keys()),
        )
