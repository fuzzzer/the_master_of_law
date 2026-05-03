"""
Full-text search index builder.

Builds supplementary search indices for hybrid search combining
vector similarity with keyword matching.
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.config import settings
from pipeline.models.legal_chunk import LegalChunk
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


class SearchIndexBuilder:
    """Build a local JSON-based inverted index for hybrid search."""

    def __init__(self, index_dir: Path | None = None) -> None:
        self._dir = index_dir or settings.index_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def build(self, chunks: list[LegalChunk]) -> dict:
        """
        Build an inverted index from chunks and persist to disk.

        Returns a summary dict with statistics.
        """
        # Article-number index
        article_index: dict[str, list[str]] = {}
        # Code-name index
        code_index: dict[str, list[str]] = {}
        # Domain index
        domain_index: dict[str, list[str]] = {}

        for chunk in chunks:
            cid = chunk.chunk_id
            article_index.setdefault(chunk.article_number, []).append(cid)
            code_index.setdefault(chunk.code_name, []).append(cid)
            for domain in chunk.legal_domains:
                domain_index.setdefault(domain, []).append(cid)

        # Persist
        self._write_json("article_index.json", article_index)
        self._write_json("code_index.json", code_index)
        self._write_json("domain_index.json", domain_index)

        stats = {
            "total_chunks": len(chunks),
            "unique_articles": len(article_index),
            "unique_codes": len(code_index),
            "unique_domains": len(domain_index),
        }
        self._write_json("index_stats.json", stats)
        logger.info("Search index built: %s", stats)
        return stats

    def _write_json(self, filename: str, data: dict) -> None:
        path = self._dir / filename
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
