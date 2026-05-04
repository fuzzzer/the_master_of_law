"""
Central configuration for the Georgian Law Corpus Pipeline.

All settings are loaded from environment variables (via .env files) and
validated through Pydantic Settings.  Import ``settings`` to access them
anywhere in the codebase:

    from pipeline.config import settings
"""

from __future__ import annotations

import enum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Enums ────────────────────────────────────────────────────

class VectorStoreBackend(str, enum.Enum):
    """Supported vector-store backends."""
    CHROMA = "chroma"
    VERTEX = "vertex"


class LogLevel(str, enum.Enum):
    """Supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ── Settings ─────────────────────────────────────────────────

class Settings(BaseSettings):
    """Application settings — sourced from env vars / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Google Cloud / Vertex AI ─────────────────────────────
    google_cloud_project: str = Field(
        default="",
        description="GCP project ID for Vertex AI",
    )
    google_cloud_location: str = Field(
        default="us-central1",
        description="GCP region",
    )
    vertex_ai_api_key: str = Field(
        default="",
        description="Vertex AI API key (if using key-based auth)",
    )
    embedding_model: str = Field(
        default="gemini-embedding-001",
        description="Gemini embedding model name (via Google Gen AI SDK)",
    )
    embedding_dimensions: int = Field(
        default=768,
        description="Embedding vector dimensionality",
    )

    # ── Vector Store ─────────────────────────────────────────
    vector_store_backend: VectorStoreBackend = Field(
        default=VectorStoreBackend.CHROMA,
        description="Which vector store to use",
    )
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma"),
        description="ChromaDB persistent storage directory",
    )
    vertex_vector_search_index_id: str = Field(
        default="",
        description="Vertex AI Vector Search index resource ID",
    )
    vertex_vector_search_endpoint_id: str = Field(
        default="",
        description="Vertex AI Vector Search endpoint resource ID",
    )

    # ── PostgreSQL ───────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/law_corpus",
        description="Async SQLAlchemy database URL",
    )

    # ── Scraping ─────────────────────────────────────────────
    scrape_delay_seconds: float = Field(
        default=2.0,
        ge=1.0,
        description="Minimum seconds between requests to any single host",
    )
    scrape_max_concurrent: int = Field(
        default=3,
        ge=1,
        description="Maximum concurrent scrape connections",
    )
    scrape_user_agent: str = Field(
        default="LawCorpusBot/1.0 (research; contact@example.com)",
        description="User-Agent header sent with every request",
    )

    # ── Pipeline ─────────────────────────────────────────────
    log_level: LogLevel = Field(default=LogLevel.INFO)
    data_dir: Path = Field(
        default=Path("./data"),
        description="Root directory for all pipeline data",
    )
    checkpoint_dir: Path = Field(
        default=Path("./data/checkpoints"),
        description="Directory for pipeline checkpoint files",
    )

    # ── Chunking ─────────────────────────────────────────────
    chunk_max_tokens: int = Field(
        default=1000,
        description="Maximum tokens per chunk before splitting",
    )
    chunk_overlap_ratio: float = Field(
        default=0.12,
        ge=0.0,
        le=0.5,
        description="Overlap ratio between adjacent chunks",
    )

    # ── Embedding batch ──────────────────────────────────────
    embedding_batch_size: int = Field(
        default=100,
        ge=1,
        le=250,
        description="Number of texts per embedding API request",
    )
    embedding_requests_per_minute: int = Field(
        default=600,
        ge=1,
        description="Rate limit for embedding API calls",
    )

    # ── Derived paths ────────────────────────────────────────

    @property
    def raw_html_dir(self) -> Path:
        return self.data_dir / "raw" / "html"

    @property
    def raw_pdf_dir(self) -> Path:
        return self.data_dir / "raw" / "pdf"

    @property
    def raw_metadata_dir(self) -> Path:
        return self.data_dir / "raw" / "metadata"

    @property
    def parsed_dir(self) -> Path:
        return self.data_dir / "parsed"

    @property
    def chunks_dir(self) -> Path:
        return self.data_dir / "chunks"

    @property
    def embeddings_dir(self) -> Path:
        return self.data_dir / "embeddings"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    def ensure_dirs(self) -> None:
        """Create every data directory that the pipeline needs."""
        for d in (
            self.raw_html_dir,
            self.raw_pdf_dir,
            self.raw_metadata_dir,
            self.parsed_dir,
            self.chunks_dir,
            self.embeddings_dir,
            self.index_dir,
            self.checkpoint_dir,
            self.chroma_persist_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    @field_validator("data_dir", "checkpoint_dir", "chroma_persist_dir", mode="before")
    @classmethod
    def _resolve_path(cls, v: str | Path) -> Path:
        return Path(v).resolve()


# Singleton instance — import this everywhere.
settings = Settings()
