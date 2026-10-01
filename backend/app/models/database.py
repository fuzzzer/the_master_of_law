"""
SQLAlchemy base and database session setup.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


# Engine and session factory — lazy init
_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            echo=False,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
