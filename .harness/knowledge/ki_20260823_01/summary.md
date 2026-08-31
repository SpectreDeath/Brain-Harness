# Subprocess Sandbox Boundary & Dynamic Plugin Isolation

## Problem
Running external or dynamically ingested plugins directly inside the host Python process creates critical stability and security hazards:
- Unhandled exceptions or memory leaks crash the entire agent kernel.
- Untrusted dependencies can alter global interpreter state or pollute the IoC container.

## Solution
Isolate all untrusted plugins inside a child Python subprocess using `SubprocessExecutor`:
- **Protocol**: Standard input/output line-delimited JSON-RPC bridge.
- **Resilience**: Enforce 30-second `asyncio.wait_for` timeouts on all RPC calls.
- **Teardown**: Automated process kill and cleanup hooks on plugin deactivation.

## Operational Guideline
- Always default to `SubprocessExecutor` for plugins loaded from external paths or user drop-in directories (`plugins/`).
- Reserve `InProcessExecutor` exclusively for verified internal plugins declared in `src/harness/services/`.

## Provenance
- Source Target: [`src/harness/plugins/sandbox.py:L141-180`](file:///d:/GitHub/projects/Brain%20Harness/src/harness/plugins/sandbox.py#L141-L180)
- Architectural Invariant: [`AGENTS.md:L9`](file:///d:/GitHub/projects/Brain%20Harness/AGENTS.md#L9)
- Isnad Decision ID: `dec_20260823_01`
