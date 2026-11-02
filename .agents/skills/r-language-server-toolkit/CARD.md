```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: r-language-server-toolkit                                     │
│ Category: engineering / developer-tooling                            │
│ Version: 1.0.0                                                       │
│ Invocation: /r-language-server-toolkit                               │
│ Triggers: "r language server", "r lsp", "r runtime", "jgd plot",     │
│           "r session watcher", "reditorsupport", "vscode-r"          │
│ Requires: "r-runtime", "developer_tooling"                           │
│ Target: R language server integration, graphics streaming & session  │
└──────────────────────────────────────────────────────────────────────┘
```

# R Language Server Toolkit — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Session Discovery** | Discover R binaries, packages & session environment | `RSessionInspection` | Valid R runtime & working directory mapped |
| **Stage 2: Diagnostics & AST** | Ingest LSP diagnostics & normalize code units | `tuple[RDiagnosticItem, ...]` | 0-indexed UTF-16 code units aligned |
| **Stage 3: Graphics Streaming** | Stream `jgd` JSON display-list packets | `RPlotEvent` | Zero-dependency plot packets serialized |
| **Stage 4: Configuration Gate** | Validate language server arguments & timeouts | `RLanguageServerConfig` | Non-blocking debounce & path parameters verified |

---

## Vocabulary & Levers

- **LSP 3.17 Protocol**: Microsoft Language Server Protocol standardizing completion, definition, hover, and diagnostics.
- **`GEdevice` Callbacks**: Low-level C graphics engine callback hooks implemented by `jgd` to serialize drawing primitives to JSON.
- **Session Watcher (`.vsc.attach`)**: Non-invasive R task callback observing global symbols and loaded namespaces without polluting `.GlobalEnv`.
- **Slotted/Frozen Dataclasses (Rule 12)**: Memory-efficient immutable structures for diagnostics, sessions, and plot events.
- **Subprocess Pipe Drainage (Rule 14)**: Clean disposal of IPC pipes inside `finally` blocks to prevent proactor deadlocks.

---

## Mandatory Invariants Checklist

- [ ] **Non-Invasive Observation**: Never inject variables into `.GlobalEnv`; isolate all helper functions in `.vsc`.
- [ ] **Debounced Diagnostics**: Linter and AST diagnostic passes must debounce edit events to prevent compute thrashing.
- [ ] **Headless Graphics Transport**: Plot primitives must stream via IPC pipes or WebSockets without creating blocking GUI windows.
- [ ] **Slotted & Frozen Models**: Domain entities must declare `slots=True, frozen=True` to enforce immutability (Rule 12).
- [ ] **Subprocess Pipe Drainage**: All asynchronous subprocess transports must explicitly close standard pipes in `finally` blocks (Rule 14).

