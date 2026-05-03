"""
Chunk quality and completeness validation.
"""

from __future__ import annotations

from pipeline.models.legal_chunk import LegalChunk
from pipeline.utils.georgian_text import contains_georgian
from pipeline.utils.logger import get_logger

logger = get_logger(__name__)

MIN_CHUNK_CHARS = 20
MAX_CHUNK_CHARS = 15_000


def validate_chunk(chunk: LegalChunk) -> list[str]:
    """
    Return a list of warning messages for *chunk*.
    An empty list means the chunk is valid.
    """
    warnings: list[str] = []

    if len(chunk.content) < MIN_CHUNK_CHARS:
        warnings.append(f"Chunk too short ({len(chunk.content)} chars)")

    if len(chunk.content) > MAX_CHUNK_CHARS:
        warnings.append(f"Chunk too long ({len(chunk.content)} chars)")

    if not contains_georgian(chunk.content_ka):
        warnings.append("Chunk content_ka contains no Georgian characters")

    if chunk.token_count <= 0:
        warnings.append("Token count not set")

    if not chunk.article_number:
        warnings.append("Missing article_number")

    return warnings


def validate_chunks(chunks: list[LegalChunk]) -> dict[str, list[str]]:
    """Validate all chunks and return a mapping of chunk_id → warnings."""
    issues: dict[str, list[str]] = {}
    for chunk in chunks:
        w = validate_chunk(chunk)
        if w:
            issues[chunk.chunk_id] = w
            for msg in w:
                logger.warning("Chunk %s: %s", chunk.chunk_id, msg)
    return issues
