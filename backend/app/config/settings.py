"""
Application settings — loaded from environment variables / .env file.

Usage:
    from app.config.settings import settings
"""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
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
    # ── Model tiers ──────────────────────────────────────────
    # Two named tiers, both settable from the environment. Every call site
    # picks a TIER, never a model id, so retargeting the whole app is a
    # two-line env change and no code edit.
    #
    #   STRONG — reasoning that a wrong answer would harm the user:
    #            phase-2 generation + tools, case analysis, documents.
    #   CHEAP  — mechanical work whose output is checked or discarded:
    #            guardrail, planning, rerank, verification, guard passes.
    #
    # They currently resolve to the same model (gemini-3.7-flash). The split
    # is kept because it is a COST and TRUST boundary, not a model-name alias:
    # the moment the tiers diverge again, every call site is already correct.
    gemini_strong_model: str = Field(
        default="gemini-3.7-flash",
        validation_alias=AliasChoices("GEMINI_STRONG_MODEL", "GEMINI_MODEL"),
        description="Model for high-stakes generation (phase 2, case analysis, documents).",
    )
    gemini_cheap_model: str = Field(
        default="gemini-3.7-flash",
        validation_alias=AliasChoices("GEMINI_CHEAP_MODEL", "GEMINI_CHAT_MODEL"),
        description="Model for planning, reranking, verification and guard passes.",
    )
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
    # ON by default as of the 3.7-flash retarget. These three were shipped
    # default-off as opt-in experiments and then run true in dev for months,
    # which meant the reviewed system and the deployed one enforced different
    # invariants with nothing surfacing the gap. Defaulting them ON makes the
    # code the source of truth; set the env var to false to opt OUT.
    full_code_injection: bool = Field(
        default=True,
        description="Inject the full text of the classified domain's legal code "
                    "into the prompt (statute retrieval becomes deterministic). "
                    "Only unambiguous domain->code pairs, and only when the code "
                    "fully fits the char budget.",
    )
    full_code_injection_max_chars: int = Field(
        default=300_000,
        description="Combined char budget for injected codes; codes that don't "
                    "fully fit are skipped (a truncated code defeats the purpose)",
    )
    faithfulness_check: bool = Field(
        default=True,
        description="Run a batched faithfulness pass over each response "
                    "(sentence-level supported/unsupported check + correction) "
                    "on the CHEAP tier. One extra model call per chat.",
    )
    anchoring_repair: bool = Field(
        default=True,
        description="When the unanchored legal-claim rate is >= 5%, run one "
                    "CHEAP-tier pass that anchors claim paragraphs using ONLY the "
                    "citations already present in the response. Also gates the "
                    "court-practice attribution guard.",
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
