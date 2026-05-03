"""
Metadata model for a Georgian legal document.

Captures all bibliographic and provenance information needed for
citation, filtering, and incremental update detection.
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class LegalDocumentType(str, enum.Enum):
    """Classification of Georgian normative acts."""
    CONSTITUTION = "constitution"
    CONSTITUTIONAL_AGREEMENT = "constitutional_agreement"
    INTERNATIONAL_TREATY = "international_treaty"
    ORGANIC_LAW = "organic_law"
    CODE = "code"
    LAW = "law"
    PRESIDENTIAL_DECREE = "presidential_decree"
    GOVERNMENT_RESOLUTION = "government_resolution"
    MINISTERIAL_ORDER = "ministerial_order"
    MUNICIPAL_ACT = "municipal_act"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    """Metadata for a single legal document / normative act."""

    document_id: str = Field(
        ..., description="Unique internal identifier (slug-style, e.g. 'civil_code')"
    )
    title_ka: str = Field(
        ..., description="Title in Georgian (Mkhedruli)"
    )
    title_en: Optional[str] = Field(
        default=None, description="Title in English (if available)"
    )
    document_type: LegalDocumentType = Field(
        ..., description="Category of the normative act"
    )
    document_number: str = Field(
        default="", description="Official document / registration number"
    )

    # ── Temporal ─────────────────────────────────────────────
    adoption_date: Optional[date] = Field(
        default=None, description="Date the act was adopted / passed"
    )
    effective_date: Optional[date] = Field(
        default=None, description="Date the act came into force"
    )
    last_amendment_date: Optional[date] = Field(
        default=None, description="Date of the most recent amendment"
    )
    last_amendment_number: Optional[str] = Field(
        default=None, description="Registration number of the latest amendment"
    )

    # ── Provenance ───────────────────────────────────────────
    issuing_body: str = Field(
        default="", description="Parliament, President, Government, etc."
    )
    legal_domain: list[str] = Field(
        default_factory=list,
        description="Subject-matter tags (e.g. ['criminal', 'property'])",
    )
    source_url: str = Field(
        default="", description="Canonical URL on matsne.gov.ge"
    )
    language: str = Field(
        default="ka", description="Primary language code"
    )
    version: str = Field(
        default="consolidated",
        description="'consolidated' or a specific historical version identifier",
    )

    # ── Status ───────────────────────────────────────────────
    is_in_force: bool = Field(
        default=True, description="Whether the act is currently in force"
    )
    superseded_by: Optional[str] = Field(
        default=None,
        description="document_id of the act that replaced this one (if any)",
    )

    # ── Scrape metadata ──────────────────────────────────────
    scraped_at: Optional[datetime] = Field(
        default=None, description="UTC timestamp when the document was last scraped"
    )
    content_hash: Optional[str] = Field(
        default=None, description="SHA-256 of the raw content for change detection"
    )
