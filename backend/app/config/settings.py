"""
Application settings — loaded from environment variables / .env file.

Usage:
    from app.config.settings import settings
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings, validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    app_name: str = Field(default="the-master-of-law")
    app_env: str = Field(default="development")
    app_port: int = Field(default=8000)
    app_secret_key: str = Field(default="change-me-in-production")
    app_cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Comma-separated list of allowed CORS origins",
    )

    # ── Google Cloud / Vertex AI ─────────────────────────────
    google_cloud_project: str = Field(default="gen-lang-client-0225498420")
    google_cloud_location: str = Field(default="global")
    # Note: Vertex AI authenticates via ADC (GOOGLE_APPLICATION_CREDENTIALS).
    # No API key needed — set GCP_SA_KEY_PATH in .env for Docker.
    gemini_model: str = Field(default="gemini-3.1-pro-preview")
    gemini_chat_model: str = Field(default="gemini-3-flash-preview")
    embedding_model: str = Field(default="gemini-embedding-001")
    embedding_dimensions: int = Field(default=768)

    # ── Vector Store (ChromaDB) ──────────────────────────────
    chroma_persist_dir: Path = Field(
        default=Path("../law_corpus/data/chroma"),
        description="Path to pre-built ChromaDB data",
    )
    chroma_collection_name: str = Field(default="georgian_laws")

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://mol_user:corpus_dev_pw@localhost:5432/master_of_law",
    )
    database_pool_size: int = Field(default=10)

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── Firebase ─────────────────────────────────────────────
    firebase_project_id: str = Field(default="")
    firebase_service_account_key: str = Field(default="")

    # ── Credit System ────────────────────────────────────────
    free_tier_daily_credits: int = Field(default=5)
    credit_cost_chat: int = Field(default=1)
    credit_cost_analysis: int = Field(default=2)
    credit_cost_case_file: int = Field(default=3)

    # ── Rate Limiting ────────────────────────────────────────
    rate_limit_free_per_minute: int = Field(default=5)
    rate_limit_pro_per_minute: int = Field(default=30)
    rate_limit_admin_per_minute: int = Field(default=120)

    # ── Logging ──────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    # ── Derived ──────────────────────────────────────────────
    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Singleton — import this everywhere.
settings = Settings()
