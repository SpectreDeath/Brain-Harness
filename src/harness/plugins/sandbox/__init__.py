"""Sandbox executors — isolation strategies for untrusted plugins.

Decomposed package providing multiple execution isolation levels:
- in_process: direct Python calls (trusted built-in only, Rule 5)
- subprocess: JSON-RPC over stdin/stdout with Win32/Linux kernel OOM enforcement
- venv: dedicated virtualenv + subprocess execution
- container: Docker / Podman container isolation with network air-gapping
- wasm: in-process WebAssembly execution via wasmtime
- factory: centralized strategy selection and Rule 58 single-seam IoC resolution
"""

from __future__ import annotations

from harness.plugins.sandbox.base import (
    SANDBOX_FACTORY_KEY,
    SandboxError,
    SandboxExecutor,
    _get_process_rss_mb,
)
from harness.plugins.sandbox.container import (
    ContainerExecutor,
    DockerExecutor,
)
from harness.plugins.sandbox.factory import (
    SandboxExecutorFactory,
    resolve_sandbox_executor_factory,
)
from harness.plugins.sandbox.in_process import InProcessExecutor
from harness.plugins.sandbox.subprocess import SubprocessExecutor
from harness.plugins.sandbox.venv import VenvExecutor
from harness.plugins.sandbox.wasm import WasmSandboxExecutor

__all__ = [
    "ContainerExecutor",
    "DockerExecutor",
    "InProcessExecutor",
    "SANDBOX_FACTORY_KEY",
    "SandboxError",
    "SandboxExecutor",
    "SandboxExecutorFactory",
    "SubprocessExecutor",
    "VenvExecutor",
    "WasmSandboxExecutor",
    "_get_process_rss_mb",
    "resolve_sandbox_executor_factory",
]
