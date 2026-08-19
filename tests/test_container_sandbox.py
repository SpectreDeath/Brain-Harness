"""Tests for ContainerExecutor, Docker isolation mode, and fallback resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from harness.plugins.manifest import ContainerConfig, IsolationMode, PluginManifest
from harness.plugins.sandbox import (
    ContainerExecutor,
    DockerExecutor,
    SandboxError,
    SandboxExecutorFactory,
    SubprocessExecutor,
)


@pytest.mark.unit
class TestContainerSandbox:
    def test_container_config_manifest_schema(self) -> None:
        cfg = ContainerConfig(
            image="python:3.11-alpine",
            memory_limit="512m",
            cpu_limit=2.0,
            network="none",
            read_only_root=True,
            environment={"API_KEY": "secret"},
        )
        manifest = PluginManifest(
            name="container_test",
            version="1.0.0",
            isolation=IsolationMode.DOCKER,
            container=cfg,
        )
        assert manifest.isolation == IsolationMode.DOCKER
        assert manifest.container is not None
        assert manifest.container.image == "python:3.11-alpine"
        assert manifest.container.memory_limit == "512m"

    def test_factory_fallback_when_docker_not_in_path(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def run(): return 'ok'")
        manifest = PluginManifest(
            name="docker_plug",
            version="1.0.0",
            isolation=IsolationMode.DOCKER,
        )

        with patch.object(ContainerExecutor, "_detect_runtime", return_value=None):
            executor = SandboxExecutorFactory.create(manifest, tmp_path)
            # Should fall back gracefully to SubprocessExecutor
            assert isinstance(executor, SubprocessExecutor)

    def test_factory_creates_container_executor_when_runtime_available(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def run(): return 'ok'")
        manifest = PluginManifest(
            name="docker_plug",
            version="1.0.0",
            isolation=IsolationMode.DOCKER,
            container=ContainerConfig(memory_limit="128m"),
        )

        with patch.object(ContainerExecutor, "_detect_runtime", return_value="docker"):
            executor = SandboxExecutorFactory.create(manifest, tmp_path)
            assert isinstance(executor, ContainerExecutor)
            assert executor.name == "docker"
            assert isinstance(executor, DockerExecutor)

    @pytest.mark.asyncio
    async def test_container_executor_start_missing_runtime_raises(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def run(): return 'ok'")
        executor = ContainerExecutor(tmp_path, runtime=None)

        with pytest.raises(SandboxError) as exc_info:
            await executor.start()
        assert "Container runtime (docker/podman) not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_container_executor_start_and_execute_mocked(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def compute(x): return x * 2")
        executor = ContainerExecutor(
            tmp_path,
            runtime="docker",
            config=ContainerConfig(memory_limit="256m", network="none"),
        )

        mock_transport = AsyncMock()
        mock_transport.is_running = True
        mock_transport.pid = 12345
        mock_transport.call.return_value = {"result": 84}

        with patch("harness.plugins.transport.StdioJsonRpcTransport", return_value=mock_transport):
            await executor.start()
            assert executor.is_running is True

            res = await executor.execute("compute", {"x": 42})
            assert res["status"] == "ok"
            assert res["result"] == 84

            mock_transport.call.assert_called_once_with("compute", {"x": 42}, timeout=30.0)

            await executor.stop()
            mock_transport.stop.assert_called_once()
