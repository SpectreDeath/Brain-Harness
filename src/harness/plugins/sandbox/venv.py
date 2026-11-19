"""Virtualenv isolation with dependency installation and SubprocessExecutor delegation."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

import structlog

from harness.plugins.artifact_cache import (
    PluginArtifactCache, estimate_dir_bytes, is_venv_healthy, venv_python_path,
)
from harness.plugins.sandbox.base import SandboxError, SandboxExecutor
from harness.plugins.sandbox.subprocess import SubprocessExecutor

logger = structlog.get_logger()


class VenvExecutor(SandboxExecutor):
    """Execute plugin code in an isolated virtualenv.

    Creates a dedicated venv, installs the plugin's dependencies, then
    runs the plugin via SubprocessExecutor using the venv's Python.
    """

    def __init__(
        self,
        plugin_dir: Path,
        venv_dir: Path | None = None,
        dependencies: list[str] | None = None,
        memory_limit_mb: float | None = None,
        network_disabled: bool = False,
        artifact_cache: PluginArtifactCache | None = None,
        ttl_seconds: float | None = None,
    ) -> None:
        """Initialize the venv executor.

        Args:
            plugin_dir: Root directory of the plugin.
            venv_dir: Where to create the venv. Defaults to ``plugin_dir/.venv``.
            dependencies: pip packages to install in the venv.
            memory_limit_mb: Memory ceiling in megabytes.
            network_disabled: Whether network access is disabled.
            artifact_cache: Optional dual-capped LRU cache for staged venv reuse.
            ttl_seconds: Optional cache TTL for staged venv entries.
        """
        self._plugin_dir = plugin_dir
        self._venv_dir = venv_dir if venv_dir is not None else Path(".harness") / "venvs" / plugin_dir.name
        self._dependencies = dependencies or []
        self._memory_limit_mb = memory_limit_mb
        self._network_disabled = network_disabled
        self._artifact_cache = artifact_cache
        self._ttl_seconds = ttl_seconds
        self._subprocess: SubprocessExecutor | None = None
        self._setup_done = False

    @property
    def name(self) -> str:
        return "venv"

    @property
    def is_running(self) -> bool:
        return self._subprocess is not None and self._subprocess.is_running

    @property
    def cache_key(self) -> str:
        """Canonical cache key for this executor's target virtualenv."""
        return str(self._venv_dir.resolve())

    def _is_venv_healthy(self) -> bool:
        return is_venv_healthy(self._venv_dir)

    async def start(self) -> None:
        """Create the venv, install deps, and start the subprocess."""
        if self._artifact_cache is not None:
            cached = self._artifact_cache.get(self.cache_key)
            self._setup_done = cached is not None and self._is_venv_healthy()
        elif self._setup_done and not self._is_venv_healthy():
            self._setup_done = False

        if not self._setup_done:
            await self._setup_venv()

        if self._artifact_cache is not None:
            size = estimate_dir_bytes(self._venv_dir)
            self._artifact_cache.put(self.cache_key, self._venv_dir, size, ttl_seconds=self._ttl_seconds)

        entrypoint = self._find_entrypoint()
        if entrypoint is None:
            raise SandboxError("venv", "No Python entrypoint found")

        venv_python = venv_python_path(self._venv_dir)

        self._subprocess = SubprocessExecutor(
            entrypoint,
            python=str(venv_python),
            memory_limit_mb=self._memory_limit_mb,
            network_disabled=self._network_disabled,
        )
        await self._subprocess.start()

    async def stop(self) -> None:
        if self._subprocess:
            await self._subprocess.stop()
            self._subprocess = None

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        if self._subprocess is None:
            return {"status": "error", "error": "Venv executor not started"}
        return await self._subprocess.execute(method, params, timeout=timeout)

    async def _setup_venv(self) -> None:
        """Create virtualenv and install dependencies."""
        import venv

        logger.info("Creating virtualenv", venv_dir=str(self._venv_dir))
        self._venv_dir.parent.mkdir(parents=True, exist_ok=True)
        venv.create(str(self._venv_dir), with_pip=True, clear=True)

        if self._dependencies:
            if sys.platform == "win32":
                pip = self._venv_dir / "Scripts" / "pip.exe"
            else:
                pip = self._venv_dir / "bin" / "pip"

            proc = await asyncio.create_subprocess_exec(
                str(pip),
                "install",
                *self._dependencies,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                _, stderr = await proc.communicate()
            finally:
                if proc.stdin:
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass
                if (
                    proc.stdout
                    and hasattr(proc.stdout, "_transport")
                    and proc.stdout._transport is not None
                ):
                    try:
                        proc.stdout._transport.close()
                    except Exception:
                        pass
                if (
                    proc.stderr
                    and hasattr(proc.stderr, "_transport")
                    and proc.stderr._transport is not None
                ):
                    try:
                        proc.stderr._transport.close()
                    except Exception:
                        pass

            if proc.returncode != 0:
                raise SandboxError(
                    "venv",
                    f"pip install failed: {stderr.decode()[:500]}",
                )

            logger.info(
                "Dependencies installed",
                count=len(self._dependencies),
                venv=str(self._venv_dir),
            )

        self._setup_done = True

    def _find_entrypoint(self) -> Path | None:
        """Find the main Python entrypoint in the plugin directory."""
        candidates = ["main.py", "__main__.py", "plugin.py", "app.py"]
        for name in candidates:
            path = self._plugin_dir / name
            if path.exists():
                return path

        # Fall back to the first .py file
        py_files = list(self._plugin_dir.glob("*.py"))
        return py_files[0] if py_files else None


__all__ = ["VenvExecutor"]
