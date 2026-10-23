# OpenCode Bridge Plugin (`plugin.opencode_bridge`)

Brain Harness integration plugin for the [OpenCode](https://github.com/anomalyco/opencode) agent harness and CLI.

## Capabilities

1. **`opencode_status`**: Detects local OpenCode CLI presence, active background service daemon (`opencode service status`), port, and version.
2. **`opencode_run_prompt`**: Headless instruction execution via `opencode run` with path isolation, permission flags, and model selection.
3. **`opencode_session_info`**: Introspects active and historical OpenCode sessions.
4. **`opencode_tool_catalog`**: Catalogs OpenCode's deep module tools (`persistent-pty`, `codemode`, `patch`, `edit`, `read`, `write`, `subagent`).

## Architecture & Invariants

- **AGENTS.md Rule 2**: Uses typed `OPENCODE_BRIDGE_KEY: ServiceKey[OpenCodeBridgeService]`.
- **AGENTS.md Rule 5**: Operates under subprocess sandbox isolation.
- **AGENTS.md Rule 12**: Slotted and frozen data models with `__post_init__` validation.
- **AGENTS.md Rule 45**: Exports module-level singleton `plugin = OpenCodeBridgePlugin()`.
- **AGENTS.md Rule 58**: Single-seam resolver factory `resolve_opencode_bridge(ctx)`.
