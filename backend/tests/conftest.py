"""
Test fixtures shared across all test modules.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Mock data ─────────────────────────────────────────────────

MOCK_USER_UID = "test-user-001"
MOCK_USER_EMAIL = "test@masteroflaw.ge"
MOCK_USER_ID = uuid.uuid4()
MOCK_CONVERSATION_ID = uuid.uuid4()

MOCK_CHUNKS = [
    {
        "chunk_id": "criminal_code_chunk_1",
        "content": "მუხლი 11. სისხლისსამართლებრივი პასუხისმგებლობის ასაკი...",
        "metadata": {
            "code_name": "სისხლის სამართლის კოდექსი",
            "article_number": "მუხლი 11",
            "article_title": "სისხლისსამართლებრივი პასუხისმგებლობის ასაკი",
            "citation_text": "საქართველოს სისხლის სამართლის კოდექსი, მუხლი 11",
            "article_url": "https://matsne.gov.ge/ka/document/view/16426#article_11",
            "source_url": "https://matsne.gov.ge/ka/document/view/16426",
        },
        "distance": 0.15,
    },
    {
        "chunk_id": "criminal_code_chunk_2",
        "content": "მუხლი 120. ჯანმრთელობის განზრახ მძიმე დაზიანება...",
        "metadata": {
            "code_name": "სისხლის სამართლის კოდექსი",
            "article_number": "მუხლი 120",
            "article_title": "ჯანმრთელობის განზრახ მძიმე დაზიანება",
            "citation_text": "საქართველოს სისხლის სამართლის კოდექსი, მუხლი 120",
            "article_url": "https://matsne.gov.ge/ka/document/view/16426#article_120",
            "source_url": "https://matsne.gov.ge/ka/document/view/16426",
        },
        "distance": 0.22,
    },
]


@pytest.fixture
def mock_chunks():
    """Sample law chunks for testing."""
    return MOCK_CHUNKS.copy()


@pytest.fixture
def mock_user_info():
    """Mock user info as set by auth middleware."""
    return {
        "uid": MOCK_USER_UID,
        "email": MOCK_USER_EMAIL,
        "tier": "FREE",
    }
