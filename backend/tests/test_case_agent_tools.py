"""
Tests for case agent tools — tool definitions, executor, and schemas.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.case_tool_executor import CaseToolExecutor, ToolResult, MAX_TOOL_CALLS_PER_MESSAGE
from app.tools.case_tools import CASE_TOOL_DECLARATIONS, CASE_TOOLS, DESTRUCTIVE_TOOLS


class TestCaseToolDefinitions:
    """Verify tool declaration schemas are well-formed."""

    def test_tool_count(self):
        assert len(CASE_TOOL_DECLARATIONS) == 13

    def test_all_declarations_have_names(self):
        for decl in CASE_TOOL_DECLARATIONS:
            assert decl.name, f"Declaration missing name: {decl}"
            assert decl.description, f"{decl.name} missing description"

    def test_destructive_tools_are_subset(self):
        tool_names = {d.name for d in CASE_TOOL_DECLARATIONS}
        for dt in DESTRUCTIVE_TOOLS:
            assert dt in tool_names, f"Destructive tool {dt} not in declarations"

    def test_destructive_tools_count(self):
        assert len(DESTRUCTIVE_TOOLS) == 4

    def test_case_tools_wrapper(self):
        assert len(CASE_TOOLS) == 1
        assert len(CASE_TOOLS[0].function_declarations) == 13

    def test_tool_names_are_unique(self):
        names = [d.name for d in CASE_TOOL_DECLARATIONS]
        assert len(names) == len(set(names))

    def test_read_tool_exists(self):
        names = {d.name for d in CASE_TOOL_DECLARATIONS}
        assert "get_case_summary" in names

    def test_create_tools_exist(self):
        names = {d.name for d in CASE_TOOL_DECLARATIONS}
        for expected in ["add_fact", "add_argument", "link_article", "add_action_item", "add_risk", "set_strategy"]:
            assert expected in names, f"Missing create tool: {expected}"

    def test_update_tools_exist(self):
        names = {d.name for d in CASE_TOOL_DECLARATIONS}
        for expected in ["edit_fact", "complete_action_item"]:
            assert expected in names, f"Missing update tool: {expected}"

    def test_delete_tools_exist(self):
        names = {d.name for d in CASE_TOOL_DECLARATIONS}
        for expected in ["delete_fact", "delete_argument", "unlink_article", "delete_action_item"]:
            assert expected in names


class TestToolResult:
    """Test ToolResult serialization."""

    def test_to_dict_basic(self):
        tr = ToolResult(tool_name="add_fact", status="executed", result={"fact_id": "f1"})
        d = tr.to_dict()
        assert d["tool_name"] == "add_fact"
        assert d["status"] == "executed"
        assert d["result"]["fact_id"] == "f1"
        assert d["requires_confirmation"] is False
        assert "confirmation_id" not in d

    def test_to_dict_with_confirmation(self):
        tr = ToolResult(
            tool_name="delete_fact",
            status="pending_confirmation",
            confirmation_id="conf_abc123",
            description="Delete fact?",
            requires_confirmation=True,
        )
        d = tr.to_dict()
        assert d["requires_confirmation"] is True
        assert d["confirmation_id"] == "conf_abc123"
        assert d["description"] == "Delete fact?"


class TestCaseToolExecutor:
    """Test executor routing and handler behavior."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_case_file(self):
        cf = MagicMock()
        cf.title = "Test Case"
        cf.status = "active"
        cf.facts = {"items": [{"id": "f1", "text": "Fact 1", "classification": "neutral"}]}
        cf.evidence = {}
        cf.applicable_laws = {"favorable": [], "linked": []}
        cf.defense_strategies = []
        cf.prosecution_args = [{"id": "a1", "title": "Arg 1"}]
        cf.action_checklist = [{"id": "act1", "action": "Do thing", "done": False}]
        cf.unclear_items = []
        return cf

    @pytest.mark.asyncio
    async def test_get_case_summary_returns_case_data(self, mock_db, mock_case_file):
        executor = CaseToolExecutor(mock_db)
        executor._repo = AsyncMock()
        executor._repo.get_by_id = AsyncMock(return_value=mock_case_file)

        result = await executor.execute("get_case_summary", {}, str(uuid.uuid4()), "user1")
        assert result.status == "executed"
        assert result.result["title"] == "Test Case"

    @pytest.mark.asyncio
    async def test_add_fact_creates_new_fact(self, mock_db, mock_case_file):
        executor = CaseToolExecutor(mock_db)
        executor._repo = AsyncMock()
        executor._repo.get_by_id = AsyncMock(return_value=mock_case_file)
        executor._repo.update = AsyncMock()

        result = await executor.execute(
            "add_fact",
            {"text": "New fact", "classification": "favorable"},
            str(uuid.uuid4()),
            "user1",
        )
        assert result.status == "executed"
        assert result.result["text"] == "New fact"
        assert result.result["classification"] == "favorable"
        assert "fact_id" in result.result

    @pytest.mark.asyncio
    async def test_destructive_tool_defers_for_confirmation(self, mock_db):
        executor = CaseToolExecutor(mock_db)

        result = await executor.execute(
            "delete_fact",
            {"fact_id": "f1"},
            str(uuid.uuid4()),
            "user1",
        )
        assert result.status == "pending_confirmation"
        assert result.requires_confirmation is True
        assert result.confirmation_id is not None
        assert "წაშალოთ" in result.description

    @pytest.mark.asyncio
    async def test_confirm_pending_executes(self, mock_db, mock_case_file):
        executor = CaseToolExecutor(mock_db)
        executor._repo = AsyncMock()
        executor._repo.get_by_id = AsyncMock(return_value=mock_case_file)
        executor._repo.update = AsyncMock()

        defer_result = await executor.execute(
            "delete_fact",
            {"fact_id": "f1"},
            str(uuid.uuid4()),
            "user1",
        )
        assert defer_result.status == "pending_confirmation"

        confirm_result = await executor.confirm_pending(
            defer_result.confirmation_id,
            "user1",
            confirmed=True,
        )
        assert confirm_result.status == "executed"

    @pytest.mark.asyncio
    async def test_reject_pending(self, mock_db):
        executor = CaseToolExecutor(mock_db)

        defer_result = await executor.execute(
            "delete_fact",
            {"fact_id": "f1"},
            str(uuid.uuid4()),
            "user1",
        )

        reject_result = await executor.confirm_pending(
            defer_result.confirmation_id,
            "user1",
            confirmed=False,
        )
        assert reject_result.status == "rejected"

    @pytest.mark.asyncio
    async def test_confirm_wrong_user_fails(self, mock_db):
        executor = CaseToolExecutor(mock_db)

        defer_result = await executor.execute(
            "delete_fact",
            {"fact_id": "f1"},
            str(uuid.uuid4()),
            "user1",
        )

        mismatch_result = await executor.confirm_pending(
            defer_result.confirmation_id,
            "user2",
            confirmed=True,
        )
        assert mismatch_result.status == "error"
        assert "mismatch" in mismatch_result.result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_expired_confirmation(self, mock_db):
        executor = CaseToolExecutor(mock_db)
        result = await executor.confirm_pending("nonexistent_id", "user1", confirmed=True)
        assert result.status == "error"
        assert "expired" in result.result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, mock_db):
        executor = CaseToolExecutor(mock_db)
        result = await executor.execute("nonexistent_tool", {}, str(uuid.uuid4()), "user1")
        assert result.status == "error"
        assert "Unknown" in result.result.get("error", "")

    @pytest.mark.asyncio
    async def test_set_strategy(self, mock_db, mock_case_file):
        executor = CaseToolExecutor(mock_db)
        executor._repo = AsyncMock()
        executor._repo.get_by_id = AsyncMock(return_value=mock_case_file)
        executor._repo.update = AsyncMock()

        result = await executor.execute(
            "set_strategy",
            {"primary": "Self-defense claim", "confidence": 75},
            str(uuid.uuid4()),
            "user1",
        )
        assert result.status == "executed"
        assert result.result["strategy"] == "Self-defense claim"
        assert result.result["confidence"] == 75

    @pytest.mark.asyncio
    async def test_add_action_item(self, mock_db, mock_case_file):
        executor = CaseToolExecutor(mock_db)
        executor._repo = AsyncMock()
        executor._repo.get_by_id = AsyncMock(return_value=mock_case_file)
        executor._repo.update = AsyncMock()

        result = await executor.execute(
            "add_action_item",
            {"task": "File motion", "priority": "high"},
            str(uuid.uuid4()),
            "user1",
        )
        assert result.status == "executed"
        assert result.result["task"] == "File motion"

    @pytest.mark.asyncio
    async def test_complete_action_item(self, mock_db, mock_case_file):
        executor = CaseToolExecutor(mock_db)
        executor._repo = AsyncMock()
        executor._repo.get_by_id = AsyncMock(return_value=mock_case_file)
        executor._repo.update = AsyncMock()

        result = await executor.execute(
            "complete_action_item",
            {"item_id": "act1"},
            str(uuid.uuid4()),
            "user1",
        )
        assert result.status == "executed"
        assert result.result["completed"] is True


