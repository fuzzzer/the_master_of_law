"""
Court decision chunker — semantic chunking for court practice and Grand Chamber.

Splits extracted .txt case files into embeddable chunks with rich metadata.
Chunks are delimited by court decision section boundaries (descriptive,
reasoning, resolution) and numbered paragraphs.

Usage:
    from pipeline.court.chunker import CourtChunker

    chunker = CourtChunker(data_dir=Path("data/court_practice/extracted"))
    chunks = chunker.chunk_all(source="court_practice", court="supreme_court")
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.utils.logger import get_logger

logger = get_logger(__name__)


# ── Chunk data model ─────────────────────────────────────────

@dataclass
class CourtChunk:
    """A single chunk of court decision text with metadata."""

    chunk_id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


# ── Section detection ────────────────────────────────────────

SECTION_PATTERNS = {
    "descriptive": re.compile(
        r'აღწერილობითი\s+ნაწილი|აღწერილობითი|ა\s*ღ\s*წ\s*ე\s*რ\s*ი\s*ლ\s*ო\s*ბ\s*ი\s*თ\s*ი',
        re.IGNORECASE,
    ),
    "reasoning": re.compile(
        r'სამოტივაციო\s+ნაწილი|სამოტივაციო|მ\s*ო\s*ტ\s*ი\s*ვ\s*ა\s*ც\s*ი',
        re.IGNORECASE,
    ),
    "resolution": re.compile(
        r'სარეზოლუციო\s+ნაწილი|სარეზოლუციო|რ\s*ე\s*ზ\s*ო\s*ლ\s*უ\s*ც\s*ი',
        re.IGNORECASE,
    ),
}

NUMBERED_SECTION = re.compile(r'^\s*(\d+)\.\s+', re.MULTILINE)


def detect_section(text: str) -> str:
    """Detect which section of a court decision this text belongs to."""
    for section, pattern in SECTION_PATTERNS.items():
        if pattern.search(text[:500]):
            return section
    return "general"


def detect_year(text: str) -> int | None:
    """Extract the year from case text."""
    year_match = re.search(r'20(2[0-6]|1\d|0\d)\s*(წ\.|წელი|წლის)', text[:2000])
    if year_match:
        return int("20" + year_match.group(1))
    year_match = re.search(r'\b(20[012]\d)\b', text[:2000])
    if year_match:
        return int(year_match.group(1))
    return None


def detect_category(file_path: Path) -> str:
    """Detect case category from file path."""
    path_str = str(file_path).lower()
    if "criminal" in path_str or "sisxli" in path_str:
        return "criminal"
    elif "civil" in path_str or "samoq" in path_str:
        return "civil"
    elif "admin" in path_str:
        return "administrative"
    return "unknown"


def extract_norm_interpretation(text: str) -> dict[str, str]:
    """
    For Grand Chamber norm interpretation documents, extract:
    - norm_interpreted: which legal norm was interpreted
    - binding_rule: the established binding interpretation
    """
    result = {}
    norm_match = re.search(
        r'(სსკ|სამოქალაქო\s+კოდექსის?|სპკ|ადმინისტრაციული)\s+(\d+)',
        text[:1000],
    )
    if norm_match:
        result["norm_interpreted"] = norm_match.group(0)

    rule_match = re.search(
        r'(დადგენილია|განმარტება|სავალდებულო\s+ინტერპრეტაცია)[^.]*\.',
        text[:3000],
    )
    if rule_match:
        result["binding_rule"] = rule_match.group(0)[:200]

    return result


# ── Text splitting ───────────────────────────────────────────

def split_text(
    text: str,
    target_words: int = 750,
    max_words: int = 1000,
    overlap_words: int = 50,
) -> list[str]:
    """
    Split text into chunks of target_words with overlap.

    Tries to split at numbered sections (1., 2., 3.) or paragraph
    boundaries.  Falls back to word-count-based splitting.
    """
    if not text.strip():
        return []

    words = text.split()
    total_words = len(words)

    if total_words <= max_words:
        return [text.strip()]

    chunks = []
    start = 0

    while start < total_words:
        end = min(start + max_words, total_words)

        if end < total_words:
            chunk_candidate = " ".join(words[start:end])
            numbered = list(NUMBERED_SECTION.finditer(chunk_candidate))
            if numbered and len(numbered) > 1:
                last = numbered[-1]
                split_pos = len(chunk_candidate[:last.start()].split())
                if split_pos >= target_words // 2:
                    end = start + split_pos

        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap_words if end < total_words else total_words

    return chunks


# ── Chunker class ────────────────────────────────────────────

class CourtChunker:
    """Chunks court decision .txt files into embeddable pieces."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def find_files(self) -> list[Path]:
        """Find all extracted .txt case files."""
        if not self.data_dir.exists():
            logger.warning("Data directory not found: %s", self.data_dir)
            return []
        return sorted(self.data_dir.rglob("*.txt"))

    def chunk_file(
        self,
        file_path: Path,
        source: str,
        court: str,
    ) -> list[CourtChunk]:
        """Chunk a single case file into CourtChunk instances."""
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("Cannot read %s: %s", file_path, e)
            return []

        if not text.strip():
            return []

        case_id = file_path.stem
        category = detect_category(file_path)
        year = detect_year(text)
        section = detect_section(text)

        norm_data = {}
        if source == "grand_chamber":
            norm_data = extract_norm_interpretation(text)

        text_chunks = split_text(text)

        chunks = []
        for idx, chunk_content in enumerate(text_chunks):
            content_hash = hashlib.md5(
                chunk_content.encode("utf-8")
            ).hexdigest()[:8]
            chunk_id = f"{source}:{case_id}:chunk_{idx}:{content_hash}"

            metadata = {
                "source": source,
                "case_id": case_id,
                "category": category,
                "section": section if idx == 0 else detect_section(chunk_content),
                "court": court,
                "chunk_index": idx,
                "total_chunks": len(text_chunks),
                "source_file": file_path.name,
            }
            if year:
                metadata["year"] = year
            if norm_data:
                metadata.update(norm_data)

            chunks.append(CourtChunk(
                chunk_id=chunk_id,
                content=chunk_content,
                metadata=metadata,
            ))

        return chunks

    def chunk_all(self, source: str, court: str) -> list[CourtChunk]:
        """Chunk all case files in the data directory."""
        files = self.find_files()
        if not files:
            return []

        all_chunks: list[CourtChunk] = []
        for f in files:
            all_chunks.extend(self.chunk_file(f, source=source, court=court))

        logger.info(
            "Chunked %d files into %d chunks (source=%s)",
            len(files), len(all_chunks), source,
        )
        return all_chunks
