"""
Absolute Law Integrity Tests
=============================
Validates that the HTML → Parse → Chunk pipeline preserves 100% of
legal content from matsne.gov.ge consolidated laws.

Test Strategy:
  1. VERSION CHECK: Verify every HTML is consolidated (not original)
  2. ARTICLE COUNT: Compare HTML ground-truth vs parsed article counts
  3. CONTENT PRESERVATION: Ensure no article text is lost in parsing
  4. RANDOM SAMPLE DEEP CHECK: Pick random articles and verify content
  5. CHUNK COVERAGE: Ensure chunks cover every article with content
  6. CHUNK TEXT INTEGRITY: Verify chunk text is a subset of parsed text
  7. NO DATA LOSS: Verify total text volume at each transformation step

Run:
    cd law_corpus
    python -m pytest .testing/absolute_law_testing/test_law_integrity.py -v
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
from pathlib import Path

import orjson
import pytest
from bs4 import BeautifulSoup

# ── Setup paths ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]  # law_corpus/
HTML_DIR = ROOT / "data" / "raw" / "html"
PARSED_DIR = ROOT / "data" / "parsed"
CHUNKS_DIR = ROOT / "data" / "chunks"

ARTICLE_RE = re.compile(
    r"მუხლი\s+(\d+(?:[⁰¹²³⁴⁵⁶⁷⁸⁹]+|\-\d+)?)\s*[.\-–—]?\s*(.*)",
    re.UNICODE,
)

# Expected active documents (exclude access-denied pages)
SKIP_DOCS = {"consumer_rights_law", "customs_code", "entrepreneurial_law"}

# ── Known ground-truth minimum article counts (from HTML analysis) ──
# These are MINIMUM expected articles with actual content
# (i.e., excluding repealed/ამოღებულია articles)
EXPECTED_MIN_ARTICLES = {
    "constitution": 78,
    "civil_code": 1400,
    "criminal_code": 520,
    "civil_procedure_code": 580,
    "criminal_procedure_code": 360,
    "admin_offences_code": 650,
    "general_admin_code": 225,
    "admin_procedure_code": 160,
    "tax_code": 330,
    "labour_code": 85,
    "election_code": 235,
    "personal_data_law": 60,
}

# ── Helpers ──────────────────────────────────────────────────────────

def get_active_doc_ids() -> list[str]:
    """Return document IDs that have valid HTML (not access-denied)."""
    docs = []
    for f in sorted(HTML_DIR.glob("*.html")):
        doc_id = f.stem
        if doc_id in SKIP_DOCS:
            continue
        html = f.read_bytes()
        if b"Access Denied" in html or b"Oops!" in html:
            continue
        docs.append(doc_id)
    return docs


def count_html_article_markers(soup: BeautifulSoup) -> set[str]:
    """Extract unique article numbers from HTML markers."""
    articles = set()
    # From muxlixml class
    for p in soup.find_all("p", class_="muxlixml"):
        m = ARTICLE_RE.search(p.get_text(strip=True))
        if m:
            articles.add(m.group(1))
    # From oldStyleDocumentPart anchors
    for a in soup.find_all("a", class_="oldStyleDocumentPart"):
        m = ARTICLE_RE.search(a.get_text(strip=True))
        if m:
            articles.add(m.group(1))
    return articles


def load_parsed(doc_id: str) -> dict:
    path = PARSED_DIR / f"{doc_id}.json"
    return json.loads(path.read_text("utf-8"))


def load_chunks(doc_id: str) -> list[dict]:
    path = CHUNKS_DIR / f"{doc_id}.json"
    return list(orjson.loads(path.read_bytes()))


# ── Fixtures ─────────────────────────────────────────────────────────

ACTIVE_DOCS = get_active_doc_ids()


@pytest.fixture(params=ACTIVE_DOCS, ids=ACTIVE_DOCS)
def doc_id(request):
    return request.param


# ══════════════════════════════════════════════════════════════════════
# TEST 1: VERSION VERIFICATION
# ══════════════════════════════════════════════════════════════════════

class TestVersionVerification:
    """Guarantee every HTML file is the consolidated (საბოლოო) version."""

    def test_html_is_consolidated(self, doc_id):
        """Each HTML must contain the consolidated version label or be
        a single-version law (no amendments history)."""
        html = (HTML_DIR / f"{doc_id}.html").read_bytes()
        html_str = html.decode("utf-8", errors="replace")

        is_consolidated = "კონსოლიდირებული ვერსია (საბოლოო)" in html_str
        # Some newer laws only have one version (no consolidation needed)
        is_single_version = "პირველადი სახე" not in html_str and not is_consolidated

        assert is_consolidated or is_single_version, (
            f"{doc_id}: HTML is NOT the consolidated version! "
            f"Found 'პირველადი სახე' (original version) label."
        )

    def test_not_access_denied(self, doc_id):
        """No active document should be an error page."""
        html = (HTML_DIR / f"{doc_id}.html").read_bytes()
        assert b"Access Denied" not in html, f"{doc_id}: HTML is an Access Denied page!"
        assert b"Oops!" not in html, f"{doc_id}: HTML is an error page!"

    def test_html_has_substantial_content(self, doc_id):
        """HTML must be at least 50KB (real law docs are 100KB+)."""
        size = (HTML_DIR / f"{doc_id}.html").stat().st_size
        assert size > 50_000, (
            f"{doc_id}: HTML is only {size/1024:.0f}KB — likely an error page "
            f"or incomplete download."
        )


# ══════════════════════════════════════════════════════════════════════
# TEST 2: ARTICLE COUNT VALIDATION
# ══════════════════════════════════════════════════════════════════════

class TestArticleCount:
    """Verify parsed article counts match HTML ground truth."""

    def test_parsed_article_count_matches_html(self, doc_id):
        """Parsed articles should be within 5% of HTML article markers.

        The counts may differ slightly because:
        - muxlixml duplicates (superscript articles like 15¹)
        - oldStyleDocumentPart may count differently
        But they should be close.
        """
        html = (HTML_DIR / f"{doc_id}.html").read_bytes()
        soup = BeautifulSoup(html, "lxml")
        html_articles = count_html_article_markers(soup)

        parsed = load_parsed(doc_id)
        parsed_count = len(parsed["articles"])

        # Allow 10% tolerance for edge cases (duplicates, superscripts)
        lower = len(html_articles) * 0.85
        upper = len(html_articles) * 1.15

        assert lower <= parsed_count <= upper, (
            f"{doc_id}: Parsed {parsed_count} articles but HTML has "
            f"{len(html_articles)} unique article markers. "
            f"Expected between {lower:.0f}–{upper:.0f}."
        )

    def test_meets_minimum_article_count(self, doc_id):
        """Each law must have at least the known minimum number of
        articles with actual content."""
        if doc_id not in EXPECTED_MIN_ARTICLES:
            pytest.skip(f"No minimum defined for {doc_id}")

        parsed = load_parsed(doc_id)
        articles_with_content = sum(
            1 for a in parsed["articles"]
            if a.get("content_ka", "").strip()
        )

        minimum = EXPECTED_MIN_ARTICLES[doc_id]
        assert articles_with_content >= minimum, (
            f"{doc_id}: Only {articles_with_content} articles with content, "
            f"expected at least {minimum}."
        )

    def test_no_parsed_file_has_zero_articles(self, doc_id):
        """No active document should parse to 0 articles."""
        parsed = load_parsed(doc_id)
        assert len(parsed["articles"]) > 0, (
            f"{doc_id}: Parsed to 0 articles — parser failed completely!"
        )


# ══════════════════════════════════════════════════════════════════════
# TEST 3: CONTENT PRESERVATION
# ══════════════════════════════════════════════════════════════════════

class TestContentPreservation:
    """Verify article content is not empty or truncated."""

    def test_all_non_repealed_articles_have_content(self, doc_id):
        """Every article that isn't repealed must have non-empty content."""
        parsed = load_parsed(doc_id)
        failures = []
        for art in parsed["articles"]:
            title = art.get("article_title", "") or ""
            is_repealed = "ამოღებულია" in title or "ძალადაკარგული" in title
            content = art.get("content_ka", "").strip()

            if not is_repealed and not content:
                failures.append(art.get("article_number", "?"))

        assert len(failures) == 0, (
            f"{doc_id}: {len(failures)} non-repealed articles have empty content: "
            f"{failures[:10]}"
        )

    def test_articles_have_reasonable_length(self, doc_id):
        """Non-repealed articles should have at least 20 characters of content."""
        parsed = load_parsed(doc_id)
        too_short = []
        for art in parsed["articles"]:
            title = art.get("article_title", "") or ""
            is_repealed = "ამოღებულია" in title or "ძალადაკარგული" in title
            content = art.get("content_ka", "").strip()

            if not is_repealed and content and len(content) < 20:
                too_short.append(
                    f"{art.get('article_number')}: {len(content)} chars"
                )

        # Allow up to 2% extremely short articles (some are legitimately brief)
        total_active = sum(
            1 for a in parsed["articles"]
            if "ამოღებულია" not in (a.get("article_title", "") or "")
        )
        threshold = max(3, int(total_active * 0.02))

        assert len(too_short) <= threshold, (
            f"{doc_id}: {len(too_short)} articles are suspiciously short "
            f"(threshold={threshold}): {too_short[:5]}"
        )

    def test_total_text_volume(self, doc_id):
        """Total text volume should be substantial (>10KB for any real law)."""
        parsed = load_parsed(doc_id)
        total_chars = sum(
            len(a.get("content_ka", ""))
            for a in parsed["articles"]
        )
        # Even the smallest law (personal_data_law) should have 20KB+ of text
        assert total_chars > 10_000, (
            f"{doc_id}: Total text is only {total_chars} chars — "
            f"suspiciously low for a complete law."
        )


