"""
Corpus Module Registry.

Each knowledge source is a self-contained module with:
- Its own ChromaDB collection
- Its own data directory
- Its own RAG instructions (how the LLM should use retrieved context)
- A feature flag to enable/disable it

Usage:
    from modules import registry

    # Get all enabled modules
    for module in registry.enabled():
        print(module.id, module.collection_name)

    # Get RAG instructions for sources present in retrieved chunks
    instructions = registry.get_rag_instructions({"court_practice", "grand_chamber"})
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class CorpusModule(abc.ABC):
    """Base class for a corpus knowledge source."""

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """Unique module identifier, matches ChromaDB collection name."""
        ...

    @property
    @abc.abstractmethod
    def name_ka(self) -> str:
        """Georgian display name."""
        ...

    @property
    @abc.abstractmethod
    def name_en(self) -> str:
        """English display name."""
        ...

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Short description of this knowledge source."""
        ...

    @property
    @abc.abstractmethod
    def rag_instructions(self) -> str:
        """
        Instructions injected into the system prompt when chunks from
        this module appear in the retrieved RAG context.
        """
        ...

    @property
    def collection_name(self) -> str:
        """ChromaDB collection name. Defaults to module id."""
        return self.id

    @property
    def enabled_by_default(self) -> bool:
        """Whether this module is on by default."""
        return False


class ModuleRegistry:
    """Registry of all corpus modules with feature-flag support."""

    def __init__(self) -> None:
        self._modules: dict[str, CorpusModule] = {}
        self._overrides: dict[str, bool] = {}

    def register(self, module: CorpusModule) -> None:
        """Register a corpus module."""
        self._modules[module.id] = module

    def set_enabled(self, module_id: str, enabled: bool) -> None:
        """Override the default enabled state for a module."""
        self._overrides[module_id] = enabled

    def is_enabled(self, module_id: str) -> bool:
        """Check if a module is currently enabled."""
        if module_id in self._overrides:
            return self._overrides[module_id]
        module = self._modules.get(module_id)
        return module.enabled_by_default if module else False

    def get(self, module_id: str) -> CorpusModule | None:
        """Get a module by ID."""
        return self._modules.get(module_id)

    def all(self) -> list[CorpusModule]:
        """Return all registered modules."""
        return list(self._modules.values())

    def enabled(self) -> list[CorpusModule]:
        """Return only enabled modules."""
        return [m for m in self._modules.values() if self.is_enabled(m.id)]

    def enabled_collection_names(self) -> list[str]:
        """Return ChromaDB collection names for enabled modules."""
        return [m.collection_name for m in self.enabled()]

    def get_rag_instructions(self, source_ids: set[str]) -> str:
        """
        Build combined RAG instructions for the given source IDs.

        Called after RAG retrieval — only includes instructions for
        sources that actually appear in the retrieved context.
        """
        parts: list[str] = []
        for sid in sorted(source_ids):
            module = self._modules.get(sid)
            if module and module.rag_instructions.strip():
                parts.append(
                    f"[{module.name_ka} / {module.name_en}]\n"
                    f"{module.rag_instructions.strip()}"
                )
        if not parts:
            return ""
        return (
            "\n\nSOURCE-SPECIFIC INSTRUCTIONS FOR RETRIEVED CONTEXT:\n"
            + "\n\n".join(parts)
        )


# ── Singleton registry ──────────────────────────────────────

registry = ModuleRegistry()


def _auto_register() -> None:
    """Auto-register all built-in modules."""
    from modules.georgian_laws import GeorgianLawsModule
    from modules.court_practice import CourtPracticeModule
    from modules.grand_chamber import GrandChamberModule

    registry.register(GeorgianLawsModule())
    registry.register(CourtPracticeModule())
    registry.register(GrandChamberModule())


_auto_register()
