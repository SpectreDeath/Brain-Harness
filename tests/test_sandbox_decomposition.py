"""Characterization test contract for decomposed harness.plugins.sandbox package."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from harness.kernel.context import ServiceContext
from harness.plugins.manifest import (
    ContainerConfig,
    EntrypointSpec,
    IsolationMode,
    PluginManifest,
)


class SampleModule:
    """Sample in-process test target."""

    def sync_multiply(self, a: int, b: int) -> int:
        return a * b

    async def async_greet(self, name: str) -> str:
        return f"Hello, {name}!"

    async def slow_operation(self) -> str:
        await asyncio.sleep(0.5)
        return "done"

    def fail(self) -> None:
        raise RuntimeError("Sample execution failure")


def test_submodule_independent_imports() -> None:
    """Verify all decomposed sandbox submodules can be imported independently."""
    from harness.plugins.sandbox.base import (
        SANDBOX_FACTORY_KEY,
        SandboxError,
        SandboxExecutor,
        _get_process_rss_mb,
    )
    from harness.plugins.sandbox.in_process import InProcessExecutor
    from harness.plugins.sandbox.subprocess import SubprocessExecutor
    from harness.plugins.sandbox.venv import VenvExecutor
    from harness.plugins.sandbox.container import ContainerExecutor, DockerExecutor
    from harness.plugins.sandbox.wasm import WasmSandboxExecutor
    from harness.plugins.sandbox.factory import (
        SandboxExecutorFactory,
        resolve_sandbox_executor_factory,
    )
    from harness.plugins.sandbox import (
        SANDBOX_FACTORY_KEY as ROOT_KEY,
        ContainerExecutor as RootContainer,
        DockerExecutor as RootDocker,
        InProcessExecutor as RootInProcess,
        SandboxError as RootError,
        SandboxExecutor as RootExecutor,
        SandboxExecutorFactory as RootFactory,
        SubprocessExecutor as RootSubprocess,
        VenvExecutor as RootVenv,
        WasmSandboxExecutor as RootWasm,
        _get_process_rss_mb as root_rss,
        resolve_sandbox_executor_factory as root_resolve,
    )

    assert RootError is SandboxError
    assert RootExecutor is SandboxExecutor
    assert RootInProcess is InProcessExecutor
    assert RootSubprocess is SubprocessExecutor
    assert RootVenv is VenvExecutor
    assert RootContainer is ContainerExecutor
    assert RootDocker is DockerExecutor
    assert RootWasm is WasmSandboxExecutor
    assert RootFactory is SandboxExecutorFactory
    assert RootDocker is ContainerExecutor
    assert ROOT_KEY is SANDBOX_FACTORY_KEY
    assert root_rss is _get_process_rss_mb
    assert root_resolve is resolve_sandbox_executor_factory


@pytest.mark.asyncio
async def test_in_process_executor_contract() -> None:
    """Verify InProcessExecutor execution, lifecycle, timeouts, and error handling."""
    from harness.plugins.sandbox.in_process import InProcessExecutor

    mod = SampleModule()
    executor = InProcessExecutor(mod)

    assert executor.name == "in_process"
    assert not executor.is_running

    # Not running -> error
    res = await executor.execute("sync_multiply", {"a": 2, "b": 3})
    assert res["status"] == "error"
    assert "not running" in res["error"].lower()

    await executor.start()
    assert executor.is_running

    # Sync method
    res = await executor.execute("sync_multiply", {"a": 4, "b": 5})
    assert res == {"status": "ok", "result": 20}

    # Async method
    res = await executor.execute("async_greet", {"name": "Antigravity"})
    assert res == {"status": "ok", "result": "Hello, Antigravity!"}

    # Method not found
    res = await executor.execute("non_existent_method")
    assert res["status"] == "error"
    assert "Method not found" in res["error"]

    # Exception in method
    res = await executor.execute("fail")
    assert res["status"] == "error"
    assert "Sample execution failure" in res["error"]

    # Timeout
    res = await executor.execute("slow_operation", timeout=0.05)
    assert res["status"] == "error"
    assert "Timeout" in res["error"]

    await executor.stop()
    assert not executor.is_running


def test_subprocess_executor_runner_resolution(tmp_path: Path) -> None:
    """Verify SubprocessExecutor initializes and resolves bridge_runner.py cleanly."""
    from harness.plugins.sandbox.subprocess import SubprocessExecutor

    dummy_script = tmp_path / "dummy_plugin.py"
    dummy_script.write_text("print('test')", encoding="utf-8")

    executor = SubprocessExecutor(
        dummy_script,
        memory_limit_mb=256.0,
        network_disabled=True,
    )
    assert executor.name == "subprocess"
    assert not executor.is_running
    assert executor.transport is None

    # Check runner script exists
    runner = Path(executor._resolve_runner_path())
    assert runner.exists()
    assert runner.name == "bridge_runner.py"


def test_container_and_docker_aliases(tmp_path: Path) -> None:
    """Verify ContainerExecutor properties and DockerExecutor alias."""
    from harness.plugins.sandbox.container import ContainerExecutor, DockerExecutor

    dummy_script = tmp_path / "main.py"
    dummy_script.write_text("print('container')", encoding="utf-8")

    assert DockerExecutor is ContainerExecutor

    cfg = ContainerConfig(image="python:3.12-slim", memory_limit="128m")
    executor = ContainerExecutor(
        plugin_dir=tmp_path,
        entrypoint=dummy_script,
        config=cfg,
        runtime="mock-docker",
    )
    assert executor.name == "docker"
    assert not executor.is_running


def test_wasm_sandbox_executor_attributes(tmp_path: Path) -> None:
    """Verify WasmSandboxExecutor properties and availability probe."""
    from harness.plugins.sandbox.wasm import WasmSandboxExecutor

    wasm_file = tmp_path / "test.wasm"
    wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")

    executor = WasmSandboxExecutor(wasm_file)
    assert executor.name == "wasm"
    assert executor.wasm_path == wasm_file.resolve()
    assert not executor.is_running
    assert isinstance(WasmSandboxExecutor.is_available(), bool)


def test_factory_entrypoint_discovery(tmp_path: Path) -> None:
    """Verify SandboxExecutorFactory discovers entrypoints via manifest or candidates."""
    from harness.plugins.sandbox.factory import SandboxExecutorFactory

    factory = SandboxExecutorFactory

    # 1. Manifest explicit entrypoint
    manifest = PluginManifest(
        name="test_explicit",
        version="1.0.0",
        entrypoint="custom_entry.py",
    )
    custom_ep = tmp_path / "custom_entry.py"
    custom_ep.write_text("pass", encoding="utf-8")

    found = factory.find_entrypoint(manifest, tmp_path)
    assert found == custom_ep

    # 2. Candidate entrypoint fallback (main.py)
    custom_ep.unlink()
    main_py = tmp_path / "main.py"
    main_py.write_text("pass", encoding="utf-8")

    found_main = factory.find_entrypoint(manifest=None, root=tmp_path)
    assert found_main == main_py


def test_factory_strategy_creation(tmp_path: Path) -> None:
    """Verify SandboxExecutorFactory dispatches appropriate executor strategies."""
    from harness.plugins.sandbox.factory import SandboxExecutorFactory
    from harness.plugins.sandbox.in_process import InProcessExecutor
    from harness.plugins.sandbox.subprocess import SubprocessExecutor
    from harness.plugins.sandbox.venv import VenvExecutor

    entrypoint = tmp_path / "main.py"
    entrypoint.write_text("def run(): pass\n", encoding="utf-8")

    # InProcess (trusted)
    trusted_manifest = PluginManifest(
        name="trusted_plugin",
        version="1.0.0",
        isolation=IsolationMode.IN_PROCESS,
        trusted=True,
    )
    inproc = SandboxExecutorFactory.create(trusted_manifest, tmp_path)
    assert isinstance(inproc, InProcessExecutor)

    # InProcess requested but untrusted -> Subprocess sandbox forced (Rule 5)
    untrusted_manifest = PluginManifest(
        name="untrusted_plugin",
        version="1.0.0",
        isolation=IsolationMode.IN_PROCESS,
        trusted=False,
    )
    forced_subproc = SandboxExecutorFactory.create(untrusted_manifest, tmp_path)
    assert isinstance(forced_subproc, SubprocessExecutor)

    # Venv isolation
    venv_manifest = PluginManifest(
        name="venv_plugin",
        version="1.0.0",
        isolation=IsolationMode.VENV,
        dependencies=["requests"],
    )
    venv_exec = SandboxExecutorFactory.create(venv_manifest, tmp_path)
    assert isinstance(venv_exec, VenvExecutor)


def test_resolve_sandbox_executor_factory_single_seam() -> None:
    """Verify Rule 58 single-seam IoC resolution for SandboxExecutorFactory."""
    from harness.plugins.sandbox.factory import (
        SandboxExecutorFactory,
        resolve_sandbox_executor_factory,
    )
    from harness.plugins.sandbox.base import SANDBOX_FACTORY_KEY

    ctx = ServiceContext()

    # When not registered, resolve_sandbox_executor_factory registers and returns the factory class
    factory_class = resolve_sandbox_executor_factory(ctx)
    assert factory_class is SandboxExecutorFactory
    assert ctx.has(SANDBOX_FACTORY_KEY)

    # Subsequent resolution retrieves the cached class
    cached = resolve_sandbox_executor_factory(ctx)
    assert cached is SandboxExecutorFactory
