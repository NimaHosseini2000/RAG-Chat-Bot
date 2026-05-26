"""
Persian/Farsi text normalizer.

Performs the following cleaning steps in order:
  1. Unicode NFC normalization
  2. Strip Arabic diacritics (harakat / tashkil)
  3. Remove emoji and symbol ranges
  4. Map Arabic look-alike characters to their Persian equivalents
  5. Collapse duplicate zero-width non-joiners (ZWNJ)
  6. Collapse runs of whitespace and excess blank lines
"""

from __future__ import annotations

import re
import unicodedata

# Arabic → Persian character substitution table
_CHAR_MAP = str.maketrans({
    "ك": "ک",   # Arabic kaf → Persian kaf
    "ي": "ی",   # Arabic ya → Persian ya
    "ى": "ی",   # Arabic alef maqsura → Persian ya
    "ة": "ه",   # Arabic ta marbuta → Persian he
    "أ": "ا",   # Arabic alef with hamza above → alef
    "إ": "ا",   # Arabic alef with hamza below → alef
    "‍": "",   # zero-width joiner
    "‎": "",   # left-to-right mark
    "‏": "",   # right-to-left mark
    "﻿": "",   # BOM
})

_DIACRITICS_RE = re.compile(
    r"[ؐ-ؚ"
    r"ً-ٟ"
    r"ٰ"
    r"ۖ-ۜ"
    r"۟-ۤ"
    r"ۧۨ"
    r"۪-ۭ]"
)

_EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001F9FF"
    r"\U00002600-\U000027BF"
    r"\U0000FE00-\U0000FE0F"
    r"\U000024C2-\U0001F251]+"
)

_MULTI_ZWNJ  = re.compile(r"‌{2,}")  # duplicate ZWNJs
_MULTI_SPACE = re.compile(r"[ \t ​]+")  # runs of whitespace
_MULTI_NL    = re.compile(r"\n{3,}")              # more than two consecutive newlines


def normalize_persian(text: str) -> str:
    """Return a cleaned, normalized version of a Persian/Farsi string."""
    if not isinstance(text, str) or not text.strip():
        return ""

    text = unicodedata.normalize("NFC", text)
    text = _DIACRITICS_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    text = text.translate(_CHAR_MAP)
    text = _MULTI_ZWNJ.sub("‌", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_NL.sub("\n\n", text)
    return text.strip()
