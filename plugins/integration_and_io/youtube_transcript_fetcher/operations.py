"""Facade exposing core transcript fetch, listing, and health operations."""

from __future__ import annotations

from .fetch import (
    fetch_transcript,
    get_transcript_text,
)
from .tracks import (
    health,
    list_transcripts,
)

__all__ = [
    "fetch_transcript",
    "get_transcript_text",
    "health",
    "list_transcripts",
]