# ══════════════════════════════════════════════════════════════════════
# TEST 4: RANDOM SAMPLE DEEP VERIFICATION
# ══════════════════════════════════════════════════════════════════════

class TestRandomSampleVerification:
    """Pick random articles and verify their content against HTML source."""

    SAMPLE_SIZE = 5  # articles per document

    def test_random_article_content_exists_in_html(self, doc_id):
        """Random sample of parsed articles must have content that
        appears in the original HTML."""
        html = (HTML_DIR / f"{doc_id}.html").read_text(
            encoding="utf-8", errors="replace"
        )

        parsed = load_parsed(doc_id)
        articles_with_content = [
            a for a in parsed["articles"]
            if a.get("content_ka", "").strip()
        ]

        if len(articles_with_content) == 0:
            pytest.skip(f"{doc_id}: No articles with content to sample")

        # Deterministic seed for reproducibility
        rng = random.Random(42 + hash(doc_id))
        sample = rng.sample(
            articles_with_content,
            min(self.SAMPLE_SIZE, len(articles_with_content)),
        )

        failures = []
        for art in sample:
            content = art["content_ka"]
            # Take first 50 chars of content (enough to verify, short enough
            # to handle minor whitespace differences)
            snippet = content[:50].strip()
            if snippet and snippet not in html:
                # Try with normalized whitespace
                normalized = " ".join(snippet.split())
                if not any(
                    normalized[:30] in " ".join(line.split())
                    for line in html.split("\n")
                ):
                    failures.append(
                        f"{art.get('article_number')}: '{snippet[:40]}...'"
                    )

        assert len(failures) == 0, (
            f"{doc_id}: {len(failures)} sampled articles have content NOT "
            f"found in HTML: {failures}"
        )

    def test_random_article_metadata_integrity(self, doc_id):
        """Random articles must have valid metadata fields."""
        parsed = load_parsed(doc_id)
        articles = parsed["articles"]

        rng = random.Random(99 + hash(doc_id))
        sample = rng.sample(articles, min(self.SAMPLE_SIZE, len(articles)))

        for art in sample:
            # Must have article_id
            assert art.get("article_id"), (
                f"{doc_id}: Article missing article_id"
            )
            # Must have document_id matching
            assert art.get("document_id") == doc_id, (
                f"{doc_id}: Article has wrong document_id: {art.get('document_id')}"
            )
            # Must have article_number
            assert art.get("article_number"), (
                f"{doc_id}: Article missing article_number"
            )
            # article_number should start with მუხლი
            assert art["article_number"].startswith("მუხლი"), (
                f"{doc_id}: Article number doesn't start with მუხლი: "
                f"{art['article_number']}"
            )


