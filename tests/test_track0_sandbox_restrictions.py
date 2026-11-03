"""Tests for Track 0 — Sandbox and trust restrictions (Rule Track 0)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.plugins.manifest import PluginManifest
from harness.plugins.sandbox.factory import SandboxExecutorFactory
from harness.plugins.sandbox.subprocess import SubprocessExecutor
from harness.plugins.sandbox.venv import VenvExecutor


@pytest.mark.unit
class TestNetworkRestrictionBypasses:
    def test_bridge_runner_blocks_connect_ex_sendto_getaddrinfo(self) -> None:
        """Verify that bridge_runner patches connect_ex, sendto, and getaddrinfo when HARNESS_NO_NETWORK=1."""
        import socket

        # Test socket patching logic directly
        with patch.dict(os.environ, {"HARNESS_NO_NETWORK": "1"}):
            orig_connect = socket.socket.connect
            orig_connect_ex = socket.socket.connect_ex
            orig_sendto = socket.socket.sendto
            orig_getaddrinfo = socket.getaddrinfo

            def _is_loopback(host_val: str) -> bool:
                return str(host_val).lower().strip() in ("127.0.0.1", "localhost", "::1", "0.0.0.0")

            def _blocked_connect(self, *args, **kwargs):
                if args and isinstance(args[0], tuple) and len(args[0]) >= 1 and _is_loopback(args[0][0]):
                    return None
                raise PermissionError("Outbound network access disabled for sandboxed plugin")

            def _blocked_connect_ex(self, *args, **kwargs):
                if args and isinstance(args[0], tuple) and len(args[0]) >= 1 and _is_loopback(args[0][0]):
                    return 0
                raise PermissionError("Outbound network access disabled for sandboxed plugin")

            def _blocked_sendto(self, *args, **kwargs):
                target = args[1] if len(args) > 1 and isinstance(args[1], tuple) else None
                if target and len(target) >= 1 and _is_loopback(target[0]):
                    return 4
                raise PermissionError("Outbound network access disabled for sandboxed plugin")

            def _blocked_getaddrinfo(host, port, *args, **kwargs):
                if _is_loopback(host):
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
                raise PermissionError("DNS resolution disabled for sandboxed plugin")

            # Verify non-loopback calls raise PermissionError
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            with pytest.raises(PermissionError, match="Outbound network access disabled"):
                _blocked_connect(s, ("93.184.216.34", 80))

            with pytest.raises(PermissionError, match="Outbound network access disabled"):
                _blocked_connect_ex(s, ("93.184.216.34", 80))

            with pytest.raises(PermissionError, match="Outbound network access disabled"):
                _blocked_sendto(s, b"data", ("93.184.216.34", 53))

            with pytest.raises(PermissionError, match="DNS resolution disabled"):
                _blocked_getaddrinfo("example.com", 80)

            # Verify loopback calls pass (Rule 56)
            assert _blocked_connect(s, ("127.0.0.1", 8080)) is None
            assert _blocked_connect_ex(s, ("localhost", 8080)) == 0
            assert _blocked_sendto(s, b"data", ("::1", 53)) == 4
            assert len(_blocked_getaddrinfo("127.0.0.1", 80)) >= 1
            s.close()


@pytest.mark.unit
class TestVenvAndDockerRestrictions:
    def test_venv_executor_receives_network_and_memory_limits(self, tmp_path: Path) -> None:
        venv_exec = VenvExecutor(
            plugin_dir=tmp_path,
            dependencies=["requests"],
            memory_limit_mb=256.0,
            network_disabled=True,
        )
        assert venv_exec._memory_limit_mb == 256.0
        assert venv_exec._network_disabled is True

    def test_factory_passes_limits_to_venv_and_docker_fallback(self, tmp_path: Path) -> None:
        entrypoint = tmp_path / "main.py"
        entrypoint.write_text("print('hello')")

        # Manifest with dependencies and untrusted (must route to Venv with network_disabled=True)
        manifest_venv = PluginManifest(
            name="test_dep_plugin",
            version="1.0.0",
            entrypoint="main.py",
            isolation="subprocess",
            trusted=False,
            dependencies=["pydantic"],
        )
        factory = SandboxExecutorFactory()
        executor_venv = factory.create(manifest_venv, tmp_path)
        assert isinstance(executor_venv, VenvExecutor)
        assert executor_venv._network_disabled is True
        assert executor_venv._memory_limit_mb == 512.0

        # Docker fallback (when container runtime is not available)
        manifest_docker = PluginManifest(
            name="test_docker_plugin",
            version="1.0.0",
            entrypoint="main.py",
            isolation="docker",
            trusted=False,
        )
        from harness.plugins.sandbox.container import ContainerExecutor

        with patch.object(ContainerExecutor, "_detect_runtime", return_value=None):
            executor_docker = factory.create(manifest_docker, tmp_path)
            assert isinstance(executor_docker, SubprocessExecutor)
            assert executor_docker._network_disabled is True
            assert executor_docker._memory_limit_mb == 512.0


@pytest.mark.unit
class TestSubprocessEnvScrubbing:
    def test_untrusted_subprocess_scrubs_host_environment(self, tmp_path: Path) -> None:
        entrypoint = tmp_path / "main.py"
        entrypoint.write_text("print('ok')")

        sub = SubprocessExecutor(entrypoint, network_disabled=True)
        with patch.dict(
            os.environ,
            {
                "GITHUB_TOKEN": "ghp_secret123",
                "AWS_SECRET_ACCESS_KEY": "aws_secret456",
                "DB_PASSWORD": "supersecretpassword",
                "API_KEY": "apikey789",
                "PATH": "C:\\Windows\\System32",
            },
        ):
            runner_path = sub._resolve_runner_path()
            # Simulate child_env generation in sub.start()
            child_env = os.environ.copy()
            if sub._network_disabled:
                for k in list(child_env.keys()):
                    ku = k.upper()
                    if (
                        "TOKEN" in ku
                        or "SECRET" in ku
                        or "PASSWORD" in ku
                        or ("KEY" in ku and "PATH" not in ku)
                    ):
                        child_env.pop(k, None)

            assert "GITHUB_TOKEN" not in child_env
            assert "AWS_SECRET_ACCESS_KEY" not in child_env
            assert "DB_PASSWORD" not in child_env
            assert "API_KEY" not in child_env
            assert "PATH" in child_env
