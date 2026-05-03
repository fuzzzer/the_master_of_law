"""Tests for the indexer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.indexer.search_index_builder import SearchIndexBuilder
from pipeline.models.legal_chunk import LegalChunk


def _make_test_chunk(chunk_id: str, article: str, code: str, domains: list[str]) -> LegalChunk:
    return LegalChunk(
        chunk_id=chunk_id,
        document_id="test_doc",
        content="test content ტესტი",
        content_ka="ტესტი",
        code_name=code,
        article_number=article,
        chunk_index=0,
        total_chunks_in_article=1,
        token_count=10,
        legal_domains=domains,
    )


class TestSearchIndexBuilder:
    """Test the local search index builder."""

    def test_build_creates_files(self, tmp_path: Path) -> None:
        builder = SearchIndexBuilder(index_dir=tmp_path)
        chunks = [
            _make_test_chunk("c1", "მუხლი 1", "სამოქალაქო", ["civil"]),
            _make_test_chunk("c2", "მუხლი 2", "სამოქალაქო", ["civil", "property"]),
            _make_test_chunk("c3", "მუხლი 1", "სისხლის", ["criminal"]),
        ]
        stats = builder.build(chunks)

        assert (tmp_path / "article_index.json").exists()
        assert (tmp_path / "code_index.json").exists()
        assert (tmp_path / "domain_index.json").exists()
        assert (tmp_path / "index_stats.json").exists()

        assert stats["total_chunks"] == 3
        assert stats["unique_articles"] == 2  # მუხლი 1 and მუხლი 2
        assert stats["unique_codes"] == 2
        assert stats["unique_domains"] == 3   # civil, property, criminal

    def test_build_empty(self, tmp_path: Path) -> None:
        builder = SearchIndexBuilder(index_dir=tmp_path)
        stats = builder.build([])
        assert stats["total_chunks"] == 0
