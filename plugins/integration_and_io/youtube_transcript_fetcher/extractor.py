"""URL parsing and 11-character YouTube video ID extraction."""

from __future__ import annotations

import re
import urllib.parse

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
