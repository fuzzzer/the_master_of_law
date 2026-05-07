"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_html() -> str:
    """Load the sample Civil Code HTML fixture."""
    return (FIXTURES_DIR / "sample_article.html").read_text("utf-8")


@pytest.fixture
def sample_html_bytes() -> bytes:
    """Load the sample Civil Code HTML fixture as bytes."""
    return (FIXTURES_DIR / "sample_article.html").read_bytes()


@pytest.fixture
def sample_law_meta() -> dict:
    """Load the sample law metadata fixture."""
    import json

    return json.loads((FIXTURES_DIR / "sample_law.json").read_text("utf-8"))


@pytest.fixture
def sample_chunk_data() -> dict:
    """Load the sample chunk fixture."""
    import json

    return json.loads((FIXTURES_DIR / "sample_chunk.json").read_text("utf-8"))