class TestSchemas:
    """Test that chat schemas support tool results."""

    def test_tool_result_info_schema(self):
        from app.schemas.chat_schema import ToolResultInfo
        tri = ToolResultInfo(
            tool_name="add_fact",
            status="executed",
            result={"fact_id": "f1"},
        )
        assert tri.tool_name == "add_fact"
        assert tri.requires_confirmation is False

    def test_tool_confirm_request_schema(self):
        from app.schemas.chat_schema import ToolConfirmRequest
        tcr = ToolConfirmRequest(confirmation_id="conf_123", confirmed=True)
        assert tcr.confirmed is True

    def test_chat_response_has_tool_results(self):
        from app.schemas.chat_schema import ChatSendResponse
        resp = ChatSendResponse(
            response="Done",
            tool_results=[],
        )
        assert resp.tool_results == []

    def test_chat_request_has_case_file_id(self):
        from app.schemas.chat_schema import ChatSendRequest
        req = ChatSendRequest(
            message="Add a fact",
            mode="case_agent",
            case_file_id="some-uuid",
        )
        assert req.case_file_id == "some-uuid"
        assert req.mode == "case_agent"


class TestPrompts:
    """Test case agent prompt."""

    def test_case_agent_system_renders(self):
        from app.prompts.chat import CASE_AGENT_SYSTEM
        rendered = CASE_AGENT_SYSTEM.render(case_context="Test case context")
        assert "CASE AGENT" in rendered
        assert "Test case context" in rendered
        assert "get_case_summary" in rendered

    def test_case_agent_registered(self):
        from app.prompts.registry import prompts
        agent_prompt = prompts.get("case_agent_system")
        assert agent_prompt is not None
