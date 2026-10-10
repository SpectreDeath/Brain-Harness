"""Tokenization and textual keyword extraction utilities for skill clustering."""

from __future__ import annotations

import re

STOPWORDS: frozenset[str] = frozenset({
    "and", "the", "for", "with", "from", "using", "that", "this", "into",
    "across", "not", "use", "when", "what", "which", "are", "you", "user",
    "will", "can", "how", "all", "each", "have", "more", "such", "than",
})


def tokenize(text: str) -> set[str]:
    """Tokenize string into normalized keyword set, filtering common English stopwords."""
    return {
        w.lower()
        for w in re.findall(r"[a-zA-Z]{3,}", text)
        if w.lower() not in STOPWORDS
    }
