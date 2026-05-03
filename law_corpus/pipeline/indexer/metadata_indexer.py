"""
PostgreSQL metadata indexer with full-text search.

Uses SQLAlchemy async engine to store legal articles and their metadata
in a relational database alongside a GIN-indexed tsvector column.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from pipeline.config import settings
from pipeline.models.legal_chunk import LegalChunk
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


# ── ORM Model ───────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class LegalArticleRow(Base):
    """SQLAlchemy model mirroring the spec's PostgreSQL schema."""
    __tablename__ = "legal_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String(255), nullable=False, index=True)
    article_number = Column(String(50), nullable=False)
    title_ka = Column(Text)
    title_en = Column(Text)
    content_ka = Column(Text, nullable=False)
    content_en = Column(Text)
    code_name = Column(String(255), nullable=False, index=True)
    book = Column(String(255))
    chapter = Column(String(255))
    legal_domains = Column(ARRAY(Text), default=[])
    keywords_ka = Column(ARRAY(Text), default=[])
    keywords_en = Column(ARRAY(Text), default=[])
    cross_references = Column(ARRAY(Text), default=[])
    effective_date = Column(Date)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_current = Column(Boolean, default=True)

    # Source provenance — essential for AI citations
    source_url = Column(Text, default="", doc="Canonical matsne.gov.ge URL")
    article_url = Column(Text, default="", doc="Deep-link to this specific article")
    document_number = Column(String(100), default="", doc="Official registration number")
    adoption_date = Column(Date, doc="Date the law was adopted")
    citation_text = Column(Text, default="", doc="Pre-formatted citation string")

    __table_args__ = (
        Index("idx_articles_document", "document_id"),
        Index("idx_articles_code", "code_name"),
    )


# ── Indexer ──────────────────────────────────────────────────

class MetadataIndexer:
    """Indexes legal articles into PostgreSQL with full-text search."""

    def __init__(self, database_url: str | None = None) -> None:
        self._url = database_url or settings.database_url
        self._engine = create_async_engine(self._url, echo=False)
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False,
        )

    async def create_tables(self) -> None:
        """Create all tables and the full-text search index."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            # Create tsvector GIN index (raw SQL — not expressible via ORM)
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = 'idx_articles_search'
                    ) THEN
                        EXECUTE 'CREATE INDEX idx_articles_search ON legal_articles
                            USING GIN (
                                to_tsvector(''simple'',
                                    coalesce(content_ka, '''') || '' '' ||
                                    coalesce(content_en, '''')
                                )
                            )';
                    END IF;
                END
                $$;
            """))

            # GIN index on legal_domains array
            await conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = 'idx_articles_domains'
                    ) THEN
                        EXECUTE 'CREATE INDEX idx_articles_domains
                            ON legal_articles USING GIN (legal_domains)';
                    END IF;
                END
                $$;
            """))

        logger.info("Database tables and indices created")

    async def index_chunks(self, chunks: list[LegalChunk]) -> int:
        """Upsert chunks as article rows (one per article)."""
        count = 0
        async with self._session_factory() as session:
            async with session.begin():
                for chunk in chunks:
                    row = LegalArticleRow(
                        document_id=chunk.document_id,
                        article_number=chunk.article_number,
                        title_ka=chunk.article_title,
                        content_ka=chunk.content_ka,
                        content_en=chunk.content_en,
                        code_name=chunk.code_name,
                        book=chunk.book,
                        chapter=chunk.chapter,
                        legal_domains=chunk.legal_domains,
                        keywords_ka=chunk.keywords_ka,
                        keywords_en=chunk.keywords_en,
                        cross_references=chunk.cross_references,
                        effective_date=chunk.effective_date,
                        last_updated=chunk.last_updated,
                        is_current=chunk.is_current,
                        # Source provenance
                        source_url=chunk.source_url,
                        article_url=chunk.article_url,
                        document_number=chunk.document_number,
                        adoption_date=chunk.adoption_date,
                        citation_text=chunk.citation_text,
                    )
                    session.add(row)
                    count += 1
        logger.info("Indexed %d articles in PostgreSQL", count)
        return count

    async def full_text_search(
        self, query: str, limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Run a full-text search against the legal_articles table."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT id, document_id, article_number, code_name,
                           title_ka, left(content_ka, 500) as snippet,
                           source_url, article_url, document_number, citation_text,
                           ts_rank(
                               to_tsvector('simple', coalesce(content_ka, '') || ' ' || coalesce(content_en, '')),
                               plainto_tsquery('simple', :query)
                           ) as rank
                    FROM legal_articles
                    WHERE to_tsvector('simple', coalesce(content_ka, '') || ' ' || coalesce(content_en, ''))
                          @@ plainto_tsquery('simple', :query)
                    ORDER BY rank DESC
                    LIMIT :limit
                """),
                {"query": query, "limit": limit},
            )
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

    async def close(self) -> None:
        await self._engine.dispose()