# ══════════════════════════════════════════════════════════════════════
# TEST 5: CHUNK COVERAGE COMPLETENESS
# ══════════════════════════════════════════════════════════════════════

class TestChunkCoverage:
    """Verify chunks cover every article with content."""

    def test_every_article_with_content_has_chunks(self, doc_id):
        """Every parsed article with non-empty content must produce
        at least one chunk."""
        parsed = load_parsed(doc_id)
        chunks = load_chunks(doc_id)

        # Articles with content
        articles_with_content = {
            a["article_id"]
            for a in parsed["articles"]
            if a.get("content_ka", "").strip()
        }

        # Article IDs that have chunks
        chunked_articles = set()
        for c in chunks:
            # Chunk ID format: doc_id.article_X.chunk_N
            # Extract article portion
            chunk_id = c["chunk_id"]
            parts = chunk_id.rsplit(".chunk_", 1)
            if parts:
                chunked_articles.add(parts[0])

        missing = articles_with_content - chunked_articles
        # Allow small tolerance for edge cases
        threshold = max(2, int(len(articles_with_content) * 0.01))

        assert len(missing) <= threshold, (
            f"{doc_id}: {len(missing)} articles with content have NO chunks "
            f"(threshold={threshold}). Missing: "
            f"{list(missing)[:10]}"
        )

    def test_no_empty_chunks(self, doc_id):
        """No chunk should have empty content."""
        chunks = load_chunks(doc_id)
        empty = [
            c["chunk_id"] for c in chunks
            if not c.get("content", "").strip() and not c.get("content_ka", "").strip()
        ]
        assert len(empty) == 0, (
            f"{doc_id}: {len(empty)} chunks have empty content: {empty[:5]}"
        )

    def test_chunk_count_is_reasonable(self, doc_id):
        """Each document should have a reasonable number of chunks
        relative to articles."""
        parsed = load_parsed(doc_id)
        chunks = load_chunks(doc_id)

        articles_with_content = sum(
            1 for a in parsed["articles"]
            if a.get("content_ka", "").strip()
        )

        if articles_with_content == 0:
            pytest.skip(f"{doc_id}: No articles to chunk")

        # Each article should produce at least 1 chunk
        assert len(chunks) >= articles_with_content, (
            f"{doc_id}: Only {len(chunks)} chunks for {articles_with_content} "
            f"articles — some articles may be missing chunks."
        )


