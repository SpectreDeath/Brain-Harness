# Circuit-Breaker Sandboxing & Manifest Schema Verification for Dynamic Plugin Ecosystems

## Context
When loading community or dynamically synthesized plugins, plugins may throw unhandled exceptions, loop indefinitely, attempt path traversal, or access unauthorized system resources, threatening gateway stability.

## Distilled Learning
Implement secure extension management and failure containment (`ExtensionManager`):
1. **Manifest Schema Validation (`MANIFEST_SCHEMA`)**:
   - Enforces strict regex patterns for `plugin_id` (`^[a-z][a-z0-9_-]+$`), semantic versioning, and description constraints.
   - Declares explicit boolean permissions: `network_access`, `filesystem_read`, `filesystem_write`, `subprocess`.
2. **Path Traversal & Import Blocking**:
   - Ensures `entry_point` resolves strictly within the plugin directory boundary.
   - Prevents unsafe directory escapes.
3. **Automated 3-Strike Circuit Breaker (`_wrap_sandboxed_handler`)**:
   - Tracks consecutive tool execution failures per plugin.
   - Upon 3 consecutive failures, trips the circuit to `OPEN` state, rejecting subsequent calls immediately with a graceful fallback error payload without crashing the agent loop.
   - Supports cool-off timeouts and self-healing reset.

## Triggers & Seam Choices
- **Trigger**: Plugin discovery, loading, and tool handler execution in `src/harness/plugins/loader.py`.
- **Seam Choice**: Wire circuit breaker wrapping into `InProcessExecutor` and `SubprocessSandboxTransport`.
