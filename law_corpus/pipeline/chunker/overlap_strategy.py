"""
Chunk overlap configuration.

Defines how adjacent chunks within the same chapter should overlap
to preserve context across chunk boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OverlapStrategy:
    """Overlap configuration for legal chunking."""

    ratio: float = 0.12         # 10-15% overlap between adjacent chunks
    min_overlap_chars: int = 80
    max_overlap_chars: int = 500
    include_prev_article_header: bool = True  # prepend previous article number/title

    def compute_overlap(self, text_length: int) -> int:
        """Return the number of characters to overlap."""
        overlap = int(text_length * self.ratio)
        return max(self.min_overlap_chars, min(overlap, self.max_overlap_chars))
