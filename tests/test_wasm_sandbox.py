"""Tests for WASM Sandbox Executor and Factory Dispatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.plugins.manifest import IsolationMode, PluginManifest
from harness.plugins.sandbox import (
    SandboxExecutorFactory,
    SubprocessExecutor,
    WasmSandboxExecutor,
)


@pytest.mark.unit
class TestWasmManifestAndIsolation:
    def test_isolation_mode_wasm_enum(self) -> None:
        assert IsolationMode.WASM == "wasm"
        assert IsolationMode("wasm") == IsolationMode.WASM

    def test_manifest_with_wasm_isolation(self) -> None:
        manifest = PluginManifest(
            name="test-wasm-tool",
            version="1.0.0",
            isolation=IsolationMode.WASM,
            wasm_entrypoint="leaf_transform.wasm",
        )
        assert manifest.isolation == IsolationMode.WASM
        assert manifest.wasm_entrypoint == "leaf_transform.wasm"


@pytest.mark.unit
@pytest.mark.asyncio
class TestWasmSandboxExecutor:
    async def test_wasm_executor_metadata(self, tmp_path: Path) -> None:
        wasm_file = tmp_path / "module.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")

        executor = WasmSandboxExecutor(wasm_file)
        assert executor.name == "wasm"
        assert not executor.is_running
        assert executor.wasm_path == wasm_file.resolve()

    async def test_start_without_wasmtime_raises_runtime_error(
        self, tmp_path: Path
    ) -> None:
        wasm_file = tmp_path / "module.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")

        with patch.object(WasmSandboxExecutor, "is_available", return_value=False):
            executor = WasmSandboxExecutor(wasm_file)
            with pytest.raises(RuntimeError, match="requires 'wasmtime'"):
                await executor.start()

    async def test_execute_when_not_running(self, tmp_path: Path) -> None:
        wasm_file = tmp_path / "module.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")

        executor = WasmSandboxExecutor(wasm_file)
        res = await executor.execute("run", {"val": 42})
        assert res["status"] == "error"
        assert "not running" in res["error"]

    async def test_execute_with_mocked_wasmtime(self, tmp_path: Path) -> None:
        wasm_file = tmp_path / "module.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")

        mock_wasmtime = MagicMock()
        mock_engine = MagicMock()
        mock_module = MagicMock()
        mock_wasmtime.Engine.return_value = mock_engine
        mock_wasmtime.Module.from_file.return_value = mock_module

        with patch.dict("sys.modules", {"wasmtime": mock_wasmtime}):
            with patch.object(WasmSandboxExecutor, "is_available", return_value=True):
                executor = WasmSandboxExecutor(wasm_file)
                await executor.start()
                assert executor.is_running

                await executor.stop()
                assert not executor.is_running


@pytest.mark.unit
class TestWasmFactoryDispatch:
    def test_factory_fallback_to_subprocess_when_wasmtime_missing(
        self, tmp_path: Path
    ) -> None:
        py_entry = tmp_path / "main.py"
        py_entry.write_text("print('hello')", encoding="utf-8")
        wasm_file = tmp_path / "plugin.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")

        manifest = PluginManifest(
            name="demo-wasm",
            isolation=IsolationMode.WASM,
            entrypoint="main.py",
            wasm_entrypoint="plugin.wasm",
        )

        with patch.object(WasmSandboxExecutor, "is_available", return_value=False):
            executor = SandboxExecutorFactory.create(manifest, tmp_path)
            assert isinstance(executor, SubprocessExecutor)

    def test_factory_creates_wasm_executor_when_available(
        self, tmp_path: Path
    ) -> None:
        wasm_file = tmp_path / "plugin.wasm"
        wasm_file.write_bytes(b"\x00asm\x01\x00\x00\x00")

        manifest = PluginManifest(
            name="demo-wasm",
            isolation=IsolationMode.WASM,
            wasm_entrypoint="plugin.wasm",
        )

        with patch.object(WasmSandboxExecutor, "is_available", return_value=True):
            executor = SandboxExecutorFactory.create(manifest, tmp_path)
            assert isinstance(executor, WasmSandboxExecutor)
            assert executor.wasm_path == wasm_file.resolve()
