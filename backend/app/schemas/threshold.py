"""
Threshold API schemas.

Used to return structured threshold data from RAG endpoints
and to validate threshold ingestion payloads.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class ThresholdValue(BaseModel):
    """A single named threshold value."""

    name: str = Field(..., description="Key name, e.g. 'small', 'large', 'maximum'")
    value: str = Field(..., description="The threshold value, e.g. '≤ 70 გრამი'")


class ThresholdResponse(BaseModel):
    """API response model for a retrieved legal threshold."""

    threshold_id: str = Field(..., description="Unique identifier")
    code_name: str = Field(..., description="Legal code name in Georgian")
    article_number: str = Field(..., description="Article number")
    threshold_type: str = Field(..., description="Category of threshold")
    description_ka: str = Field(..., description="Description in Georgian")
    substance: str | None = Field(default=None, description="Substance name if applicable")
    values: list[ThresholdValue] = Field(default_factory=list, description="Structured values")
    consequence_ka: str = Field(..., description="Legal consequences in Georgian")
    source_url: str = Field(..., description="Official source URL")
    last_verified: date = Field(..., description="Verification date")
    distance: float | None = Field(
        default=None, description="Cosine distance from query (lower = more relevant)"
    )
    threshold_boost_applied: bool = Field(
        default=False, description="True if the 1.5x rerank boost was applied"
    )

    @classmethod
    def from_chroma_hit(cls, hit: dict[str, Any]) -> "ThresholdResponse":
        """Build a ThresholdResponse from a ChromaDB hit dictionary."""
        meta = hit.get("metadata", {})

        # Reconstruct values dict from flattened metadata
        values: list[ThresholdValue] = []
        for key, val in meta.items():
            if key.startswith("value_"):
                values.append(ThresholdValue(name=key[6:], value=str(val)))

        return cls(
            threshold_id=meta.get("threshold_id", hit.get("chunk_id", "")),
            code_name=meta.get("code_name", ""),
            article_number=meta.get("article_number", ""),
            threshold_type=meta.get("threshold_type", ""),
            description_ka=meta.get("description_ka", ""),
            substance=meta.get("substance"),
            values=values,
            consequence_ka=meta.get("consequence_ka", ""),
            source_url=meta.get("source_url", ""),
            last_verified=date.fromisoformat(
                meta.get("last_verified", "2026-01-01")
            ),
            distance=hit.get("distance"),
            threshold_boost_applied=hit.get("threshold_boost_applied", False),
        )


class ThresholdQueryResult(BaseModel):
    """Wrapper for a batch of threshold results returned to the client."""

    query: str = Field(..., description="Original user query")
    is_threshold_query: bool = Field(
        ..., description="Whether the heuristic detected a quantity/deadline signal"
    )
    thresholds: list[ThresholdResponse] = Field(
        default_factory=list, description="Retrieved threshold entries"
    )
    total_found: int = Field(..., description="Total thresholds in the result set")
