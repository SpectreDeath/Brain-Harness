# Agent Desktop Plugin (`plugin.agent_desktop`)

The `plugin.agent_desktop` integrates Vercel Labs' native OS accessibility tree computer-use engine into Brain Harness.

## Features

- **No Pixels or OCR**: Reads the native OS accessibility tree directly (UI Automation on Windows, AXUIElement on macOS, AT-SPI on Linux).
- **Qualified Element References**: Allocates scoped `@<snapshot_id>:e<N>` refs per snapshot with whole-window `CaptureProof` uniqueness verification.
- **2D Delivery & Retry Disposition**: Returns `DeliveryDisposition` (`NotDelivered`..`DeliveredVerified`) and `RetryDisposition` (`Safe`..`Unsafe`) to prevent double-activation of non-idempotent actions.
- **Headless Semantic Dispatch**: Dispatches clicks and value edits through OS accessibility APIs without moving the mouse pointer or stealing focus.
- **Clap-Derived MCP Stdio Integration**: Connects seamlessly with `agent-desktop mcp` (protocol `2026-07-28`) with bounded concurrency (8 calls) and graceful SIGTERM input release.

## Tools Exposed

1. `desktop_snapshot`: Capture accessibility tree or drill down into a qualified root ref.
2. `desktop_act`: Act on a ref (`click`, `set-value`, `type`, `select`, `toggle`, `focus`).
3. `desktop_find`: Search tree by role, name, or text substring.
4. `desktop_manage_window`: List, focus, resize, and move desktop windows.
5. `desktop_wait`: Wait for dynamic element or window conditions.
6. `desktop_status`: Query OS accessibility permissions and supported surface overlays.

## IoC Service Key

Registered under `AGENT_DESKTOP_KEY: ServiceKey[AgentDesktopService]`.
