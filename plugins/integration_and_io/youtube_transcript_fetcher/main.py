"""Native YouTube Transcript Fetcher plugin for Brain-Harness.

Operates within an isolated subprocess sandbox, communicating via line-buffered
JSON-RPC 2.0 over standard I/O streams (stdin/stdout). Extracts transcripts,
timed caption segments, and dialogue from YouTube video URLs or 11-character IDs
using youtube-transcript-api.
"""

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

from .api import (
    HAS_YOUTUBE_API,
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeRequestFailed,
    YouTubeTranscriptApi,
)
from .extractor import (
    BARE_ID_REGEX,
    YOUTUBE_ID_REGEX,
    extract_video_id,
)
from .models import (
    CaptionSegment,
    TranscriptResult,
    TranscriptTrack,
)
from .operations import (
    fetch_transcript as _ops_fetch_transcript,
    get_transcript_text as _ops_get_transcript_text,
    health as _ops_health,
    list_transcripts as _ops_list_transcripts,
)
from .resolvers import (
    get_default_transcript_fetcher_service,
    resolve_youtube_transcript_fetcher,
)
from .rpc import (
    RPC_METHODS,
    handle_rpc_request,
    run_jsonrpc_server,
)
from .service import (
    YOUTUBE_TRANSCRIPT_FETCHER_KEY,
    DefaultYouTubeTranscriptFetcherService,
    YouTubeTranscriptFetcherPlugin,
    YouTubeTranscriptFetcherService,
)


def fetch_transcript(
    video_url: str = "",
    video_id: str = "",
    languages: list[str] | None = None,
    format: str = "json",
    preserve_formatting: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Extract transcript or timed captions from a YouTube video."""
    return _ops_fetch_transcript(
        video_url=video_url,
        video_id=video_id,
        languages=languages,
        format=format,
        preserve_formatting=preserve_formatting,
        **kwargs,
    )


def get_transcript_text(
    video_url: str = "",
    video_id: str = "",
    languages: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Extract plain text transcript without timestamp metadata."""
    return _ops_get_transcript_text(
        video_url=video_url,
        video_id=video_id,
        languages=languages,
        **kwargs,
    )


def list_transcripts(
    video_url: str = "",
    video_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """List all available transcripts, languages, and translation tracks for a video."""
    return _ops_list_transcripts(
        video_url=video_url,
        video_id=video_id,
        **kwargs,
    )


def health() -> dict[str, Any]:
    """Check runtime health and dependencies of the YouTube transcript fetcher plugin."""
    return _ops_health()


plugin = YouTubeTranscriptFetcherPlugin()

__all__ = [
    "BARE_ID_REGEX",
    "CaptionSegment",
    "CouldNotRetrieveTranscript",
    "DefaultYouTubeTranscriptFetcherService",
    "HAS_YOUTUBE_API",
    "NoTranscriptFound",
    "RPC_METHODS",
    "TranscriptResult",
    "TranscriptTrack",
    "TranscriptsDisabled",
    "VideoUnavailable",
    "YOUTUBE_ID_REGEX",
    "YOUTUBE_TRANSCRIPT_FETCHER_KEY",
    "YouTubeRequestFailed",
    "YouTubeTranscriptApi",
    "YouTubeTranscriptFetcherPlugin",
    "YouTubeTranscriptFetcherService",
    "extract_video_id",
    "fetch_transcript",
    "get_default_transcript_fetcher_service",
    "get_transcript_text",
    "handle_rpc_request",
    "health",
    "list_transcripts",
    "plugin",
    "resolve_youtube_transcript_fetcher",
    "run_jsonrpc_server",
]

if __name__ == "__main__":
    run_jsonrpc_server()
