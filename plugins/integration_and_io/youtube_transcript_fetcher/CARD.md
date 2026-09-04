```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        youtube-transcript-fetcher                │
│ Category:    integration_and_io                        │
│ Invocation:  /youtube-transcript-fetcher               │
│ Triggers:    "youtube transcript", "fetch captions",   │
│              "youtube video", "video subtitles"        │
│ Version:     1.0.0                                     │
│ Isolation:   subprocess                                │
│ Provides:    "service.youtube_transcript_fetcher"      │
├────────────────────────────────────────────────────────┤
│ Target:      Extract YouTube transcripts via isolated  │
│              subprocess JSON-RPC.                      │
└────────────────────────────────────────────────────────┘
```

# YouTube Transcript Fetcher — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Completion Gate |
|---|---|---|
| **1. Normalization** | Extract and validate 11-character YouTube video ID from URL or text | `11-char ID verified` |
| **2. Dispatch** | Send line-buffered JSON-RPC 2.0 command over stdin/stdout transport | `RPC handshake ok` |
| **3. Visual Brief** | Render interactive sequence and data-flow topology in `%TEMP%` | `HTML report linked` |
| **4. Checkpoint Gate** | Mandatory pause requiring user approval before batch or heavy ingestion | `User approval` |
| **5. Ingestion** | Extract timed segments or plain text with token budget optimization | `Transcript structured` |
| **6. Walkthrough** | Document extraction latency, segment counts, and transcript artifacts | `Walkthrough recorded` |

---

## Input & Output Schema Specification

### Input Schema
| Field | Type | Required | Description |
|---|---|---|---|
| `video_url` | string | Optional | YouTube URL (watch, shortened, embed, shorts, live) |
| `video_id` | string | Optional | 11-character canonical video ID |
| `languages` | list[string] | Optional | Preferred language codes (default: `["en"]`) |
| `format` | string | Optional | Output representation: `"json"` or `"text"` |
| `preserve_formatting` | boolean | Optional | Retain HTML tags in caption text |

### Output Schema
| Field | Type | Description |
|---|---|---|
| `status` | string | Execution outcome: `"ok"` or `"error"` |
| `video_id` | string | Identified 11-character video ID |
| `format` | string | Delivered format (`"json"` or `"text"`) |
| `captions_available` | boolean | Whether valid captions were retrieved |
| `segment_count` | integer | Number of timed dialogue segments |
| `transcript` | list[object] | Timed segments with `text`, `start`, `duration` |
| `raw_text` | string | Concatenated full dialogue text |
| `error_code` | string | Error categorization (`"TRANSCRIPTS_DISABLED"`, etc.) |

---

## Vocabulary & Levers

- **Subprocess Sandbox**: Isolated child process executing external libraries safely without polluting the kernel environment.
- **Line-Buffered JSON-RPC**: Lightweight 2.0 wire protocol exchanging single-line newline-delimited JSON messages over stdin and stdout.
- **Timed Segments**: Individual subtitle entries containing caption text, start offset in seconds, and segment duration.
- **Auto-Generated Captions**: Algorithmic speech-to-text tracks provided by YouTube when manual transcripts are absent.

---

## Mandatory Invariants Checklist

- [ ] Subprocess standard streams reconfigured to UTF-8 on Windows
- [ ] Strict regex parsing preventing malformed URL injection
- [ ] `TranscriptsDisabled` gracefully handled without crashing the runner
- [ ] Line-delimited JSON-RPC messages flushed immediately on stdout
- [ ] No unhandled exceptions propagating across the IPC boundary
