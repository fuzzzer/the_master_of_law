"""
Threshold chunk model — represents a structured legal threshold
stored in ChromaDB (not PostgreSQL).

These entries capture exact quantitative legal boundaries:
drug quantities, sentence ranges, fine amounts, filing deadlines,
statute of limitations, and monetary thresholds.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class ThresholdChunk(BaseModel):
    """A single legal threshold entry embedded in the vector store."""

    id: str = Field(..., description="Unique threshold identifier")
    type: str = Field(default="legal_threshold", description="Document type discriminator")
    code_name: str = Field(..., description="Full name of the legal code")
    article_number: str = Field(..., description="Article number within the code")
    threshold_type: str = Field(
        ...,
        description="Category: drug_quantity, sentence_range, fine_range, filing_deadline, statute_of_limitations, monetary_limit, age_limit, quantity",
    )
    description_ka: str = Field(
        ..., description="Human-readable description of the threshold in Georgian"
    )
    substance: str | None = Field(
        default=None, description="Substance name for drug/quantity thresholds"
    )
    values: dict[str, str] = Field(
        default_factory=dict,
        description="Structured threshold values (e.g., {'small': '≤70g', 'large': '>70g'})",
    )
    consequence_ka: str = Field(
        ..., description="Legal consequences when the threshold is crossed, in Georgian"
    )
    source_url: str = Field(..., description="Official source URL (e.g., matsne.gov.ge)")
    last_verified: date = Field(..., description="Date the threshold was last verified")

    def to_chroma_document(self) -> str:
        """Build the human-readable text used for embedding generation."""
        parts = [
            f"სამართლებრივი ზღვარი: {self.description_ka}",
            f"კოდექსი: {self.code_name}",
            f"მუხლი: {self.article_number}",
            f"ზღვრის ტიპი: {self.threshold_type}",
        ]
        if self.substance:
            parts.append(f"საგანი: {self.substance}")
        if self.values:
            parts.append("მნიშვნელობები:")
            for key, val in self.values.items():
                parts.append(f"  • {key}: {val}")
        if self.consequence_ka:
            parts.append(f"შედეგი: {self.consequence_ka}")
        return "\n".join(parts)

    def to_chroma_metadata(self) -> dict[str, Any]:
        """Build flat metadata dict for ChromaDB (no nested dicts allowed)."""
        meta: dict[str, Any] = {
            "chunk_type": "threshold",
            "code_name": self.code_name,
            "article_number": self.article_number,
            "threshold_type": self.threshold_type,
            "description_ka": self.description_ka,
            "source_url": self.source_url,
            "last_verified": str(self.last_verified),
            "threshold_id": self.id,
        }
        if self.substance:
            meta["substance"] = self.substance
        for key, val in self.values.items():
            meta[f"value_{key}"] = str(val)
        return meta

    @classmethod
    def from_catalog_entry(cls, entry: dict[str, Any]) -> "ThresholdChunk":
        """Parse a raw JSON catalog entry into a ThresholdChunk."""
        return cls(
            id=entry.get("id", ""),
            type=entry.get("type", "legal_threshold"),
            code_name=entry.get("code_name", ""),
            article_number=entry.get("article_number", ""),
            threshold_type=entry.get("threshold_type", ""),
            description_ka=entry.get("description_ka", ""),
            substance=entry.get("substance"),
            values=entry.get("values", {}),
            consequence_ka=entry.get("consequence_ka", ""),
            source_url=entry.get("source_url", ""),
            last_verified=date.fromisoformat(entry.get("last_verified", "2026-01-01")),
        )
