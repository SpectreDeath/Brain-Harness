# Shim: MCP Client Namespacing, Local Discovery & Env-Ref Config

## Overview
- **Source Repository**: `https://github.com/Balanov/shim` (`3b5acfdf`)
- **Primary Files**:
  - `internal/mcp/manager.go#L27-L170`
  - `internal/provider/discovery.go#L14-L99`
  - `internal/config/config.go#L14-L150`

## Core Architecture & Invariants
1. **Dual-Transport MCP Handshake (`mcp.Manager`)**: Supports HTTP (`cfg.URL`) and stdio (`cfg.Command`, `cfg.Args`, `cfg.Env`) using `protocolVersion: "2025-03-26"`, `30s` initialization + discovery timeout, `notifications/initialized` notification, and `60s` execution timeout inspecting `result.IsError`.
2. **Bounded Collision-Free Tool Names (`Register`)**: Maps external tools to `mcp_<server>_<tool>` sanitized to `[A-Za-z0-9_-]`, capped at `64` characters, and fails fast if sanitization produces duplicate names.
3. **Bounded Parallel Local Model Discovery (`Discover`)**: Probes `ollama` (`/api/tags`), `lmstudio` (`/models`), and `llamacpp` (`/models`) concurrently with a `900ms` HTTP deadline and deterministic sorted output.
4. **Secret-Safe Atomic Config (`config.go`)**: Enforces `CurrentVersion = 1`, `Permissions` in `{"ask", "read-only", "auto"}`, `api` in `{"openai", "anthropic"}`, stores `api_key_env` names (never raw secrets), and writes via temp file + atomic rename in `0o700` dirs (`0o600` files).

## Decision Heuristics & Anti-Patterns
- **Never persist raw API keys into config JSON**: Always store the environment variable name (`api_key_env`).
- **Never register sanitized MCP tool names without collision checks**: Truncation to 64 characters can alias distinct upstream tool names unless collisions abort registration.
