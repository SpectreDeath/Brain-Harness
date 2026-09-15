# plugin.youtube_transcript_fetcher (v1.0.0)

Extract transcripts and timed captions from YouTube video URLs or IDs via isolated subprocess JSON-RPC

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/youtube_transcript_fetcher` |
| Category | `integration_and_io` |
| Isolation Mode | `subprocess` |
| Services Provided | `service.youtube_transcript_fetcher` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `fetch_transcript` | `(video_url, video_id, languages, format, preserve_formatting)` | Extract full transcript or timed segments from a YouTube video URL or ID |
| `get_transcript_text` | `(video_url, video_id, languages)` | Extract plain concatenated text of a YouTube video transcript without timestamp metadata |
| `list_transcripts` | `(video_url, video_id)` | List all available transcripts, languages, and translation tracks for a YouTube video |
| `health` | `()` | Check runtime health status and dependencies of the YouTube transcript fetcher plugin |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Native YouTube Transcript Fetcher plugin for Brain-Harness.

Operates within an isolated subprocess sandbox, communicating via line-buffered
JSON-RPC 2.0 over standard I/O streams (stdin/stdout). Extracts transcripts,
timed caption segments, and dialogue from YouTube video URLs or 11-character IDs
using youtube-transcript-api.

#### Functions

- `def extract_video_id(url_or_id) -> str` — Extract an 11-character YouTube video ID from a URL or raw ID string.
- `def fetch_transcript(video_url, video_id, languages, format, preserve_formatting) -> dict[str, Any]` — Extract transcript or timed captions from a YouTube video.
- `def get_transcript_text(video_url, video_id, languages) -> dict[str, Any]` — Extract plain text transcript without timestamp metadata.
- `def list_transcripts(video_url, video_id) -> dict[str, Any]` — List all available transcripts, languages, and translation tracks for a video.
- `def health() -> dict[str, Any]` — Check runtime health and dependencies of the YouTube transcript fetcher plugin.
- `def handle_rpc_request(request_data) -> dict[str, Any]` — Execute a parsed JSON-RPC 2.0 request payload and return response object.
- `def run_jsonrpc_server(stdin_stream, stdout_stream) -> None` — Run line-buffered JSON-RPC 2.0 server reading stdin and writing stdout.

### Module [__init__.py](__init__.py)

YouTube Transcript Fetcher Plugin Package.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.youtube_transcript_fetcher.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
