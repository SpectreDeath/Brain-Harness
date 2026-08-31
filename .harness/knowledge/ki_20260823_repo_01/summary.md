# Multi-Tier OS Process Sandboxing & Policy Transforms

## Problem
AI agent systems executing arbitrary shell commands and tool scripts risk filesystem corruption, privilege escalation, or unauthorized network calls if run directly in the host user context without containment.

## Solution
Implement a unified `PlatformSandbox` manager abstraction that translates high-level permission profiles (`PermissionProfile`, `FileSystemSandboxPolicy`, `NetworkSandboxPolicy`) into OS-native isolation primitives:
1. **Linux**: Bubblewrap (`bwrap`) namespaces combined with Landlock LSM rule compilation (`landlock.rs`) for fine-grained path allowlists.
2. **macOS**: Seatbelt SBPL sandbox profiles (`seatbelt_base_policy.sbpl`, `seatbelt_network_policy.sbpl`) compiled dynamically.
3. **Windows**: Restricted Tokens and Job Objects with dynamic filesystem read grant tokens (`windows_sandbox_read_grants.rs`).

## Operational Guideline
- Always route tool and shell executions through the sandbox manager.
- Map high-level permission intents into declarative platform-specific policies rather than executing ad-hoc path checks.
- Support foreign execution platforms via unified socket IPC.

## Provenance
- Source repository: `D:/GitHub/cloned/codex-main/codex-main`
- Primary files: `codex-rs/sandboxing/src/manager.rs#L36-L76`, `codex-rs/sandboxing/src/bwrap.rs`, `codex-rs/sandboxing/src/windows.rs`
