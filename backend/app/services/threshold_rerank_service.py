"""
Threshold-aware reranking for the RAG pipeline.

When a user query involves quantities, amounts, deadlines, or time periods,
threshold chunks get a score boost so the AI retrieves exact legal values.
"""

from __future__ import annotations

import re
from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Heuristic patterns ───────────────────────────────────────

# Georgian + generic terms that suggest the user wants a threshold value
_THRESHOLD_QUERY_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b\d+\s*(გრამი?|კილოგრამ|კგ|გ|ლარი|თეთრი|პრომილი|წელი|თვე|კვირა|დღე)\b", re.IGNORECASE),
    re.compile(r"\b(რამდენი|ოდენობა|ზღვარი|ლიმიტი|ვადა|თარიღი|წლამდე|წლის|თვის|დღის)\b", re.IGNORECASE),
    re.compile(r"\b(ჯარიმა|სასჯელი|თავისუფლების აღკვეთა|გირავნობა|დათქმული)\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:,\d{3})*\s*(ლარი|თეთრი)", re.IGNORECASE),
    re.compile(r"\b(კგ|kg|g|gr|mg|ml|l)\b", re.IGNORECASE),
    re.compile(r"\b\d+[\.,]?\d*\s*(პროცენტ|%|პრომილი)", re.IGNORECASE),
]

# Threshold chunk types in metadata
_THRESHOLD_CHUNK_TYPE = "threshold"
_THRESHOLD_TYPE_METADATA_KEY = "chunk_type"

# Boost factor per spec
_THRESHOLD_BOOST = 1.5


class ThresholdRerankService:
    """Boosts threshold chunks when queries contain quantity/deadline signals."""

    @staticmethod
    def is_threshold_query(query: str) -> bool:
        """Heuristic: does the query look like it's asking for a threshold value?"""
        if not query:
            return False
        lower = query.lower()
        return any(p.search(lower) for p in _THRESHOLD_QUERY_PATTERNS)

    @staticmethod
    def apply_threshold_boost(
        candidates: list[dict[str, Any]],
        query: str,
        boost: float = _THRESHOLD_BOOST,
    ) -> list[dict[str, Any]]:
        """Boost threshold chunks' effective distance scores when appropriate.

        Since ChromaDB returns cosine distance (lower = better), we scale
        the distance inversely: multiplying distance by (1/boost) makes
        threshold chunks appear closer / more relevant.
        """
        if not candidates or not ThresholdRerankService.is_threshold_query(query):
            return candidates

        boosted: list[dict[str, Any]] = []
        for c in candidates:
            meta = c.get("metadata", {})
            is_threshold = meta.get(_THRESHOLD_TYPE_METADATA_KEY) == _THRESHOLD_CHUNK_TYPE
            if is_threshold:
                new_c = dict(c)
                original_distance = c.get("distance", 1.0)
                # Scale distance down → higher relevance
                new_distance = original_distance / boost
                new_c["distance"] = new_distance
                new_c["threshold_boost_applied"] = True
                new_c["original_distance"] = original_distance
                boosted.append(new_c)
            else:
                boosted.append(c)

        # Re-sort by distance (best first)
        boosted.sort(key=lambda x: x.get("distance", 1.0))
        logger.info(
            "threshold_boost_applied",
            query=query[:80],
            total_candidates=len(candidates),
            threshold_chunks=sum(
                1 for c in boosted if c.get("threshold_boost_applied")
            ),
        )
        return boosted

    @staticmethod
    def get_threshold_chunks(
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return only the threshold chunks from a candidate list."""
        return [
            c for c in candidates
            if c.get("metadata", {}).get(_THRESHOLD_TYPE_METADATA_KEY)
            == _THRESHOLD_CHUNK_TYPE
        ]


# ── Singleton ────────────────────────────────────────────────

_threshold_service: ThresholdRerankService | None = None


def get_threshold_rerank_service() -> ThresholdRerankService:
    """Return the singleton ThresholdRerankService."""
    global _threshold_service
    if _threshold_service is None:
        _threshold_service = ThresholdRerankService()
    return _threshold_service
