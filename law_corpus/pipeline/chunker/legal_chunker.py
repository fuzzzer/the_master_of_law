"""
Structure-aware legal text chunker.

Respects the Georgian legal hierarchy when splitting text:
  Article → Paragraph → Sentence  (never splits mid-paragraph if avoidable).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import tiktoken

from pipeline.chunker.overlap_strategy import OverlapStrategy
from pipeline.config import settings
from pipeline.models.legal_article import LegalArticle
from pipeline.models.legal_chunk import LegalChunk
from pipeline.models.legal_document import LegalDocument
from pipeline.utils.deduplicator import content_hash_short
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

# tiktoken encoder for token counting (cl100k_base covers most models)
_ENCODER = tiktoken.get_encoding("cl100k_base")

DISCLAIMER = (
    "ეს მასალა მხოლოდ საინფორმაციო მიზნებისთვისაა. "
    "ოფიციალური ტექსტისთვის იხილეთ matsne.gov.ge"
)


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


class LegalChunker:
    """Structure-aware chunker for Georgian legal documents."""

    def __init__(
        self,
        max_tokens: int | None = None,
        overlap: OverlapStrategy | None = None,
    ) -> None:
        self.max_tokens = max_tokens or settings.chunk_max_tokens
        self.overlap = overlap or OverlapStrategy(ratio=settings.chunk_overlap_ratio)

    def chunk_document(self, document: LegalDocument) -> list[LegalChunk]:
        """Chunk an entire legal document into embeddable pieces."""
        all_chunks: list[LegalChunk] = []

        for article in document.articles:
            article_chunks = self._chunk_article(article, document)
            all_chunks.extend(article_chunks)

        logger.info(
            "Chunked %s: %d articles → %d chunks",
            document.document_id, len(document.articles), len(all_chunks),
        )
        return all_chunks

    def _chunk_article(
        self,
        article: LegalArticle,
        document: LegalDocument,
    ) -> list[LegalChunk]:
        """Chunk a single article, splitting at paragraph boundaries if needed."""
        header = self._build_header(article, document)
        content = article.content_ka.strip()

        if not content:
            return []

        full_text = f"{header}\n\n{content}\n\n{DISCLAIMER}"
        token_count = _count_tokens(full_text)

        # Case 1: Article fits in a single chunk
        if token_count <= self.max_tokens:
            return [self._make_chunk(
                article=article,
                document=document,
                content=full_text,
                content_ka=content,
                chunk_index=0,
                total_chunks=1,
                token_count=token_count,
            )]

        # Case 2: Split at paragraph boundaries
        chunks: list[LegalChunk] = []
        if article.paragraphs:
            segments = [
                f"{p.number}. {p.text}" for p in article.paragraphs
            ]
        else:
            # Fall back to splitting at numbered lines
            segments = self._split_by_paragraphs(content)

        # Group segments into chunks that fit within the token limit
        current_segments: list[str] = []
        current_tokens = _count_tokens(header) + _count_tokens(DISCLAIMER) + 10

        for seg in segments:
            seg_tokens = _count_tokens(seg)
            if current_tokens + seg_tokens > self.max_tokens and current_segments:
                # Flush current group
                chunk_content_ka = "\n".join(current_segments)
                chunk_text = f"{header}\n\n{chunk_content_ka}\n\n{DISCLAIMER}"
                chunks.append(self._make_chunk(
                    article=article,
                    document=document,
                    content=chunk_text,
                    content_ka=chunk_content_ka,
                    chunk_index=len(chunks),
                    total_chunks=-1,  # will be updated
                    token_count=_count_tokens(chunk_text),
                ))
                # Start new group with overlap
                overlap_chars = self.overlap.compute_overlap(len(chunk_content_ka))
                overlap_text = chunk_content_ka[-overlap_chars:]
                current_segments = [overlap_text, seg]
                current_tokens = _count_tokens(header) + _count_tokens(overlap_text) + seg_tokens
            else:
                current_segments.append(seg)
                current_tokens += seg_tokens

        # Flush remaining
        if current_segments:
            chunk_content_ka = "\n".join(current_segments)
            chunk_text = f"{header}\n\n{chunk_content_ka}\n\n{DISCLAIMER}"
            chunks.append(self._make_chunk(
                article=article,
                document=document,
                content=chunk_text,
                content_ka=chunk_content_ka,
                chunk_index=len(chunks),
                total_chunks=-1,
                token_count=_count_tokens(chunk_text),
            ))

        # Fix total_chunks
        for c in chunks:
            c.total_chunks_in_article = len(chunks)

        return chunks

    def _build_header(self, article: LegalArticle, document: LegalDocument) -> str:
        """
        Build the contextual header injected into every chunk.

        Includes full provenance so the AI can cite exact sources:
        law name, official number, hierarchy path, article, and URL.
        """
        meta = document.metadata
        parts = [meta.title_ka]
        if meta.document_number:
            parts.append(f"(#{meta.document_number})")
        if article.book:
            parts.append(f"წიგნი: {article.book}")
        if article.part:
            parts.append(f"კარი: {article.part}")
        if article.chapter:
            parts.append(f"თავი: {article.chapter}")
        parts.append(article.article_number)
        if article.article_title:
            parts.append(article.article_title)

        header = " | ".join(parts)

        # Append source URL line for explicit citation grounding
        if meta.source_url:
            article_url = self._build_article_url(meta.source_url, article.article_number)
            header += f"\nწყარო: {article_url}"
        if meta.adoption_date:
            header += f" | მიღებულია: {meta.adoption_date.isoformat()}"

        return header

    @staticmethod
    def _build_article_url(source_url: str, article_number: str) -> str:
        """
        Build a deep-link URL to a specific article on matsne.gov.ge.

        Example: https://matsne.gov.ge/ka/document/view/31702 + მუხლი 45
              → https://matsne.gov.ge/ka/document/view/31702#article_45
        """
        import re
        num_match = re.search(r"(\d+(?:-\d+)?)", article_number)
        if num_match:
            return f"{source_url.split('?')[0]}#article_{num_match.group(1)}"
        return source_url

    @staticmethod
    def _build_citation(
        code_name: str,
        article_number: str,
        source_url: str,
        document_number: str,
        adoption_date: str | None,
    ) -> str:
        """
        Build a pre-formatted citation string for AI output.

        Example:
            სამოქალაქო კოდექსი, მუხლი 45 (დოკუმენტი #786-IIS, 1997-06-26)
            წყარო: https://matsne.gov.ge/ka/document/view/31702
        """
        parts = [code_name, article_number]
        if document_number:
            parts.append(f"(#{document_number}")
            if adoption_date:
                parts[-1] += f", {adoption_date}"
            parts[-1] += ")"
        citation = ", ".join(parts)
        if source_url:
            citation += f"\nწყარო: {source_url}"
        return citation

    def _make_chunk(
        self,
        article: LegalArticle,
        document: LegalDocument,
        content: str,
        content_ka: str,
        chunk_index: int,
        total_chunks: int,
        token_count: int,
    ) -> LegalChunk:
        meta = document.metadata
        chunk_id = f"{article.article_id}.chunk_{chunk_index}"
        source_url = meta.source_url or ""
        article_url = self._build_article_url(source_url, article.article_number) if source_url else ""
        adoption_str = meta.adoption_date.isoformat() if meta.adoption_date else None

        citation = self._build_citation(
            code_name=article.code_name,
            article_number=article.article_number,
            source_url=article_url,
            document_number=meta.document_number,
            adoption_date=adoption_str,
        )

        return LegalChunk(
            chunk_id=chunk_id,
            document_id=document.document_id,
            content=content,
            content_ka=content_ka,
            content_en=article.content_en,
            code_name=article.code_name,
            book=article.book,
            part=article.part,
            chapter=article.chapter,
            article_number=article.article_number,
            article_title=article.article_title,
            paragraph_number=None,
            # Source provenance — essential for AI citations
            source_url=source_url,
            article_url=article_url,
            document_number=meta.document_number,
            adoption_date=meta.adoption_date,
            citation_text=citation,
            # Chunk position
            chunk_index=chunk_index,
            total_chunks_in_article=total_chunks,
            token_count=token_count,
            legal_domains=meta.legal_domain,
            keywords_ka=[],
            keywords_en=[],
            cross_references=article.cross_references,
            effective_date=article.effective_date,
            last_updated=datetime.now(timezone.utc),
            is_current=not article.is_repealed,
            content_hash=content_hash_short(content),
        )

    @staticmethod
    def _split_by_paragraphs(text: str) -> list[str]:
        """Split text at numbered paragraph boundaries."""
        pattern = re.compile(r"(?=^\s*\d+\s*[.)]\s)", re.MULTILINE)
        segments = pattern.split(text)
        return [s.strip() for s in segments if s.strip()]
