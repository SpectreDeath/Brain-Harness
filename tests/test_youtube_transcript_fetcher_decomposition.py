"""Contract tests verifying YouTube Transcript Fetcher decomposition.

Validates:
1. Strict submodule bounds (AGENTS.md Rule 11: all files <= 200 lines).
2. Slotted dataclass architecture (AGENTS.md Rules 12 & 43).
3. Single-seam IoC resolution (AGENTS.md Rule 58).
4. Plugin module singleton export and lifecycle (AGENTS.md Rules 2 & 45).
5. Service protocol adherence and operations delegation.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from harness.kernel.context import ServiceContext
from plugins.integration_and_io.youtube_transcript_fetcher.main import (
    CaptionSegment,
    DefaultYouTubeTranscriptFetcherService,
    TranscriptResult,
    TranscriptTrack,
    YouTubeTranscriptFetcherPlugin,
    YouTubeTranscriptFetcherService,
    get_default_transcript_fetcher_service,
    plugin,
    resolve_youtube_transcript_fetcher,
)
from plugins.integration_and_io.youtube_transcript_fetcher.service import (
    YOUTUBE_TRANSCRIPT_FETCHER_KEY,
)


@pytest.mark.unit
class TestYouTubeTranscriptFetcherDecomposition:
    """Verify architectural invariants for YouTube Transcript Fetcher decomposition."""

    def test_submodule_line_count_bounds(self) -> None:
        """Rule 11: Verify every submodule in package is <= 200 lines."""
        pkg_dir = Path("plugins") / "integration_and_io" / "youtube_transcript_fetcher"
        py_files = list(pkg_dir.glob("*.py"))
        assert len(py_files) >= 8

        for py_file in py_files:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"{py_file.name} has {lines} lines, exceeding 200-line limit"

    def test_slotted_dataclass_models(self) -> None:
        """Rules 12 & 43: Verify slotted models allocate __slots__."""
        seg = CaptionSegment(text="Hello", start=0.0, duration=1.5)
        assert hasattr(seg, "__slots__")
        assert seg.text == "Hello"

        track = TranscriptTrack(language="English", language_code="en", is_generated=False)
        assert hasattr(track, "__slots__")
        assert track.language_code == "en"

        res = TranscriptResult(status="ok", video_id="dQw4w9WgXcQ", segment_count=1)
        assert hasattr(res, "__slots__")
        assert res.video_id == "dQw4w9WgXcQ"

    def test_single_seam_resolver_fallback_and_ioc(self) -> None:
        """Rule 58: Verify resolver behaves correctly with and without ServiceContext."""
        # Fallback to default when context is None
        default_svc = resolve_youtube_transcript_fetcher(None)
        assert isinstance(default_svc, YouTubeTranscriptFetcherService)
        assert default_svc is get_default_transcript_fetcher_service()

        # Resolution from ServiceContext when provided
        ctx = ServiceContext()
        mock_svc = MagicMock(spec=YouTubeTranscriptFetcherService)
        ctx.provide(YOUTUBE_TRANSCRIPT_FETCHER_KEY, mock_svc)

        resolved = resolve_youtube_transcript_fetcher(ctx)
        assert resolved is mock_svc

    @pytest.mark.asyncio
    async def test_plugin_singleton_and_lifecycle(self) -> None:
        """Rules 2 & 45: Verify exported plugin singleton and IoC registration."""
        assert isinstance(plugin, YouTubeTranscriptFetcherPlugin)
        assert plugin.name == "plugin.youtube_transcript_fetcher"
        assert plugin.version == "1.0.0"
        assert YOUTUBE_TRANSCRIPT_FETCHER_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.optional(YOUTUBE_TRANSCRIPT_FETCHER_KEY)
        assert resolved is not None
        assert isinstance(resolved, YouTubeTranscriptFetcherService)

    def test_service_delegation(self) -> None:
        """Verify DefaultYouTubeTranscriptFetcherService delegates to underlying operations."""
        svc = DefaultYouTubeTranscriptFetcherService()

        # Health
        h = svc.health()
        assert h["service"] == "youtube-transcript-fetcher"
        assert "status" in h

        # Fetch transcript delegation
        with patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.HAS_YOUTUBE_API",
            True,
        ), patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.YouTubeTranscriptApi"
        ) as mock_api:
            mock_api.get_transcript.return_value = [
                {"text": "Sample text", "start": 0.0, "duration": 2.0}
            ]
            res = svc.fetch_transcript(video_id="dQw4w9WgXcQ")
            assert res["status"] == "ok"
            assert res["segment_count"] == 1
            assert res["raw_text"] == "Sample text"

            txt_res = svc.get_transcript_text(video_id="dQw4w9WgXcQ")
            assert txt_res["status"] == "ok"
            assert txt_res["transcript_text"] == "Sample text"
