"""Service protocol, default implementation, and HarnessPlugin lifecycle entrypoint."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

from .operations import (
    fetch_transcript,
    get_transcript_text,
    health,
    list_transcripts,
)


@runtime_checkable
class YouTubeTranscriptFetcherService(Protocol):
    """Protocol for fetching YouTube transcripts, segments, and metadata."""

    def fetch_transcript(
        self,
        video_url: str = "",
        video_id: str = "",
        languages: list[str] | None = None,
        format: str = "json",
        preserve_formatting: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Extract transcript or timed captions from a YouTube video."""
        ...

    def get_transcript_text(
        self,
        video_url: str = "",
        video_id: str = "",
        languages: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Extract plain text transcript without timestamp metadata."""
        ...

    def list_transcripts(
        self,
        video_url: str = "",
        video_id: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """List all available transcripts, languages, and translation tracks."""
        ...

    def health(self) -> dict[str, Any]:
        """Check runtime health and dependencies of the YouTube transcript fetcher plugin."""
        ...


YOUTUBE_TRANSCRIPT_FETCHER_KEY = ServiceKey[YouTubeTranscriptFetcherService](
    "service.youtube_transcript_fetcher"
)


class DefaultYouTubeTranscriptFetcherService:
    """Default service implementation dispatching to operational functions."""

    def fetch_transcript(
        self,
        video_url: str = "",
        video_id: str = "",
        languages: list[str] | None = None,
        format: str = "json",
        preserve_formatting: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return fetch_transcript(
            video_url=video_url,
            video_id=video_id,
            languages=languages,
            format=format,
            preserve_formatting=preserve_formatting,
            **kwargs,
        )

    def get_transcript_text(
        self,
        video_url: str = "",
        video_id: str = "",
        languages: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return get_transcript_text(
            video_url=video_url,
            video_id=video_id,
            languages=languages,
            **kwargs,
        )

    def list_transcripts(
        self,
        video_url: str = "",
        video_id: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        return list_transcripts(
            video_url=video_url,
            video_id=video_id,
            **kwargs,
        )

    def health(self) -> dict[str, Any]:
        return health()


class YouTubeTranscriptFetcherPlugin(HarnessPlugin):
    """Native YouTube Transcript Fetcher Plugin for Brain Harness."""

    def __init__(self) -> None:
        super().__init__()
        self._service: YouTubeTranscriptFetcherService = (
            DefaultYouTubeTranscriptFetcherService()
        )

    @property
    def name(self) -> str:
        return "plugin.youtube_transcript_fetcher"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Extract transcripts and timed captions from YouTube video URLs or IDs."

    @property
    def service(self) -> YouTubeTranscriptFetcherService:
        return self._service

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [YOUTUBE_TRANSCRIPT_FETCHER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(YOUTUBE_TRANSCRIPT_FETCHER_KEY, self._service)

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass
