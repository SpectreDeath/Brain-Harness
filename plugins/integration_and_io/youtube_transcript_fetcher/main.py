"""Native YouTube Transcript Fetcher plugin for Brain-Harness.

Operates within an isolated subprocess sandbox, communicating via line-buffered
JSON-RPC 2.0 over standard I/O streams (stdin/stdout). Extracts transcripts,
timed caption segments, and dialogue from YouTube video URLs or 11-character IDs
using youtube-transcript-api.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from typing import Any, TextIO

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

# Regex patterns for identifying 11-character YouTube video IDs
YOUTUBE_ID_REGEX = re.compile(
    r"(?:v=|\/|youtu\.be\/|embed\/|shorts\/|live\/|e\/)([a-zA-Z0-9_-]{11})(?:[?&/]|$)"
)
BARE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def extract_video_id(url_or_id: str) -> str:
    """Extract an 11-character YouTube video ID from a URL or raw ID string.

    Supports:
        - Raw ID: 'dQw4w9WgXcQ'
        - Watch URL: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        - Shortened URL: 'https://youtu.be/dQw4w9WgXcQ'
        - Embed URL: 'https://www.youtube.com/embed/dQw4w9WgXcQ'
        - Shorts URL: 'https://www.youtube.com/shorts/dQw4w9WgXcQ'
        - Live URL: 'https://www.youtube.com/live/dQw4w9WgXcQ'

    Args:
        url_or_id: YouTube URL or 11-character video ID.

    Returns:
        Canonical 11-character video ID string.

    Raises:
        ValueError: If unable to parse or find a valid 11-character video ID.
    """
    cleaned = (url_or_id or "").strip()
    if not cleaned:
        raise ValueError("Video URL or ID cannot be empty.")

    # 1. Direct 11-character ID check
    if BARE_ID_REGEX.match(cleaned):
        return cleaned

    # 2. Regex match against known path patterns
    match = YOUTUBE_ID_REGEX.search(cleaned)
    if match:
        return match.group(1)

    # 3. Query parameter extraction via urlparse fallback
    try:
        parsed = urllib.parse.urlparse(cleaned)
        query_params = urllib.parse.parse_qs(parsed.query)
        if "v" in query_params and query_params["v"]:
            vid = query_params["v"][0].strip()
            if BARE_ID_REGEX.match(vid):
                return vid
    except Exception:
        pass

    raise ValueError(f"Invalid YouTube URL or video ID format: '{url_or_id}'")


def _get_raw_transcript_data(
    video_id: str,
    languages: list[str],
    preserve_formatting: bool = False,
) -> list[dict[str, Any]]:
    """Helper to retrieve raw transcript items across v0.6+ and v1.2+ API versions."""
    api_cls = YouTubeTranscriptApi

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
    """Helper to retrieve TranscriptList across v0.6+ and v1.2+ API versions."""
    api_cls = YouTubeTranscriptApi
    if hasattr(api_cls, "list_transcripts"):
        return api_cls.list_transcripts(video_id)
    if hasattr(api_cls, "list"):
        client = api_cls() if callable(api_cls) else api_cls
        return client.list(video_id)
    raise RuntimeError("YouTubeTranscriptApi does not support list or list_transcripts.")


def fetch_transcript(
    video_url: str = "",
    video_id: str = "",
    languages: list[str] | None = None,
    format: str = "json",
    preserve_formatting: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Extract transcript or timed captions from a YouTube video.

    Args:
        video_url: Target YouTube video URL.
        video_id: Optional 11-character video ID (takes precedence if provided).
        languages: Preferred language codes ordered by priority (e.g. ['en', 'es']).
        format: Output format: 'json' (timed segments list) or 'text' (concatenated string).
        preserve_formatting: Whether to preserve HTML formatting in caption segments.

    Returns:
        Structured response dictionary with transcript content or categorized error.
    """
    target_input = video_id or video_url or kwargs.get("url") or kwargs.get("id") or ""
    try:
        target_id = extract_video_id(target_input)
    except ValueError as val_err:
        return {
            "status": "error",
            "error": str(val_err),
            "error_code": "INVALID_INPUT",
            "captions_available": False,
        }

    if not HAS_YOUTUBE_API or YouTubeTranscriptApi is None:
        return {
            "status": "error",
            "error": "youtube-transcript-api package is not installed in current environment.",
            "error_code": "DEPENDENCY_MISSING",
            "video_id": target_id,
            "captions_available": False,
        }

    requested_langs = languages if languages else ["en"]

    try:
        raw_transcript = _get_raw_transcript_data(
            target_id,
            languages=requested_langs,
            preserve_formatting=preserve_formatting,
        )

        raw_text = " ".join(seg.get("text", "") for seg in raw_transcript).strip()

        if format.lower() == "text":
            return {
                "status": "ok",
                "video_id": target_id,
                "format": "text",
                "captions_available": True,
                "segment_count": len(raw_transcript),
                "transcript_text": raw_text,
                "raw_text": raw_text,
            }

        # Default 'json' format with timed segments
        return {
            "status": "ok",
            "video_id": target_id,
            "format": "json",
            "captions_available": True,
            "segment_count": len(raw_transcript),
            "transcript": raw_transcript,
            "raw_text": raw_text,
        }

    except TranscriptsDisabled:
        return {
            "status": "error",
            "error": f"Captions and transcripts are disabled for video '{target_id}'.",
            "error_code": "TRANSCRIPTS_DISABLED",
            "video_id": target_id,
            "captions_available": False,
        }
    except NoTranscriptFound:
        return {
            "status": "error",
            "error": f"No transcript found for video '{target_id}' in requested languages ({requested_langs}).",
            "error_code": "NO_TRANSCRIPT_FOUND",
            "video_id": target_id,
            "captions_available": False,
        }
    except VideoUnavailable:
        return {
            "status": "error",
            "error": f"YouTube video '{target_id}' is unavailable, private, or has been removed.",
            "error_code": "VIDEO_UNAVAILABLE",
            "video_id": target_id,
            "captions_available": False,
        }
    except YouTubeRequestFailed as req_err:
        return {
            "status": "error",
            "error": f"YouTube network request failure for video '{target_id}': {req_err}",
            "error_code": "RATE_LIMITED",
            "video_id": target_id,
            "captions_available": False,
        }
    except CouldNotRetrieveTranscript as ret_err:
        return {
            "status": "error",
            "error": f"Could not retrieve transcript for video '{target_id}': {ret_err}",
            "error_code": "RETRIEVAL_FAILED",
            "video_id": target_id,
            "captions_available": False,
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Unexpected transcript extraction error for video '{target_id}': {exc}",
            "error_code": "EXECUTION_ERROR",
            "video_id": target_id,
            "captions_available": False,
        }


