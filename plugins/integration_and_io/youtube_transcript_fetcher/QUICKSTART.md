# Quickstart: `plugin.youtube_transcript_fetcher`

Native Brain-Harness plugin for extracting YouTube transcripts and timed captions via isolated subprocess JSON-RPC 2.0.

## Overview

- **Plugin Name**: `plugin.youtube_transcript_fetcher`
- **Isolation**: `subprocess`
- **Transport**: Line-buffered JSON-RPC 2.0 over standard I/O (stdin/stdout)
- **Engine**: `youtube-transcript-api`

## Tools Exposed

1. `fetch_transcript(video_url, video_id, languages, format, preserve_formatting)`
2. `get_transcript_text(video_url, video_id, languages)`
3. `list_transcripts(video_url, video_id)`
4. `health()`

## JSON-RPC Example

Request:
```json
{"jsonrpc": "2.0", "id": 1, "method": "fetch_transcript", "params": {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "json"}}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "status": "ok",
    "video_id": "dQw4w9WgXcQ",
    "format": "json",
    "captions_available": true,
    "segment_count": 42,
    "transcript": [
      {"text": "We're no strangers to love", "start": 18.5, "duration": 3.2}
    ],
    "raw_text": "We're no strangers to love..."
  }
}
```
