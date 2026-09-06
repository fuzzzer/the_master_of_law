"""
Test fixtures shared across all test modules.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Mock identifiers ─────────────────────────────────────────

MOCK_USER_UID = "test-user-001"
MOCK_USER_EMAIL = "test@fuzzzylaw.ge"
MOCK_USER_ID = uuid.uuid4()
MOCK_CONVERSATION_ID = uuid.uuid4()

# ── Sample law chunks ────────────────────────────────────────

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
            "_collection": "georgian_laws",
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
            "_collection": "georgian_laws",
        },
        "distance": 0.22,
    },
]


@pytest.fixture(autouse=True)
def _reset_genai_client_cache():
    """Keep the process-global Gemini client cache from leaking across tests.

    create_genai_client memoises one client per credential so that a per-request
    BYOK lookup stays cheap. That cache is deliberately process-wide, which
    makes it shared mutable state between tests: without this, a test that
    warms it decides what the NEXT test observes, and the failure lands on
    whichever test happens to run second.
    """
    from app.integrations.vertex_ai_client import reset_client_cache

    reset_client_cache()
    yield
    reset_client_cache()


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


# ── Database fixtures ────────────────────────────────────────

@pytest.fixture
def mock_db():
    """AsyncMock of AsyncSession with flush/commit/rollback."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db


# ── Gemini / VertexAI fixtures ───────────────────────────────

@pytest.fixture
def mock_gemini():
    """AsyncMock of VertexAIClient with default returns."""
    gemini = AsyncMock()
    gemini.generate = AsyncMock(return_value="Legal analysis response text.")
    gemini.generate_json = AsyncMock(return_value=["query1", "query2"])
    gemini.generate_stream = AsyncMock()

    # create_chat returns a MagicMock with send_message
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"needs_rag": true, "search_queries": ["test query"]}'
    mock_response.candidates = []
    mock_chat.send_message = AsyncMock(return_value=mock_response)
    gemini.create_chat = AsyncMock(return_value=mock_chat)

    return gemini


# ── ChromaDB fixtures ────────────────────────────────────────

@pytest.fixture
def mock_chroma():
    """MagicMock of ChromaClient with vector_search/get_by_ids."""
    chroma = MagicMock()
    chroma.vector_search = MagicMock(return_value=MOCK_CHUNKS.copy())
    chroma.get_by_ids = MagicMock(return_value=MOCK_CHUNKS.copy())
    chroma.search_by_metadata = MagicMock(return_value=MOCK_CHUNKS.copy())
    return chroma


@pytest.fixture
def mock_embedding():
    """MagicMock of VertexEmbeddingClient."""
    emb = MagicMock()
    emb.embed_query = MagicMock(return_value=[0.1] * 768)
    emb.embed_queries = MagicMock(return_value=[[0.1] * 768, [0.2] * 768])
    return emb


# ── Source-specific chunk fixtures ───────────────────────────

@pytest.fixture
def sample_law_chunks():
    """3 georgian_laws chunks with full metadata."""
    return [
        {
            "chunk_id": f"law_chunk_{i}",
            "content": f"მუხლი {i}. ტესტი კანონის ტექსტი...",
            "metadata": {
                "code_name": "სისხლის სამართლის კოდექსი",
                "article_number": f"მუხლი {i}",
                "article_title": f"ტესტი სათაური {i}",
                "citation_text": f"საქართველოს სისხლის სამართლის კოდექსი, მუხლი {i}",
                "article_url": f"https://matsne.gov.ge/ka/document/view/16426#article_{i}",
                "_collection": "georgian_laws",
            },
            "distance": 0.1 * i,
        }
        for i in range(1, 4)
    ]


@pytest.fixture
def sample_court_chunks():
    """2 court_practice chunks with case_id/category/year."""
    return [
        {
            "chunk_id": f"court_chunk_{i}",
            "content": f"სასამართლო გადაწყვეტილება ტექსტი {i}...",
            "metadata": {
                "case_id": f"ბს-245-{i}(კ-24)",
                "category": "criminal",
                "year": "2023",
                "section": "general",
                "_collection": "court_practice",
            },
            "distance": 0.2 * i,
        }
        for i in range(1, 3)
    ]


@pytest.fixture
def sample_grand_chamber_chunks():
    """1 grand_chamber chunk with binding_rule/norm_interpreted."""
    return [
        {
            "chunk_id": "gc_chunk_1",
            "content": "დიდი პალატის სავალდებულო განმარტება...",
            "metadata": {
                "case_id": "GC-2023-001",
                "category": "criminal",
                "year": "2023",
                "norm_interpreted": "მუხლი 120",
                "binding_rule": "სავალდებულო განმარტება ტექსტი",
                "_collection": "grand_chamber",
            },
            "distance": 0.1,
        }
    ]


@pytest.fixture
def sample_threshold_chunks():
    """Threshold-type chunks with chunk_type metadata."""
    return [
        {
            "chunk_id": "threshold_1",
            "content": "Threshold values for criminal offenses...",
            "metadata": {
                "chunk_type": "threshold",
                "_collection": "georgian_laws",
            },
            "distance": 0.05,
        }
    ]


@pytest.fixture
def sample_history():
    """5-message conversation history [user, assistant, user, ...]."""
    return [
        {"role": "user", "content": "გამარჯობა"},
        {"role": "assistant", "content": "გამარჯობა! რით შემიძლია დაგეხმაროთ?"},
        {"role": "user", "content": "რა სასჯელი ეკისრება ქურდობისთვის?"},
        {"role": "assistant", "content": "ქურდობა განიხილება სისხლის სამართლის კოდექსის..."},
        {"role": "user", "content": "მუხლი 177 რა არის ზუსტად?"},
    ]