def get_transcript_text(
    video_url: str = "",
    video_id: str = "",
    languages: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Extract plain text transcript without timestamp metadata."""
    return fetch_transcript(
        video_url=video_url,
        video_id=video_id,
        languages=languages,
        format="text",
        **kwargs,
    )


def list_transcripts(
    video_url: str = "",
    video_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """List all available transcripts, languages, and translation tracks for a video.

    Args:
        video_url: Target YouTube video URL.
        video_id: Optional 11-character video ID.

    Returns:
        Structured listing of manually created and auto-generated transcripts.
    """
    target_input = video_id or video_url or kwargs.get("url") or kwargs.get("id") or ""
    try:
        target_id = extract_video_id(target_input)
    except ValueError as val_err:
        return {
            "status": "error",
            "error": str(val_err),
            "error_code": "INVALID_INPUT",
        }

    if not HAS_YOUTUBE_API or YouTubeTranscriptApi is None:
        return {
            "status": "error",
            "error": "youtube-transcript-api package is not installed in current environment.",
            "error_code": "DEPENDENCY_MISSING",
            "video_id": target_id,
        }

    try:
        transcript_list = _get_transcript_list(target_id)
        available_tracks: list[dict[str, Any]] = []

        for t in transcript_list:
            available_tracks.append({
                "language": getattr(t, "language", ""),
                "language_code": getattr(t, "language_code", ""),
                "is_generated": getattr(t, "is_generated", False),
                "is_translatable": getattr(t, "is_translatable", False),
            })

        return {
            "status": "ok",
            "video_id": target_id,
            "track_count": len(available_tracks),
            "transcripts": available_tracks,
        }
    except TranscriptsDisabled:
        return {
            "status": "error",
            "error": f"Transcripts are disabled for video '{target_id}'.",
            "error_code": "TRANSCRIPTS_DISABLED",
            "video_id": target_id,
            "transcripts": [],
        }
    except VideoUnavailable:
        return {
            "status": "error",
            "error": f"YouTube video '{target_id}' is unavailable or private.",
            "error_code": "VIDEO_UNAVAILABLE",
            "video_id": target_id,
            "transcripts": [],
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Failed to list transcripts for video '{target_id}': {exc}",
            "error_code": "EXECUTION_ERROR",
            "video_id": target_id,
            "transcripts": [],
        }


def health() -> dict[str, Any]:
    """Check runtime health and dependencies of the YouTube transcript fetcher plugin."""
    return {
        "status": "healthy" if HAS_YOUTUBE_API else "degraded",
        "service": "youtube-transcript-fetcher",
        "engine": "youtube-transcript-api",
        "dependency_installed": HAS_YOUTUBE_API,
        "isolation": "subprocess",
        "version": "1.0.0",
    }


# -----------------------------------------------------------------------------
# JSON-RPC 2.0 Dispatcher & Server Bridge
# -----------------------------------------------------------------------------

RPC_METHODS = {
    "fetch_transcript": fetch_transcript,
    "get_transcript": fetch_transcript,
    "get_transcript_text": get_transcript_text,
    "list_transcripts": list_transcripts,
    "health": health,
    "ping": lambda: {"status": "ok", "pong": True},
}


def handle_rpc_request(request_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a parsed JSON-RPC 2.0 request payload and return response object."""
    req_id = request_data.get("id", 0)
    method_name = request_data.get("method", "")
    params = request_data.get("params", {})

    if not isinstance(params, dict):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32602,
                "message": "Invalid params: params must be a JSON object",
            },
        }

    handler = RPC_METHODS.get(method_name)
    if handler is None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: '{method_name}'",
            },
        }

    try:
        result = handler(**params)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }
    except Exception as handler_err:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32000,
                "message": f"Server execution error in '{method_name}': {handler_err}",
            },
        }


def run_jsonrpc_server(
    stdin_stream: TextIO | None = None,
    stdout_stream: TextIO | None = None,
) -> None:
    """Run line-buffered JSON-RPC 2.0 server reading stdin and writing stdout."""
    stdin = stdin_stream or sys.stdin
    stdout = stdout_stream or sys.stdout

    for raw_line in stdin:
        trimmed = raw_line.strip()
        if not trimmed:
            continue

        try:
            req_json = json.loads(trimmed)
            if not isinstance(req_json, dict):
                resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32600, "message": "Invalid Request: expected JSON object"},
                }
            else:
                resp = handle_rpc_request(req_json)
        except json.JSONDecodeError as decode_err:
            resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {decode_err}"},
            }

        stdout.write(json.dumps(resp) + "\n")
        stdout.flush()


if __name__ == "__main__":
    run_jsonrpc_server()
