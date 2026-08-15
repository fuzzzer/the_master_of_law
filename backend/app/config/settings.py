"""
Application settings — loaded from environment variables / .env file.

Usage:
    from app.config.settings import settings
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
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
    app_name: str = Field(default="fuzzzy-law")
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
    gemini_api_key: str = Field(
        default="",
        description="If set, all Gemini calls use the Gemini Developer API "
                    "(free tier — good for local debugging) instead of Vertex AI. "
                    "Leave empty to keep Vertex AI with ADC.",
    )

    # ── Vector Store (ChromaDB) ──────────────────────────────
    chroma_persist_dir: Path = Field(
        default=Path("../law_corpus/data/chroma"),
        description="Path to pre-built ChromaDB data",
    )
    chroma_collection_name: str = Field(default="georgian_laws")

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://fuzzzy_user:corpus_dev_pw@localhost:5432/fuzzzy_law",
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

    # ── Pipeline Transparency ────────────────────────────────
    trace_enabled: bool = Field(
        default=True,
        description="Record step-by-step pipeline traces to pipeline_traces",
    )

    # ── Grounding: whole-code context injection (mechanism C) ─
    full_code_injection: bool = Field(
        default=False,
        description="Inject the full text of the classified domain's legal code "
                    "into the prompt (statute retrieval becomes deterministic). "
                    "No-op when disabled — the prod-default path is unchanged.",
    )
    full_code_injection_max_chars: int = Field(
        default=300_000,
        description="Combined char budget for injected codes; codes that don't "
                    "fully fit are skipped (a truncated code defeats the purpose)",
    )
    faithfulness_check: bool = Field(
        default=False,
        description="Run a batched Flash faithfulness pass over each response "
                    "(sentence-level supported/unsupported check + correction). "
                    "One extra model call per chat — no-op when disabled.",
    )
    anchoring_repair: bool = Field(
        default=False,
        description="When the unanchored legal-claim rate is >= 5%, run one "
                    "Flash pass that anchors claim paragraphs using ONLY the "
                    "citations already present in the response. No-op when disabled.",
    )

    # ── Temporary Staging Auth ───────────────────────────────
    admin_api_key: str = Field(default="")
    api_keys_file: Path = Field(default=Path("api_keys.json"))

    @model_validator(mode="after")
    def validate_secrets(self) -> Settings:
        if self.app_env == "production":
            if not self.admin_api_key:
                raise ValueError("admin_api_key must be set in production environment!")
            if self.admin_api_key == "master-admin-key":
                raise ValueError("Insecure default admin_api_key ('master-admin-key') is not allowed in production environment!")
            if self.app_secret_key == "change-me-in-production":
                raise ValueError("Insecure default app_secret_key ('change-me-in-production') is not allowed in production environment!")
        else:
            # In development/test, if admin_api_key is not set, default it to "master-admin-key"
            if not self.admin_api_key:
                self.admin_api_key = "master-admin-key"
        return self

    # ── Derived ──────────────────────────────────────────────
    @property
    def gemini_provider(self) -> str:
        """Active Gemini provider: 'gemini_api' (free tier key) or 'vertex' (ADC)."""
        return "gemini_api" if self.gemini_api_key else "vertex"

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Singleton — import this everywhere.
settings = Settings()
