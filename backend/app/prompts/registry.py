"""
Global prompt registry — auto-registers all prompt templates at import time.

Usage:
    from app.prompts.registry import prompts
    prompt = prompts.get("legal_analysis_system")
    rendered = prompt.render(user_message="...")
"""

from app.prompts import PromptRegistry

from app.prompts.legal_analysis import LEGAL_ANALYSIS_SYSTEM
from app.prompts.rag_pipeline import QUERY_EXPANSION, RERANK
from app.prompts.case_builder import CASE_BUILDER
from app.prompts.classifier import LEGAL_CLASSIFIER
from app.prompts.explanation import SIMPLIFY_TEXT, EXPLAIN_ARTICLE
from app.prompts.questionnaire import QUESTIONNAIRE_GENERATOR, NARRATIVE_EXTRACTOR
from app.prompts.guardrail import GUARDRAIL_CLASSIFIER
from app.prompts.chat import CHAT_SYSTEM, CASE_INTAKE_SYSTEM, CASE_AGENT_SYSTEM
from app.prompts.document_generator import DOCUMENT_DRAFTER
from app.prompts.agent_planning import AGENT_PLANNER, CITATION_VERIFIER

prompts = PromptRegistry()

prompts.register(LEGAL_ANALYSIS_SYSTEM)
prompts.register(QUERY_EXPANSION)
prompts.register(RERANK)
prompts.register(CASE_BUILDER)
prompts.register(LEGAL_CLASSIFIER)
prompts.register(SIMPLIFY_TEXT)
prompts.register(EXPLAIN_ARTICLE)
prompts.register(QUESTIONNAIRE_GENERATOR)
prompts.register(NARRATIVE_EXTRACTOR)
prompts.register(GUARDRAIL_CLASSIFIER)
prompts.register(CHAT_SYSTEM)
prompts.register(CASE_INTAKE_SYSTEM)
prompts.register(CASE_AGENT_SYSTEM)
prompts.register(DOCUMENT_DRAFTER)
prompts.register(AGENT_PLANNER)
prompts.register(CITATION_VERIFIER)

_issues = prompts.validate_all()
if _issues:
    import warnings
    for name, problems in _issues.items():
        for problem in problems:
            warnings.warn(f"Prompt validation: {problem}", stacklevel=2)
