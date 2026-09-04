"""Comprehensive unit and integration tests for youtube_transcript_fetcher plugin.

Validates:
1. Video ID and URL parsing across multiple YouTube formats.
2. Transcript retrieval and format conversion (JSON & Text).
3. Graceful exception handling for disabled captions and unavailable videos.
4. Line-buffered JSON-RPC 2.0 server protocol over stdin/stdout streams.
5. SkillCardParser, SkillValidator, and PluginValidator schema compliance.
6. Skill Knowledge Graph router intent matching.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from plugins.integration_and_io.youtube_transcript_fetcher.main import (
    extract_video_id,
    fetch_transcript,
    get_transcript_text,
    health,
    list_transcripts,
    run_jsonrpc_server,
)
from harness.creator.skills import SkillValidator
from harness.creator.validator import PluginValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    index_skill_catalog,
    query_skill_router,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser


@pytest.mark.unit
class TestVideoIdExtractor:
    """Test URL parsing and 11-character video ID normalization."""

    def test_extract_bare_id(self) -> None:
        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("  1a2B3c4D5eF  ") == "1a2B3c4D5eF"

    def test_extract_watch_url(self) -> None:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_watch_url_with_parameters(self) -> None:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share&t=42s"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_shortened_url(self) -> None:
        url = "https://youtu.be/dQw4w9WgXcQ?t=10"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_embed_url(self) -> None:
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_shorts_url(self) -> None:
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_extract_live_url(self) -> None:
        url = "https://www.youtube.com/live/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_urls_raise_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid YouTube URL"):
            extract_video_id("https://vimeo.com/12345678")

        with pytest.raises(ValueError, match="cannot be empty"):
            extract_video_id("")


@pytest.mark.unit
class TestFetchTranscript:
    """Test transcript retrieval, format serialization, and error mapping."""

    @pytest.fixture
    def mock_transcript_data(self) -> list[dict[str, object]]:
        return [
            {"text": "Hello world", "start": 0.0, "duration": 2.5},
            {"text": "Welcome to the demonstration", "start": 2.5, "duration": 3.0},
        ]

    def test_fetch_transcript_json_success(
        self, mock_transcript_data: list[dict[str, object]]
    ) -> None:
        with patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.HAS_YOUTUBE_API",
            True,
        ), patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.YouTubeTranscriptApi"
        ) as mock_api:
            mock_api.get_transcript.return_value = mock_transcript_data

            result = fetch_transcript(
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                format="json",
            )

            assert result["status"] == "ok"
            assert result["video_id"] == "dQw4w9WgXcQ"
            assert result["format"] == "json"
            assert result["captions_available"] is True
            assert result["segment_count"] == 2
            assert result["transcript"] == mock_transcript_data
            assert "Hello world Welcome to the demonstration" in result["raw_text"]

    def test_fetch_transcript_text_success(
        self, mock_transcript_data: list[dict[str, object]]
    ) -> None:
        with patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.HAS_YOUTUBE_API",
            True,
        ), patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.YouTubeTranscriptApi"
        ) as mock_api:
            mock_api.get_transcript.return_value = mock_transcript_data

            result = get_transcript_text(video_id="dQw4w9WgXcQ")

            assert result["status"] == "ok"
            assert result["format"] == "text"
            assert result["transcript_text"] == "Hello world Welcome to the demonstration"
            assert result["captions_available"] is True

    def test_captions_disabled_graceful_handling(self) -> None:
        from plugins.integration_and_io.youtube_transcript_fetcher.main import (
            TranscriptsDisabled,
        )

        with patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.HAS_YOUTUBE_API",
            True,
        ), patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.YouTubeTranscriptApi"
        ) as mock_api:
            mock_api.get_transcript.side_effect = TranscriptsDisabled("dQw4w9WgXcQ")

            result = fetch_transcript(video_id="dQw4w9WgXcQ")

            assert result["status"] == "error"
            assert result["error_code"] == "TRANSCRIPTS_DISABLED"
            assert result["captions_available"] is False
            assert "disabled" in result["error"].lower()

    def test_video_unavailable_graceful_handling(self) -> None:
        from plugins.integration_and_io.youtube_transcript_fetcher.main import (
            VideoUnavailable,
        )

        with patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.HAS_YOUTUBE_API",
            True,
        ), patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.YouTubeTranscriptApi"
        ) as mock_api:
            mock_api.get_transcript.side_effect = VideoUnavailable("dQw4w9WgXcQ")

            result = fetch_transcript(video_id="dQw4w9WgXcQ")

            assert result["status"] == "error"
            assert result["error_code"] == "VIDEO_UNAVAILABLE"
            assert result["captions_available"] is False

    def test_list_transcripts_success(self) -> None:
        track1 = MagicMock()
        track1.language = "English"
        track1.language_code = "en"
        track1.is_generated = False
        track1.is_translatable = True

        track2 = MagicMock()
        track2.language = "Spanish"
        track2.language_code = "es"
        track2.is_generated = True
        track2.is_translatable = True

        with patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.HAS_YOUTUBE_API",
            True,
        ), patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.YouTubeTranscriptApi"
        ) as mock_api:
            mock_api.list_transcripts.return_value = [track1, track2]

            res = list_transcripts(video_id="dQw4w9WgXcQ")

            assert res["status"] == "ok"
            assert res["track_count"] == 2
            assert res["transcripts"][0]["language_code"] == "en"
            assert res["transcripts"][1]["is_generated"] is True

    def test_health_probe(self) -> None:
        status = health()
        assert status["service"] == "youtube-transcript-fetcher"
        assert status["isolation"] == "subprocess"


@pytest.mark.unit
class TestJsonRpcServer:
    """Test line-buffered JSON-RPC 2.0 communication over stdin/stdout."""

    def test_jsonrpc_fetch_transcript_call(self) -> None:
        sample_segments = [{"text": "Testing RPC", "start": 0.0, "duration": 1.0}]

        with patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.HAS_YOUTUBE_API",
            True,
        ), patch(
            "plugins.integration_and_io.youtube_transcript_fetcher.main.YouTubeTranscriptApi"
        ) as mock_api:
            mock_api.get_transcript.return_value = sample_segments

            request_obj = {
                "jsonrpc": "2.0",
                "id": 101,
                "method": "fetch_transcript",
                "params": {"video_id": "dQw4w9WgXcQ", "format": "json"},
            }
            stdin_stream = io.StringIO(json.dumps(request_obj) + "\n")
            stdout_stream = io.StringIO()

            run_jsonrpc_server(stdin_stream, stdout_stream)

            output_lines = stdout_stream.getvalue().strip().splitlines()
            assert len(output_lines) == 1

            response = json.loads(output_lines[0])
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 101
            assert "result" in response
            assert response["result"]["status"] == "ok"
            assert response["result"]["video_id"] == "dQw4w9WgXcQ"

    def test_jsonrpc_method_not_found(self) -> None:
        request_obj = {
            "jsonrpc": "2.0",
            "id": 102,
            "method": "non_existent_method",
            "params": {},
        }
        stdin_stream = io.StringIO(json.dumps(request_obj) + "\n")
        stdout_stream = io.StringIO()

        run_jsonrpc_server(stdin_stream, stdout_stream)

        output_line = stdout_stream.getvalue().strip()
        response = json.loads(output_line)

        assert response["id"] == 102
        assert "error" in response
        assert response["error"]["code"] == -32601

    def test_jsonrpc_parse_error(self) -> None:
        stdin_stream = io.StringIO("NOT_VALID_JSON\n")
        stdout_stream = io.StringIO()

        run_jsonrpc_server(stdin_stream, stdout_stream)

        output_line = stdout_stream.getvalue().strip()
        response = json.loads(output_line)

        assert "error" in response
        assert response["error"]["code"] == -32700


@pytest.mark.integration
class TestSkillMetadataAndValidation:
    """Test validation reports and Agent Skill Knowledge Graph routing."""

    def test_skill_card_parser(self) -> None:
        plugin_dir = (
            Path("plugins") / "integration_and_io" / "youtube_transcript_fetcher"
        )
        node = SkillCardParser.parse_directory(plugin_dir)

        assert node is not None
        assert node.name == "youtube-transcript-fetcher"
        assert node.category == "integration_and_io"
        assert len(node.stages) >= 5
        assert len(node.anti_patterns) >= 2
        assert len(node.invariants) >= 3

    def test_skill_validator_passes(self) -> None:
        plugin_dir = (
            Path("plugins") / "integration_and_io" / "youtube_transcript_fetcher"
        )
        report = SkillValidator.validate(plugin_dir)
        # Invariant AGENTS.md Rule 34: evaluate overall boolean status via report.valid
        assert report.valid is True
        assert len(report.errors) == 0

    def test_plugin_validator_passes(self) -> None:
        plugin_dir = (
            Path("plugins") / "integration_and_io" / "youtube_transcript_fetcher"
        )
        report = PluginValidator.validate_sync(plugin_dir)
        # Invariant AGENTS.md Rule 34: evaluate overall boolean status via report.valid
        assert report.valid is True
        assert len(report.errors) == 0

    def test_skill_knowledge_graph_routing(self) -> None:
        index_skill_catalog(".")

        # Query semantic intent to ingest YouTube captions
        res = query_skill_router("Fetch spoken transcript and captions from youtube video", top_k=3)
        assert res["status"] == "ok"
        assert len(res["matches"]) > 0

        # Invariant AGENTS.md Rule 35: match entries are strictly keyed by 'skill_name'
        match_names = [m["skill_name"] for m in res["matches"]]
        assert "youtube-transcript-fetcher" in match_names