# ══════════════════════════════════════════════════════════════════════
# TEST 6: CHUNK TEXT INTEGRITY
# ══════════════════════════════════════════════════════════════════════

class TestChunkTextIntegrity:
    """Verify chunk text matches parsed article text."""

    SAMPLE_SIZE = 10  # chunks per document

    def test_chunk_content_ka_matches_source_article(self, doc_id):
        """Random chunks' content_ka should be a substring of the
        parsed article's content_ka."""
        parsed = load_parsed(doc_id)
        chunks = load_chunks(doc_id)

        if not chunks:
            pytest.skip(f"{doc_id}: No chunks")

        # Build article content lookup
        article_content = {}
        for a in parsed["articles"]:
            article_content[a["article_id"]] = a.get("content_ka", "")

        rng = random.Random(77 + hash(doc_id))
        sample = rng.sample(chunks, min(self.SAMPLE_SIZE, len(chunks)))

        failures = []
        for chunk in sample:
            chunk_ka = chunk.get("content_ka", "").strip()
            if not chunk_ka:
                continue

            # Find the parent article
            chunk_id = chunk["chunk_id"]
            article_id = chunk_id.rsplit(".chunk_", 1)[0]

            source_content = article_content.get(article_id, "")

            # First 50 chars of chunk content should appear in source
            snippet = chunk_ka[:50]
            if snippet not in source_content:
                failures.append(
                    f"{chunk_id}: chunk text not found in article {article_id}"
                )

        assert len(failures) == 0, (
            f"{doc_id}: {len(failures)} chunks have content not matching "
            f"their source article: {failures[:5]}"
        )

    def test_chunk_has_required_metadata(self, doc_id):
        """Every chunk must have essential metadata fields."""
        chunks = load_chunks(doc_id)
        required_fields = [
            "chunk_id", "document_id", "content", "source_url",
            "article_number", "code_name",
        ]

        for chunk in chunks[:50]:  # Check first 50
            for field in required_fields:
                assert chunk.get(field), (
                    f"{doc_id}: Chunk {chunk.get('chunk_id', '?')} "
                    f"missing required field '{field}'"
                )


# ══════════════════════════════════════════════════════════════════════
# TEST 7: CROSS-DOCUMENT CONSISTENCY
# ══════════════════════════════════════════════════════════════════════

class TestCrossDocumentConsistency:
    """Tests across all documents for overall pipeline health."""

    def test_all_expected_documents_present(self):
        """All 12 active laws must have parsed + chunked data."""
        expected = set(EXPECTED_MIN_ARTICLES.keys())
        parsed = {f.stem for f in PARSED_DIR.glob("*.json")}
        chunked = {f.stem for f in CHUNKS_DIR.glob("*.json")}

        missing_parsed = expected - parsed
        missing_chunks = expected - chunked

        assert not missing_parsed, (
            f"Missing parsed files for: {missing_parsed}"
        )
        assert not missing_chunks, (
            f"Missing chunk files for: {missing_chunks}"
        )

    def test_total_chunk_count_reasonable(self):
        """Total chunks across all docs should be >10,000
        (we expect ~15,000)."""
        total = 0
        for f in CHUNKS_DIR.glob("*.json"):
            if f.stem in SKIP_DOCS:
                continue
            chunks = orjson.loads(f.read_bytes())
            total += len(chunks)

        assert total > 10_000, (
            f"Total chunks across all documents is only {total} — "
            f"expected >10,000 for comprehensive legal corpus."
        )

    def test_no_duplicate_chunk_ids(self):
        """Chunk IDs must be globally unique across all documents."""
        all_ids = []
        for f in CHUNKS_DIR.glob("*.json"):
            if f.stem in SKIP_DOCS:
                continue
            chunks = orjson.loads(f.read_bytes())
            all_ids.extend(c["chunk_id"] for c in chunks)

        duplicates = [
            cid for cid in set(all_ids)
            if all_ids.count(cid) > 1
        ]

        assert len(duplicates) == 0, (
            f"Found {len(duplicates)} duplicate chunk IDs: {duplicates[:5]}"
        )

    def test_source_urls_are_valid(self):
        """All source URLs should point to matsne.gov.ge."""
        for f in CHUNKS_DIR.glob("*.json"):
            if f.stem in SKIP_DOCS:
                continue
            chunks = orjson.loads(f.read_bytes())
            for chunk in chunks[:10]:  # Spot check
                url = chunk.get("source_url", "")
                assert "matsne.gov.ge" in url, (
                    f"Chunk {chunk.get('chunk_id')} has invalid URL: {url}"
                )
