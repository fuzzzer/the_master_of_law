"""
RAG collection configuration schemas.

Controls which knowledge sources (ChromaDB collections) the RAG pipeline
searches across. Allows per-request toggling of legal codes, court practice,
and Grand Chamber decisions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RAGCollectionConfig(BaseModel):
    """Controls which RAG collections to search per request."""

    legal_codes: bool = Field(
        default=True,
        description='Enable search in "georgian_laws" collection (15 legal codes)',
    )
    court_practice: bool = Field(
        default=True,
        description='Enable search in "court_practice" collection (Supreme Court rulings)',
    )
    grand_chamber: bool = Field(
        default=True,
        description='Enable search in "grand_chamber" collection (binding decisions)',
    )

    def to_collection_names(self) -> list[str]:
        """Convert boolean flags to a list of ChromaDB collection names."""
        names = []
        if self.legal_codes:
            names.append("georgian_laws")
        if self.court_practice:
            names.append("court_practice")
        if self.grand_chamber:
            names.append("grand_chamber")
        return names or ["georgian_laws"]  # Always search at least legal codes


class CollectionInfo(BaseModel):
    """Information about a single RAG collection."""
    id: str
    name_ka: str = ""
    description: str = ""
    available: bool = False
    chunk_count: int = 0


class CollectionListResponse(BaseModel):
    """Response for GET /api/v1/rag/collections."""
    collections: list[CollectionInfo]
