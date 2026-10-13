"""Single-seam IoC resolver for YouTube Transcript Fetcher per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import cast

from harness.kernel.context import ServiceContext

from .service import (
    YOUTUBE_TRANSCRIPT_FETCHER_KEY,
    DefaultYouTubeTranscriptFetcherService,
    YouTubeTranscriptFetcherService,
)

_DEFAULT_SERVICE: YouTubeTranscriptFetcherService | None = None


def get_default_transcript_fetcher_service() -> YouTubeTranscriptFetcherService:
    """Obtain or instantiate the process-level default YouTube transcript fetcher service."""
    global _DEFAULT_SERVICE
    if _DEFAULT_SERVICE is None:
        _DEFAULT_SERVICE = DefaultYouTubeTranscriptFetcherService()
    return _DEFAULT_SERVICE


def resolve_youtube_transcript_fetcher(
    context: ServiceContext | None = None,
) -> YouTubeTranscriptFetcherService:
    """Resolve YouTubeTranscriptFetcherService from ServiceContext or fallback to process default."""
    if context is not None:
        resolved = context.optional(YOUTUBE_TRANSCRIPT_FETCHER_KEY)
        if resolved is not None:
            return cast(YouTubeTranscriptFetcherService, resolved)
    return get_default_transcript_fetcher_service()
