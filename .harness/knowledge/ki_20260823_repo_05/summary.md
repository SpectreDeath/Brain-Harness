# App-Server Daemon RPC Gate & Automated Rust-to-TS Schema Synchronization

## Problem
In multi-surface agent architectures where desktop applications, command-line interfaces, terminal UIs, and IDE extensions communicate with a central agent daemon, manually writing client-side API bindings leads to severe protocol drift, subtle serialization bugs, and breaking schema changes.

## Solution
Implement an App-Server daemon with automated cross-language type synchronization:
1. **Typed JSON-RPC Protocol**: Standardize request, response, and notification structures (`*Params`, `*Response`, `*Notification`) on a singular resource model (`thread/read`, `app/list`).
2. **Strict Wire Encoding**: Use `#[serde(rename_all = "camelCase")]` and explicit discriminated union tags (`#[serde(tag = "type")]`).
3. **Automated TypeScript Export**: Annotate Rust protocol models with `#[ts(export_to = "v2/")]` (via `ts-rs`) to automatically generate matching TypeScript definitions during build (`just write-app-server-schema`).
4. **Daemon Lifecycle Management**: Expose Unix Domain Sockets and Windows Named Pipes with connection gating, connection cleanup, and dynamic tool refresh.

## Operational Guideline
- Never manually synchronize client-side TypeScript types with server-side Rust/Python models.
- Enforce automated type generation as a mandatory CI verification gate.
- Use singular resource names and camelCase encoding across all RPC wire interfaces.

## Provenance
- Source repository: `D:/GitHub/cloned/codex-main/codex-main`
- Primary files: `codex-rs/app-server-protocol/src/lib.rs#L1-L80`, `codex-rs/app-server/src/main.rs`, `AGENTS.md#L100-L160`
