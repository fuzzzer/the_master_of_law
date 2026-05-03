"""Tests for the chunker module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.chunker.legal_chunker import LegalChunker
from pipeline.chunker.chunk_validator import validate_chunk
from pipeline.chunker.overlap_strategy import OverlapStrategy
from pipeline.models.document_metadata import DocumentMetadata, LegalDocumentType
from pipeline.models.legal_article import LegalArticle
from pipeline.models.legal_chunk import LegalChunk
from pipeline.models.legal_document import LegalDocument


def _make_document(articles: list[LegalArticle]) -> LegalDocument:
    """Helper to create a test document."""
    return LegalDocument(
        metadata=DocumentMetadata(
            document_id="test_code",
            title_ka="სატესტო კოდექსი",
            document_type=LegalDocumentType.CODE,
        ),
        articles=articles,
    )


def _make_article(
    number: str, content: str, title: str = "", chapter: str | None = None,
) -> LegalArticle:
    return LegalArticle(
        article_id=f"test_code.article_{number}",
        document_id="test_code",
        code_name="სატესტო კოდექსი",
        chapter=chapter,
        article_number=f"მუხლი {number}",
        article_title=title or None,
        content_ka=content,
    )


class TestLegalChunker:
    """Test the structure-aware legal chunker."""

    def test_single_article_single_chunk(self) -> None:
        article = _make_article("1", "ეს არის მოკლე ტექსტი.")
        doc = _make_document([article])
        chunker = LegalChunker(max_tokens=1000)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) == 1
        assert chunks[0].article_number == "მუხლი 1"
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks_in_article == 1

    def test_long_article_splits(self) -> None:
        # Create an article with many paragraphs that exceed max tokens
        paragraphs = "\n".join(
            f"{i}. ეს არის ძალიან გრძელი პუნქტი რომელიც შეიცავს ბევრ სიტყვას და წინადადებებს. " * 5
            for i in range(1, 20)
        )
        article = _make_article("1", paragraphs)
        doc = _make_document([article])
        chunker = LegalChunker(max_tokens=200)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.total_chunks_in_article == len(chunks)

    def test_header_injection(self) -> None:
        article = _make_article(
            "5", "ტექსტი.", title="ტესტის სათაური", chapter="I - ტესტი",
        )
        doc = _make_document([article])
        chunker = LegalChunker(max_tokens=1000)
        chunks = chunker.chunk_document(doc)

        assert len(chunks) == 1
        # Chunk content should contain the code name and chapter
        assert "სატესტო კოდექსი" in chunks[0].content
        assert "მუხლი 5" in chunks[0].content

    def test_disclaimer_added(self) -> None:
        article = _make_article("1", "ტექსტი.")
        doc = _make_document([article])
        chunks = LegalChunker().chunk_document(doc)

        assert "matsne.gov.ge" in chunks[0].content

    def test_empty_article_skipped(self) -> None:
        article = _make_article("1", "")
        doc = _make_document([article])
        chunks = LegalChunker().chunk_document(doc)
        assert len(chunks) == 0


class TestOverlapStrategy:
    def test_compute_overlap(self) -> None:
        strategy = OverlapStrategy(ratio=0.12, min_overlap_chars=80, max_overlap_chars=500)
        assert strategy.compute_overlap(1000) == max(80, min(120, 500))

    def test_min_overlap(self) -> None:
        strategy = OverlapStrategy(ratio=0.01, min_overlap_chars=80)
        assert strategy.compute_overlap(100) == 80

    def test_max_overlap(self) -> None:
        strategy = OverlapStrategy(ratio=0.5, max_overlap_chars=500)
        assert strategy.compute_overlap(10000) == 500


class TestChunkValidator:
    def test_valid_chunk(self) -> None:
        chunk = LegalChunk(
            chunk_id="test.chunk_0", document_id="test",
            content="ტექსტი მუხლი 1 " * 10,
            content_ka="ტექსტი მუხლი 1 " * 10,
            code_name="test", article_number="მუხლი 1",
            chunk_index=0, total_chunks_in_article=1, token_count=50,
        )
        warnings = validate_chunk(chunk)
        assert len(warnings) == 0

    def test_short_chunk_warning(self) -> None:
        chunk = LegalChunk(
            chunk_id="test.chunk_0", document_id="test",
            content="x", content_ka="x",
            code_name="test", article_number="მუხლი 1",
            chunk_index=0, total_chunks_in_article=1, token_count=1,
        )
        warnings = validate_chunk(chunk)
        assert any("too short" in w for w in warnings)
