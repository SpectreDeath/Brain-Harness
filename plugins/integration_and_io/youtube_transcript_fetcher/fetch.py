"""Transcript extraction and formatting operations."""

from __future__ import annotations

import sys
from typing import Any

from .api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeRequestFailed,
    _get_raw_transcript_data,
    is_api_available,
)
from .extractor import extract_video_id


def _matches_exc(exc: BaseException, *names: str) -> bool:
    """Helper to check exception types against dynamically patched exceptions in main."""
    main_mod = sys.modules.get("plugins.integration_and_io.youtube_transcript_fetcher.main")
    for name in names:
        target = getattr(main_mod, name, None) if main_mod is not None else None
        if target is not None and isinstance(exc, target):
            return True
        local_target = globals().get(name)
        if local_target is not None and isinstance(exc, local_target):
            return True
    return False


def fetch_transcript(
    video_url: str = "",
    video_id: str = "",
    languages: list[str] | None = None,
    format: str = "json",
    preserve_formatting: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Extract transcript or timed captions from a YouTube video."""
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

    if not is_api_available():
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
        if _matches_exc(exc, "TranscriptsDisabled"):
            return {
                "status": "error",
                "error": f"Captions and transcripts are disabled for video '{target_id}'.",
                "error_code": "TRANSCRIPTS_DISABLED",
                "video_id": target_id,
                "captions_available": False,
            }
        if _matches_exc(exc, "NoTranscriptFound"):
            return {
                "status": "error",
                "error": f"No transcript found for video '{target_id}' in requested languages ({requested_langs}).",
                "error_code": "NO_TRANSCRIPT_FOUND",
                "video_id": target_id,
                "captions_available": False,
            }
        if _matches_exc(exc, "VideoUnavailable"):
            return {
                "status": "error",
                "error": f"YouTube video '{target_id}' is unavailable, private, or has been removed.",
                "error_code": "VIDEO_UNAVAILABLE",
                "video_id": target_id,
                "captions_available": False,
            }
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
