"""YouTube Transcript Fetcher Plugin Package."""

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
    fetch_transcript,
    get_transcript_text,
    health,
    list_transcripts,
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
    "resolve_youtube_transcript_fetcher",
    "run_jsonrpc_server",
]
