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

# Code names as they appear in the corpus (full "საქართველოს" prefix form).
# The model may output shorter forms — verify_citations handles both via normalization.
CODE_NAMES = [
    "საქართველოს სისხლის სამართლის კოდექსი",
    "საქართველოს სამოქალაქო კოდექსი",
    "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
    "საქართველოს სისხლის სამართლის საპროცესო კოდექსი",
    "საქართველოს სამოქალაქო საპროცესო კოდექსი",
    "საქართველოს შრომის კოდექსი",
    "საქართველოს საგადასახადო კოდექსი",
    "საქართველოს კონსტიტუცია",
    "საქართველოს ზოგადი ადმინისტრაციული კოდექსი",
    "საქართველოს ადმინისტრაციული საპროცესო კოდექსი",
    "ნარკოტიკული საშუალებების შესახებ კანონი",
    "პერსონალურ მონაცემთა დაცვის შესახებ",
    # Short forms the model commonly outputs (without "საქართველოს" prefix)
    "სისხლის სამართლის კოდექსი",
    "სამოქალაქო კოდექსი",
    "სამოქალაქო საპროცესო კოდექსი",
    "შრომის კოდექსი",
    "საგადასახადო კოდექსი",
    "კონსტიტუცია",
    "ზოგადი ადმინისტრაციული კოდექსი",
    "ადმინისტრაციულ სამართალდარღვევათა კოდექსი",
]

_GEO_PREFIX = "საქართველოს "


def _normalize_code_name(name: str) -> str:
    """Strip the 'საქართველოს' prefix for fuzzy matching."""
    return name.removeprefix(_GEO_PREFIX).strip()


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

        Builds a dual-key lookup: one under the full corpus code name and one
        under the normalized (no 'საქართველოს' prefix) form.  This handles the
        mismatch between what the model outputs (short form) and what the corpus
        stores (full form with prefix).

        Returns enriched citations with verification status and metadata.
        """
        chunk_lookup: dict[tuple[str, str], dict] = {}
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            full_code = meta.get("code_name", "")
            article = meta.get("article_number", "")
            normalized_code = _normalize_code_name(full_code)
            entry = {"content": chunk.get("content", ""), "metadata": meta}
            # Store under both full name and normalized (prefix-stripped) name
            for key in [(full_code, article), (normalized_code, article)]:
                if key not in chunk_lookup:
                    chunk_lookup[key] = entry

        verified = []
        for citation in citations:
            code = citation["code_name"]
            article = citation["article_number"]
            normalized = _normalize_code_name(code)
            # Try full name first, then normalized
            info = chunk_lookup.get((code, article)) or chunk_lookup.get((normalized, article))
            if info:
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

    def verify_against_corpus(
        self,
        citations: list[dict[str, str]],
        already_retrieved: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Actively search the corpus for unverified citations.

        Unlike verify_citations() which only checks already-retrieved chunks,
        this method performs exact metadata searches in ChromaDB for any
        citations not found in the initial retrieval.

        Returns
        -------
        dict with keys:
            verified: Citations confirmed in already_retrieved chunks.
            corpus_found: Citations NOT in chunks but found via metadata search.
            not_found: Citations not in corpus at all (likely hallucinated).
        """
        chunk_lookup: dict[tuple[str, str], dict] = {}
        for chunk in already_retrieved:
            meta = chunk.get("metadata", {})
            full_code = meta.get("code_name", "")
            article = meta.get("article_number", "")
            normalized_code = _normalize_code_name(full_code)
            entry = {"content": chunk.get("content", ""), "metadata": meta}
            for key in [(full_code, article), (normalized_code, article)]:
                if key not in chunk_lookup:
                    chunk_lookup[key] = entry

        verified: list[dict[str, Any]] = []
        corpus_found: list[dict[str, Any]] = []
        not_found: list[dict[str, Any]] = []

        for citation in citations:
            code = citation["code_name"]
            article = citation["article_number"]
            normalized = _normalize_code_name(code)

            info = chunk_lookup.get((code, article)) or chunk_lookup.get((normalized, article))
            if info:
                verified.append({
                    **citation,
                    "verified": True,
                    "article_url": info["metadata"].get("article_url", ""),
                    "citation_text": info["metadata"].get("citation_text", ""),
                    "content": info["content"][:500],
                })
                continue

            corpus_hit = self._search_corpus_exact(article, code)
            if corpus_hit:
                corpus_found.append({
                    **citation,
                    "verified": True,
                    "article_url": corpus_hit["metadata"].get("article_url", ""),
                    "citation_text": corpus_hit["metadata"].get("citation_text", ""),
                    "content": corpus_hit.get("content", "")[:500],
                    "corpus_code_name": corpus_hit["metadata"].get("code_name", ""),
                })
            else:
                not_found.append({
                    **citation,
                    "verified": False,
                })

        logger.info(
            "citations_corpus_verified",
            verified=len(verified),
            corpus_found=len(corpus_found),
            not_found=len(not_found),
        )
        return {
            "verified": verified,
            "corpus_found": corpus_found,
            "not_found": not_found,
        }

    def _search_corpus_exact(
        self, article_number: str, code_name: str
    ) -> dict[str, Any] | None:
        """Search ChromaDB by exact article metadata."""
        if not article_number.startswith("მუხლი"):
            article_number = f"მუხლი {article_number.strip()}"

        where: dict[str, Any] = {"article_number": {"$eq": article_number}}
        if code_name and code_name != "Unknown":
            full_name = code_name if code_name.startswith("საქართველოს") else f"საქართველოს {code_name}"
            where = {"$and": [
                {"article_number": {"$eq": article_number}},
                {"$or": [
                    {"code_name": {"$eq": full_name}},
                    {"code_name": {"$eq": code_name}},
                ]},
            ]}

        try:
            hits = self.chroma.search_by_metadata(
                where=where,
                collections=["georgian_laws"],
                limit=3,
            )
            return hits[0] if hits else None
        except Exception as e:
            logger.warning("corpus_exact_search_failed", error=str(e))
            return None


_citation_service = None

def get_citation_service():
    global _citation_service
    if _citation_service is None:
        _citation_service = CitationService()
    return _citation_service
