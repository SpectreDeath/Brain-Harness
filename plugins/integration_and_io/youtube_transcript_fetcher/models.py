"""Slotted domain models for YouTube transcript segments and tracks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CaptionSegment:
    """Timed caption segment in a video transcript."""

    text: str
    start: float
    duration: float


@dataclass(slots=True)
class TranscriptTrack:
    """Metadata describing an available transcript track for a YouTube video."""

    language: str
    language_code: str
    is_generated: bool = False
    is_translatable: bool = False


@dataclass(slots=True)
class TranscriptResult:
    """Structured response from a transcript fetch operation."""

    status: str
    video_id: str
    format: str = "json"
    captions_available: bool = True
    segment_count: int = 0
    transcript: list[dict[str, Any]] = field(default_factory=list)
    raw_text: str = ""
    error: str | None = None
    error_code: str | None = None
