"""Available transcript tracks listing and health probe operations."""

from __future__ import annotations

import sys
from typing import Any

from .api import (
    TranscriptsDisabled,
    VideoUnavailable,
    _get_transcript_list,
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


def list_transcripts(
    video_url: str = "",
    video_id: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """List all available transcripts, languages, and translation tracks for a video."""
    target_input = video_id or video_url or kwargs.get("url") or kwargs.get("id") or ""
    try:
        target_id = extract_video_id(target_input)
    except ValueError as val_err:
        return {
            "status": "error",
            "error": str(val_err),
            "error_code": "INVALID_INPUT",
        }

    if not is_api_available():
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
        if _matches_exc(exc, "TranscriptsDisabled"):
            return {
                "status": "error",
                "error": f"Transcripts are disabled for video '{target_id}'.",
                "error_code": "TRANSCRIPTS_DISABLED",
                "video_id": target_id,
                "transcripts": [],
            }
        if _matches_exc(exc, "VideoUnavailable"):
            return {
                "status": "error",
                "error": f"YouTube video '{target_id}' is unavailable or private.",
                "error_code": "VIDEO_UNAVAILABLE",
                "video_id": target_id,
                "transcripts": [],
            }
        return {
            "status": "error",
            "error": f"Failed to list transcripts for video '{target_id}': {exc}",
            "error_code": "EXECUTION_ERROR",
            "video_id": target_id,
            "transcripts": [],
        }


def health() -> dict[str, Any]:
    """Check runtime health and dependencies of the YouTube transcript fetcher plugin."""
    api_ok = is_api_available()
    return {
        "status": "healthy" if api_ok else "degraded",
        "service": "youtube-transcript-fetcher",
        "engine": "youtube-transcript-api",
        "dependency_installed": api_ok,
        "isolation": "subprocess",
        "version": "1.0.0",
    }
