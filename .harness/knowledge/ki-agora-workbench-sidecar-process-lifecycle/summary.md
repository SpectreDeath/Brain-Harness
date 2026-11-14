# Agora Workbench: Co-Located Loopback Sidecar Process Lifecycle

## Overview
- **Source Repository**: `https://github.com/microsoft/agora-workbench` (`a8ae030b`)
- **Primary Files**:
  - `src/agora_workbench/code_execution/code_execution_models.py#L95-L160`
  - `src/agora_workbench/code_execution/sidecar.py#L46-L195`

## Core Architecture & Invariants
1. **Loopback Containment (`SidecarConfig.host`)**: Sidecars default to `127.0.0.1` and are treated as internal helper daemons invisible to external MCP clients (`url_env_var` is explicitly propagated into sanitized kernels).
2. **Environment Variable Address Lock (`_build_env`)**: Caller-provided `spec.env` overrides are applied first, then `SIDECAR_HOST` and `SIDECAR_PORT` are forcibly rewritten so a misconfigured override cannot redirect the sidecar away from the socket health-checked in `_await_ready()`.
3. **Kernel Python Parity (`_resolve_argv`)**: When `use_env_python=True`, `SidecarManager` resolves `ServerConfig.get_python_path()` and fails loudly if the kernel environment has not been built yet, guaranteeing identical package versions without duplicating virtualenvs.
4. **Atomic Rollback & Two-Stage Teardown (`start_all`, `stop_all`)**: If sidecar `N` fails readiness or exits prematurely, `start_all()` invokes `stop_all()` so zero orphan daemons survive. Teardown signals the entire session process group with `SIGTERM`, waits `10.0s`, and escalates to `SIGKILL` only on hang.

## Decision Heuristics & Anti-Patterns
- **Never share mutable sidecar ports across workers without reservation**: Reject duplicate sidecar names before spawning processes.
- **Never allow user `env` maps to override control-plane bind variables**: Always overwrite `SIDECAR_HOST` and `SIDECAR_PORT` last.
