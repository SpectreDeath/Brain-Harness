"""Low-level YouTube Transcript API wrapper and exception hierarchy."""

from __future__ import annotations

import sys
from typing import Any

# Configure UTF-8 streams on Windows environments (AGENTS.md Rule 23)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Attempt importing youtube_transcript_api with resilient fallback
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api import _errors as _yt_errors

    TranscriptsDisabled = getattr(_yt_errors, "TranscriptsDisabled", Exception)
    NoTranscriptFound = getattr(_yt_errors, "NoTranscriptFound", Exception)
    VideoUnavailable = getattr(_yt_errors, "VideoUnavailable", Exception)
    CouldNotRetrieveTranscript = getattr(_yt_errors, "CouldNotRetrieveTranscript", Exception)
    YouTubeRequestFailed = getattr(_yt_errors, "YouTubeRequestFailed", Exception)
    HAS_YOUTUBE_API = True
except ImportError:
    YouTubeTranscriptApi = None  # type: ignore[assignment,misc]
    TranscriptsDisabled = type("TranscriptsDisabled", (Exception,), {})  # type: ignore[misc]
    NoTranscriptFound = type("NoTranscriptFound", (Exception,), {})  # type: ignore[misc]
    VideoUnavailable = type("VideoUnavailable", (Exception,), {})  # type: ignore[misc]
    CouldNotRetrieveTranscript = type("CouldNotRetrieveTranscript", (Exception,), {})  # type: ignore[misc]
    YouTubeRequestFailed = type("YouTubeRequestFailed", (Exception,), {})  # type: ignore[misc]
    HAS_YOUTUBE_API = False


def _get_active_api() -> Any:
    """Retrieve active API class, supporting test mock patching (Rule 39)."""
    main_mod = sys.modules.get("plugins.integration_and_io.youtube_transcript_fetcher.main")
    if main_mod is not None and hasattr(main_mod, "YouTubeTranscriptApi"):
        return getattr(main_mod, "YouTubeTranscriptApi")
    return YouTubeTranscriptApi


def is_api_available() -> bool:
    """Check if YouTubeTranscriptApi is available, supporting mock patching."""
    main_mod = sys.modules.get("plugins.integration_and_io.youtube_transcript_fetcher.main")
    if main_mod is not None and hasattr(main_mod, "HAS_YOUTUBE_API"):
        return bool(getattr(main_mod, "HAS_YOUTUBE_API")) and _get_active_api() is not None
    return HAS_YOUTUBE_API and _get_active_api() is not None


def _get_raw_transcript_data(
    video_id: str,
    languages: list[str],
    preserve_formatting: bool = False,
) -> list[dict[str, Any]]:
    """Helper to retrieve raw transcript items across v0.6+ and v1.2+ API versions (Rule 39)."""
    api_cls = _get_active_api()
    if api_cls is None:
        raise RuntimeError("YouTubeTranscriptApi is not available.")

    # Check for v0.6+ static get_transcript method (or classic mocks)
    if hasattr(api_cls, "get_transcript"):
        return list(
            api_cls.get_transcript(
                video_id,
                languages=languages,
                preserve_formatting=preserve_formatting,
            )
        )

    # Check for v1.2+ instance API (fetch method)
    if hasattr(api_cls, "fetch"):
        client = api_cls() if callable(api_cls) else api_cls
        fetched = client.fetch(
            video_id,
            languages=languages,
            preserve_formatting=preserve_formatting,
        )
        if hasattr(fetched, "to_raw_data"):
            return list(fetched.to_raw_data())
        return [
            {
                "text": getattr(s, "text", ""),
                "start": getattr(s, "start", 0.0),
                "duration": getattr(s, "duration", 0.0),
            }
            for s in fetched
        ]

    raise RuntimeError("YouTubeTranscriptApi does not support fetch or get_transcript.")


def _get_transcript_list(video_id: str) -> Any:
    """Helper to retrieve TranscriptList across v0.6+ and v1.2+ API versions (Rule 39)."""
    api_cls = _get_active_api()
    if api_cls is None:
        raise RuntimeError("YouTubeTranscriptApi is not available.")
    if hasattr(api_cls, "list_transcripts"):
        return api_cls.list_transcripts(video_id)
    if hasattr(api_cls, "list"):
        client = api_cls() if callable(api_cls) else api_cls
        return client.list(video_id)
    raise RuntimeError("YouTubeTranscriptApi does not support list or list_transcripts.")
