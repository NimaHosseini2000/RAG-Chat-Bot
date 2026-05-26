"""
Word-based sliding-window text chunker with configurable overlap.

Splits text on whitespace and groups tokens into chunks of `size` words,
carrying `overlap` words forward into the next chunk.  The overlap preserves
cross-sentence context at chunk boundaries and improves retrieval recall.
"""

from __future__ import annotations

from typing import List

from app.config import settings


def chunk_text(
    text: str,
    size: int | None = None,
    overlap: int | None = None,
) -> List[str]:
    """Split *text* into overlapping word-window chunks.

    Args:
        text:    The input string to chunk.
        size:    Words per chunk (defaults to settings.CHUNK_SIZE = 200).
        overlap: Words shared between consecutive chunks
                 (defaults to settings.CHUNK_OVERLAP = 30).

    Returns:
        A list of non-empty chunk strings.
    """
    size = size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    if overlap >= size:
        raise ValueError(f"overlap ({overlap}) must be less than size ({size})")

    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start : start + size])
        if chunk.strip():
            chunks.append(chunk.strip())
        if start + size >= len(words):
            break
        start += size - overlap  # slide forward, keeping `overlap` words in common

    return chunks
