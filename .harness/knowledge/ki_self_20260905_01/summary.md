# Third-Party Engine Dual-API & Mock Spec Invariant

**ID:** `ki_self_20260905_01`  
**Category:** `testing_and_mocks`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `tests/test_youtube_transcript_fetcher.py`, `plugins/integration_and_io/youtube_transcript_fetcher/main.py`, `commit#fb9ffb6`, `AGENTS.md#Rule39`

## Executive Summary
When wrapping third-party libraries subject to ongoing interface evolution (e.g. `youtube-transcript-api` moving from static `get_transcript()` functions to instance `YouTubeTranscriptApi().fetch()` methods), runtime adapters must gracefully support both calling conventions. Crucially, in unit tests, unspecced `MagicMock` fixtures dynamically return truthy mock attributes for any queried attribute, falsely convincing feature-detection logic (`hasattr(YouTubeTranscriptApi, 'fetch')`) that a new API exists on an unconfigured mock.

## Architectural Invariants & Rules
1. **Classic Method Precedence**: In dual-API adapters, evaluate classic or static methods before newer instance methods, or inspect exact callable signatures.
2. **Mock Spec Isolation**: Test fixtures mocking external classes must declare `spec=ClassName` (e.g., `mock.patch('module.YouTubeTranscriptApi', spec=YouTubeTranscriptApi)`) to prevent unconfigured mock attributes from returning dynamic truthy attributes.
3. **Subprocess Boundary Protection**: Heavy or unstable external APIs should execute within isolated subprocesses to protect the host micro-kernel from third-party segfaults or dependency drift.
4. **Codification**: Formally codified as `AGENTS.md` Rule 39.
