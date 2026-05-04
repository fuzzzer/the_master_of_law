"""
Tests for the prompt registry and template system.

Verifies:
- All 7 prompts are registered
- Template rendering with variables
- Validation detects issues
- Missing variable errors
- Registry lookup
"""

import sys
sys.path.insert(0, ".")

import pytest

from app.prompts import PromptRole, PromptTemplate, PromptRegistry
from app.prompts.registry import prompts


class TestPromptTemplate:
    def test_render_simple(self):
        pt = PromptTemplate(
            name="test", role=PromptRole.USER,
            template="Hello {name}", variables=("name",),
        )
        assert pt.render(name="World") == "Hello World"

    def test_render_missing_variable(self):
        pt = PromptTemplate(
            name="test", role=PromptRole.USER,
            template="Hello {name}", variables=("name",),
        )
        with pytest.raises(KeyError, match="missing variables"):
            pt.render()

    def test_validate_empty_template(self):
        pt = PromptTemplate(name="bad", role=PromptRole.USER, template="")
        issues = pt.validate()
        assert len(issues) > 0

    def test_validate_missing_variable_in_template(self):
        pt = PromptTemplate(
            name="bad", role=PromptRole.USER,
            template="no placeholder", variables=("missing",),
        )
        issues = pt.validate()
        assert any("missing" in i for i in issues)

    def test_validate_ok(self):
        pt = PromptTemplate(
            name="ok", role=PromptRole.USER,
            template="Hello {name}", variables=("name",),
        )
        assert pt.validate() == []

    def test_frozen(self):
        pt = PromptTemplate(name="x", role=PromptRole.USER, template="y")
        with pytest.raises(AttributeError):
            pt.name = "z"


class TestPromptRegistry:
    def test_register_and_get(self):
        reg = PromptRegistry()
        pt = PromptTemplate(name="t1", role=PromptRole.USER, template="x")
        reg.register(pt)
        assert reg.get("t1") is pt

    def test_get_missing(self):
        reg = PromptRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.get("nonexistent")

    def test_list_all(self):
        reg = PromptRegistry()
        reg.register(PromptTemplate(name="b", role=PromptRole.USER, template=""))
        reg.register(PromptTemplate(name="a", role=PromptRole.USER, template=""))
        assert reg.list_all() == ["a", "b"]

    def test_len(self):
        reg = PromptRegistry()
        assert len(reg) == 0
        reg.register(PromptTemplate(name="x", role=PromptRole.USER, template="y"))
        assert len(reg) == 1

    def test_contains(self):
        reg = PromptRegistry()
        reg.register(PromptTemplate(name="x", role=PromptRole.USER, template="y"))
        assert "x" in reg
        assert "z" not in reg


class TestGlobalRegistry:
    def test_all_prompts_registered(self):
        expected = [
            "legal_analysis_system",
            "rag_query_expansion",
            "rag_rerank",
            "case_builder",
            "legal_classifier",
            "explain_simplify",
            "explain_article",
        ]
        for name in expected:
            assert name in prompts, f"Prompt '{name}' not in registry"

    def test_prompt_count(self):
        assert len(prompts) == 7

    def test_all_valid(self):
        issues = prompts.validate_all()
        assert issues == {}, f"Prompt validation issues: {issues}"

    def test_legal_analysis_is_system_role(self):
        p = prompts.get("legal_analysis_system")
        assert p.role == PromptRole.SYSTEM

    def test_query_expansion_renders(self):
        p = prompts.get("rag_query_expansion")
        rendered = p.render(count=8, user_message="test")
        assert "test" in rendered
        assert "8" in rendered

    def test_case_builder_renders(self):
        p = prompts.get("case_builder")
        rendered = p.render(conversation_text="conv", law_context="law")
        assert "conv" in rendered
        assert "law" in rendered

    def test_classifier_renders(self):
        p = prompts.get("legal_classifier")
        rendered = p.render(user_message="test situation")
        assert "test situation" in rendered

    def test_explain_simplify_renders(self):
        p = prompts.get("explain_simplify")
        rendered = p.render(legal_text="complex legal text")
        assert "complex legal text" in rendered

    def test_explain_article_renders(self):
        p = prompts.get("explain_article")
        rendered = p.render(
            code_name="Criminal Code",
            article_number="Article 11",
            article_text="text",
        )
        assert "Criminal Code" in rendered
        assert "Article 11" in rendered
