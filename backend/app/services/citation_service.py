"""
Citation Service — extracts and verifies law citations from AI responses.

After Gemini generates a response, this service:
1. Extracts all law citations from the response text
2. Validates each citation exists in the corpus
3. Returns verified citations with full metadata
"""

from __future__ import annotations

import re
from typing import Any

from app.integrations.chroma_client import ChromaClient, get_chroma_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Pattern to match Georgian law citations like "მუხლი 45" or "მუხლი 120"
ARTICLE_PATTERN = re.compile(r"მუხლი\s+(\d+)", re.UNICODE)

# Pattern to match code names
CODE_NAMES = [
    "სისხლის სამართლის კოდექსი",
    "სამოქალაქო კოდექსი",
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "სისხლის სამართლის საპროცესო კოდექსი",
    "სამოქალაქო საპროცესო კოდექსი",
    "შრომის კოდექსი",
    "საგადასახადო კოდექსი",
    "კონსტიტუცია",
    "ზოგადი ადმინისტრაციული კოდექსი",
    "სამეწარმეო კანონი",
    "საოჯახო კანონი",
    "მიწის კოდექსი",
]


class CitationService:
    """Extracts and verifies law citations from AI-generated text."""

    def __init__(self, chroma: ChromaClient | None = None):
        self._chroma = chroma

    @property
    def chroma(self) -> ChromaClient:
        if self._chroma is None:
            self._chroma = get_chroma_client()
        return self._chroma

    def extract_citations(self, text: str) -> list[dict[str, str]]:
        """Extract law citations from text."""
        citations = []
        articles = ARTICLE_PATTERN.findall(text)

        for article_num in articles:
            # Try to find the code name preceding this article reference
            code_name = self._find_code_name(text, article_num)
            citations.append({
                "article_number": f"მუხლი {article_num}",
                "code_name": code_name or "Unknown",
                "raw_text": f"{code_name}, მუხლი {article_num}" if code_name else f"მუხლი {article_num}",
            })

        # Deduplicate
        seen = set()
        unique = []
        for c in citations:
            key = (c["code_name"], c["article_number"])
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    def _find_code_name(self, text: str, article_num: str) -> str | None:
        """Find the code name closest to and preceding the article reference."""
        pattern = f"მუხლი\\s+{article_num}"
        match = re.search(pattern, text)
        if not match:
            return None

        # Search backwards from the match for a known code name
        preceding = text[:match.start()]
        best_name = None
        best_pos = -1

        for name in CODE_NAMES:
            pos = preceding.rfind(name)
            if pos > best_pos:
                best_pos = pos
                best_name = name

        return best_name

    def verify_citations(
        self,
        citations: list[dict[str, str]],
        retrieved_chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Verify extracted citations against retrieved corpus chunks.

        Returns enriched citations with verification status and metadata.
        """
        # Build lookup from retrieved chunks
        chunk_lookup: dict[str, dict] = {}
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            key = (meta.get("code_name", ""), meta.get("article_number", ""))
            if key not in chunk_lookup:
                chunk_lookup[key] = {
                    "content": chunk.get("content", ""),
                    "metadata": meta,
                }

        verified = []
        for citation in citations:
            key = (citation["code_name"], citation["article_number"])
            if key in chunk_lookup:
                info = chunk_lookup[key]
                verified.append({
                    **citation,
                    "verified": True,
                    "article_url": info["metadata"].get("article_url", ""),
                    "source_url": info["metadata"].get("source_url", ""),
                    "citation_text": info["metadata"].get("citation_text", ""),
                })
            else:
                verified.append({
                    **citation,
                    "verified": False,
                    "article_url": "",
                    "source_url": "",
                    "citation_text": "",
                })

        n_verified = sum(1 for v in verified if v["verified"])
        logger.info(
            "citations_verified",
            total=len(verified),
            verified=n_verified,
            unverified=len(verified) - n_verified,
        )
        return verified


_citation_service = None

def get_citation_service():
    global _citation_service
    if _citation_service is None:
        _citation_service = CitationService()
    return _citation_service
