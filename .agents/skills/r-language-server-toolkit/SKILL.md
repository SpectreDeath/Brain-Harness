---
name: r-language-server-toolkit
description: Scaffold, configure, and inspect R language server protocol runtimes, C-level graphics devices (jgd), and session watchers for R execution environments. Do not use for generic web scraping or Python-only analytics.
---

# R Language Server Toolkit: Ecosystem Architecture & Integration

The `r-language-server-toolkit` skill provides structured domain capabilities for orchestrating R development tooling, integrating the Microsoft Language Server Protocol (LSP 3.17) via `languageserver`, real-time zero-dependency plot streaming via the C-level `jgd` graphics engine, and non-invasive R user-space session introspection from `vscode-R`.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.

---

## The Three Foundational Pillars

### 1. LSP 3.17 Protocol Compliance & Asynchronous Diagnostics
Orchestrating bidirectional JSON-RPC communication over standard I/O and TCP transports. Employs version-gated document caching (`update_document_index`) and debounced background lint passes (`diagnostics_generation`) to evaluate syntax trees and `lintr` rules without causing editor keystroke latency.

### 2. Headless Zero-Dependency Plot Streaming
Intercepting R C-level `GEdevice` primitives (lines, polylines, polygons, circles, rasters, and text) through function table callbacks in `device.c`. Converts drawing commands directly into structured JSON streams pushed across OS-native named pipes or WebSockets to HTML5 Canvas / SVG frontends without headful GUI windowing locks.

### 3. Non-Invasive Session Reflection
Observing active R runtime state (loaded packages, workspace symbols, active devices, working directories) through user-space task callbacks (`.vsc.attach`). Encapsulates observation logic within an isolated environment namespace (`.vsc`) to prevent symbol contamination of the user's `.GlobalEnv`.

---

## Operational Workflow

```
[R Process / Console]
         │ (addTaskCallback)
         ▼
[.vsc.attach() Reflection] ──► [Atomic JSON Queue] ──► [Session Inspection API]
         │
         ▼ (GEdevice C hooks)
[jgd Graphics Engine] ───────► [Named Pipe / TCP] ───► [Canvas / SVG Webview]
         │
         ▼ (JSON-RPC over stdio)
[languageserver Engine] ────► [LSP 3.17 Client] ─────► [Diagnostics & Completions]
```

1. **Session Inspection**:
   - Query runtime working directory, loaded namespaces, and exported workspace symbols.
   - Verify environment cleanliness to ensure user namespaces remain unpolluted.
2. **Diagnostics Normalization**:
   - Parse LSP diagnostic payloads and map R 1-indexed line/column positions into 0-indexed UTF-16 code units.
   - Classify diagnostic severity (Error = 1, Warning = 2, Information = 3, Hint = 4).
3. **Plot Event Streaming**:
   - Capture plot resize, redraw, and display-list packets from `jgd`.
   - Forward serialized graphics events to frontend consumers without blocking the R compute thread.

---

## Anti-Patterns

- **Synchronous Keystroke Linting** — Triggering full AST parsing and lintr execution synchronously on every edit event rather than debouncing.
- **Disk Polling for Graphics Updates** — Watching temporary disk directories for static PNG files instead of streaming primitives over named pipes.
- **GlobalEnv Mutation for State Tracking** — Injecting helper variables directly into the user's `.GlobalEnv` rather than isolated environments.
- **Unchecked Request Superseding** — Failing to cancel active formatting or completion requests when a new document edit arrives.
- **Monolithic LSP-Bound Syntax** — Coupling text syntax highlighting to language server initialization, causing unstyled text during server cold-starts.

