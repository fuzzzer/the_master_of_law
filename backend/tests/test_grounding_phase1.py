"""
Tests for Phase 1 grounding mechanisms:
- B: get_article / browse_code navigation tools (declarations + executors)
- C: whole-code context injection (flag-gated)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.config.settings import settings
from app.services.agent_pipeline_service import AgentPipelineService
from app.tools.case_tools import ALWAYS_TOOLS, CASE_CREATION_TOOLS, FULL_CASE_TOOLS

STORE_PATH = Path(__file__).parent.parent.parent / "law_corpus" / "data" / "georgian_laws" / "article_store.db"
needs_store = pytest.mark.skipif(not STORE_PATH.exists(), reason="article_store.db not built")


def _tool_names(tools) -> set[str]:
    return {
        fd.name
        for tool in tools
        for fd in (tool.function_declarations or [])
    }


class TestNavigationToolDeclarations:
    def test_always_tools_include_navigation(self):
        names = _tool_names(ALWAYS_TOOLS)
        assert {"search_law", "get_article", "browse_code"} <= names

    def test_case_tool_groups_include_navigation(self):
        assert {"get_article", "browse_code"} <= _tool_names(CASE_CREATION_TOOLS)
        assert {"get_article", "browse_code"} <= _tool_names(FULL_CASE_TOOLS)


@needs_store
class TestGetArticleExecutor:
    @pytest.mark.asyncio
    async def test_found_returns_full_text_and_url(self):
        svc = AgentPipelineService()
        out = await svc._handle_get_article({"code": "შრომის კოდექსი", "article": "48"})
        assert out["found"] is True
        assert "30 კალენდარული დღის" in out["content"]
        assert out["url"].endswith("#article_48")
        assert "labour_code.article_47" in out["cross_references"]

    @pytest.mark.asyncio
    async def test_paragraph_selection(self):
        svc = AgentPipelineService()
        out = await svc._handle_get_article(
            {"code": "labour_code", "article": "48", "paragraph": "8"}
        )
        assert out["paragraph"]["number"] == "8"

    @pytest.mark.asyncio
    async def test_not_found_warns_against_citing(self):
        svc = AgentPipelineService()
        with patch.object(
            svc.citation_svc, "_search_corpus_exact", return_value=None
        ):
            out = await svc._handle_get_article(
                {"code": "შრომის კოდექსი", "article": "99999"}
            )
        assert out["found"] is False
        assert "Do NOT cite" in out["message"]


@needs_store
class TestBrowseCodeExecutor:
    @pytest.mark.asyncio
    async def test_lists_articles(self):
        svc = AgentPipelineService()
        out = await svc._handle_browse_code({"code": "შრომის კოდექსი"})
        assert out["found"] is True
        assert out["article_count"] > 50
        assert any("მუხლი 47" == a["article"] for a in out["articles"])

    @pytest.mark.asyncio
    async def test_unknown_code_lists_available(self):
        svc = AgentPipelineService()
        out = await svc._handle_browse_code({"code": "არარსებული კოდექსი XYZ"})
        assert out["found"] is False
        assert len(out["available_codes"]) > 0


@needs_store
class TestFullCodeInjection:
    @pytest.mark.asyncio
    async def test_labor_domain_injects_labour_code(self, monkeypatch):
        monkeypatch.setattr(settings, "full_code_injection", True)
        svc = AgentPipelineService()
        text = await svc._build_full_code_context(
            "დამსაქმებელმა სამსახურიდან გამათავისუფლა ორსულობის გამო"
        )
        assert "მუხლი 47" in text
        assert "მუხლი 48" in text
        assert "#article_48" in text

    @pytest.mark.asyncio
    async def test_unmapped_domain_injects_nothing(self, monkeypatch):
        monkeypatch.setattr(settings, "full_code_injection", True)
        svc = AgentPipelineService()
        text = await svc._build_full_code_context(
            "მეზობელმა მიწის ნაკვეთის საზღვარი გადმოწია"
        )
        assert text == ""

    @pytest.mark.asyncio
    async def test_budget_too_small_skips(self, monkeypatch):
        monkeypatch.setattr(settings, "full_code_injection", True)
        monkeypatch.setattr(settings, "full_code_injection_max_chars", 1000)
        svc = AgentPipelineService()
        text = await svc._build_full_code_context(
            "დამსაქმებელმა სამსახურიდან გამათავისუფლა ორსულობის გამო"
        )
        assert text == ""
