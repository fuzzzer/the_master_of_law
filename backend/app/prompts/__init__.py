"""
Prompt registry — structured, typed prompt management.

All Gemini prompts live here. No hardcoded prompt strings in service files.
Each prompt is a dataclass with typed fields, template variables, and rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PromptRole(str, Enum):
    """The role a prompt plays in a Gemini call."""
    SYSTEM = "system"          # system_instruction parameter
    USER = "user"              # main prompt / contents
    CONTEXT = "context"        # injected context (law chunks, history)


@dataclass(frozen=True)
class PromptTemplate:
    """
    A single prompt template with typed metadata.

    Attributes:
        name: Unique identifier (e.g., "legal_analysis_system").
        role: Whether this is a system instruction or user prompt.
        template: The raw template string with {placeholders}.
        description: Human-readable description of what this prompt does.
        variables: Expected placeholder names for validation.
        temperature: Suggested temperature for this prompt.
        max_output_tokens: Suggested max output tokens.
        response_format: Expected response format ("text" or "json").
    """
    name: str
    role: PromptRole
    template: str
    description: str = ""
    variables: tuple[str, ...] = ()
    temperature: float = 0.1
    max_output_tokens: int = 8192
    response_format: str = "text"

    def render(self, **kwargs: Any) -> str:
        """
        Render the template with the given variables.

        Raises KeyError if a required variable is missing.
        """
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise KeyError(f"Prompt '{self.name}' missing variables: {missing}")
        return self.template.format(**kwargs)

    def validate(self) -> list[str]:
        """Check template integrity. Returns list of issues (empty = valid)."""
        issues: list[str] = []
        if not self.name:
            issues.append("Prompt has no name")
        if not self.template.strip():
            issues.append(f"Prompt '{self.name}' has empty template")
        # Verify declared variables exist in template
        for var in self.variables:
            placeholder = "{" + var + "}"
            if placeholder not in self.template:
                issues.append(f"Prompt '{self.name}': declared variable '{var}' not found in template")
        return issues


class PromptRegistry:
    """
    Central registry of all prompts.

    Usage:
        registry = PromptRegistry()
        registry.register(my_prompt)
        prompt = registry.get("my_prompt_name")
        rendered = prompt.render(var1="value1")
    """

    def __init__(self) -> None:
        self._prompts: dict[str, PromptTemplate] = {}

    def register(self, prompt: PromptTemplate) -> None:
        """Register a prompt template."""
        self._prompts[prompt.name] = prompt

    def get(self, name: str) -> PromptTemplate:
        """Get a prompt by name. Raises KeyError if not found."""
        if name not in self._prompts:
            raise KeyError(f"Prompt '{name}' not registered. Available: {list(self._prompts.keys())}")
        return self._prompts[name]

    def list_all(self) -> list[str]:
        """List all registered prompt names."""
        return sorted(self._prompts.keys())

    def validate_all(self) -> dict[str, list[str]]:
        """Validate all prompts. Returns {name: [issues]} for any with issues."""
        results: dict[str, list[str]] = {}
        for name, prompt in self._prompts.items():
            issues = prompt.validate()
            if issues:
                results[name] = issues
        return results

    def __len__(self) -> int:
        return len(self._prompts)

    def __contains__(self, name: str) -> bool:
        return name in self._prompts