# ── Mock ORM objects ─────────────────────────────────────────

def make_mock_conversation(
    conv_id=None,
    user_id=MOCK_USER_UID,
    phase="GREETING",
    title="Test Conversation",
):
    """Create a mock Conversation ORM object."""
    conv = MagicMock()
    conv.id = conv_id or uuid.uuid4()
    conv.user_id = user_id
    conv.phase = phase
    conv.title = title
    conv.legal_domain = ""
    conv.case_ready = False
    conv.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    conv.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return conv


def make_mock_message(
    msg_id=None,
    role="user",
    content="Test message",
    citations=None,
    credit_cost=0,
):
    """Create a mock Message ORM object."""
    msg = MagicMock()
    msg.id = msg_id or uuid.uuid4()
    msg.role = role
    msg.content = content
    msg.citations = citations or []
    msg.credit_cost = credit_cost
    msg.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return msg


# ── The law corpus is not in git, and twelve tests need it ───────────────────
#
# `law_corpus/data/` is 907 MB and `law_corpus/.gitignore` excludes it. A fresh
# clone — CI, a new machine, a rebuilt VPS — therefore has the code but not the
# corpus, and twelve tests below reach for the article store
# (`<chroma>/../georgian_laws/article_store.db`) or for real embeddings. Left
# alone they FAIL there, which teaches everyone to ignore a red suite; the
# information that actually matters is "these need data this checkout does not
# have", and that is a skip.
#
# They are named ONE BY ONE rather than by module on purpose: those three
# modules hold 36 tests and only these 12 need the corpus, so skipping whole
# files would silently drop 24 real assertions from every CI run.
#
# 🔴 A STALE ENTRY FAILS THE RUN — see `_assert_no_rotted_ids`. This is the
# same rule the design guard's allow-list lives under
# (`frontend/.fuzzzy_guard_allow`): a pin that quietly stops matching is worse
# than no pin, because it removes the coverage AND the warning at once.

CORPUS_DEPENDENT_TESTS = frozenset({
    "tests/test_grounding_phase1.py::TestGetArticleExecutor::test_found_returns_full_text_and_url",
    "tests/test_grounding_phase1.py::TestGetArticleExecutor::test_paragraph_selection",
    "tests/test_grounding_phase1.py::TestBrowseCodeExecutor::test_lists_articles",
    "tests/test_grounding_phase1.py::TestBrowseCodeExecutor::test_unknown_code_lists_available",
    "tests/test_grounding_phase1.py::TestFullCodeInjection::test_labor_domain_injects_labour_code",
    "tests/test_grounding_phase1.py::TestFullCodeInjection::test_budget_too_small_skips",
    "tests/test_grounding_phase3.py::TestSubArticleVerification::test_invalid_paragraph_flagged",
    "tests/test_grounding_phase3.py::TestLinkRepair::test_invented_link_repointed_via_store",
    "tests/test_threshold_service.py::TestThresholdServiceSearch::test_search_matches_substance",
    "tests/test_threshold_service.py::TestThresholdDomainGate::test_criminal_entries_gated_out_for_labor_query",
    "tests/test_threshold_service.py::TestThresholdDomainGate::test_matching_domain_entries_kept",
    "tests/test_threshold_service.py::TestThresholdDomainGate::test_secondary_domain_also_allows",
})


def corpus_is_available() -> bool:
    """True when the built article store is on disk.

    The article store is the narrowest honest probe: it is produced by the
    same `law_corpus` build as the Chroma collections and the threshold
    catalog, so if it is missing the corpus was never transferred, and if it
    is present the rest of the build is there too. Probing the Chroma
    directory instead would pass on an EMPTY directory, which is exactly the
    state a half-finished rsync leaves behind.
    """
    from pathlib import Path

    from app.config.settings import settings

    store = Path(settings.chroma_persist_dir).parent / "georgian_laws" / "article_store.db"
    return store.is_file()


def _assert_no_rotted_ids(collected_ids: set[str]) -> None:
    rotted = sorted(CORPUS_DEPENDENT_TESTS - collected_ids)
    if rotted:
        raise pytest.UsageError(
            "CORPUS_DEPENDENT_TESTS in tests/conftest.py names tests that no "
            "longer exist. A renamed test does not warn — it just stops being "
            "skipped and starts failing on every corpus-less machine. Remove "
            "or re-point:\n  " + "\n  ".join(rotted)
        )


def pytest_collection_modifyitems(config, items):
    collected = {item.nodeid for item in items}

    # Only meaningful on a full run: `-k`, `--deselect` or a single-file
    # invocation collects a subset, and every unselected pin would look rotted.
    ran_everything = not config.option.keyword and not config.option.file_or_dir[1:]
    if ran_everything and CORPUS_DEPENDENT_TESTS <= collected | CORPUS_DEPENDENT_TESTS:
        _assert_no_rotted_ids(collected)

    if corpus_is_available():
        return

    skip = pytest.mark.skip(
        reason="needs the law corpus (law_corpus/data/, 907 MB, not in git) — "
               "see LAUNCH.md 'Corpus transfer'"
    )
    for item in items:
        if item.nodeid in CORPUS_DEPENDENT_TESTS:
            item.add_marker(skip)
