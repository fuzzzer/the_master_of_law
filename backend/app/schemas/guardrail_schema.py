"""
Guardrail-related Pydantic schemas.

Used by the GuardrailService to classify incoming messages before
they reach the RAG pipeline.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class GuardrailCategory(str, Enum):
    """Classification categories for incoming user messages."""

    LEGAL = "legal"
    GREETING = "greeting"
    OFF_TOPIC = "off_topic"
    HARMFUL = "harmful"


class GuardrailDecision(BaseModel):
    """Result of guardrail classification."""

    category: GuardrailCategory = Field(..., description="Assigned category")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence in the classification"
    )
    is_legal: bool = Field(
        ..., description="Convenience flag — True when category == LEGAL"
    )

    @classmethod
    def legal(cls, confidence: float = 1.0) -> "GuardrailDecision":
        return cls(category=GuardrailCategory.LEGAL, confidence=confidence, is_legal=True)

    @classmethod
    def greeting(cls, confidence: float = 1.0) -> "GuardrailDecision":
        return cls(category=GuardrailCategory.GREETING, confidence=confidence, is_legal=False)

    @classmethod
    def off_topic(cls, confidence: float = 1.0) -> "GuardrailDecision":
        return cls(category=GuardrailCategory.OFF_TOPIC, confidence=confidence, is_legal=False)

    @classmethod
    def harmful(cls, confidence: float = 1.0) -> "GuardrailDecision":
        return cls(category=GuardrailCategory.HARMFUL, confidence=confidence, is_legal=False)


class GuardrailLogEntry(BaseModel):
    """Audit log entry for a guardrail decision."""

    user_id: str = Field(..., description="Firebase UID or anonymous identifier")
    message_hash: str = Field(..., description="SHA-256 hash of the original message")
    category: GuardrailCategory
    confidence: float
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    bypassed: bool = Field(default=False, description="True if ADMIN bypass was applied")
