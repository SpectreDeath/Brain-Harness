# LSP Incremental Text Synchronization & Asynchronous Lintr Diagnostics Pipeline

## Context & Theoretical Grounding
In dynamically typed scientific languages like R, computing full AST diagnostics (syntax parsing, symbol resolution, and stylistic linting via `lintr`) synchronously on every keystroke causes prohibitive editor latency. The R Language Server resolves this by implementing version-gated document caching and decoupled diagnostic generations.

## Distilled Mental Models & Heuristics
1. **Version-Gated Parse Data Caching**:
   - In `update_document_index()` (`handlers-textsync.R#L5-L24`), if the document version matches `doc$parse_data$version` and content is unchanged without parse errors, cached AST source specs are reused directly.
2. **Debounced Diagnostic Generation**:
   - In `diagnostics.R#L10-L21`, diagnostics track index workspace generations (`index$diagnostics_generation(uri)`). Superseded diagnostic jobs are canceled before computing expensive regex and AST lint passes.
3. **Dual Code-Point to Unit Conversion**:
   - `diagnostic_range()` maps R 1-indexed byte/column positions into LSP 0-indexed UTF-16 character code units via `code_point_to_unit()` to ensure multi-byte character alignment.

## Anti-Pattern Defenses
- **Synchronous Keystroke Linting**: Running heavy `lintr` lint passes on `textDocument/didChange` instead of debounced event queues.
- **Unchecked Request Superseding**: Failing to cancel active formatting or completion requests when a new document edit arrives (`cancel_formatting_requests`).
