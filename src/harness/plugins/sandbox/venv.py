"""Virtualenv isolation with dependency installation and SubprocessExecutor delegation."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

import structlog

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
    ) -> None:
        """Initialize the venv executor.

        Args:
            plugin_dir: Root directory of the plugin.
            venv_dir: Where to create the venv. Defaults to ``plugin_dir/.venv``.
            dependencies: pip packages to install in the venv.
        """
        self._plugin_dir = plugin_dir
        if venv_dir is not None:
            self._venv_dir = venv_dir
        else:
            self._venv_dir = Path(".harness") / "venvs" / plugin_dir.name
        self._dependencies = dependencies or []
        self._subprocess: SubprocessExecutor | None = None
        self._setup_done = False

    @property
    def name(self) -> str:
        return "venv"

    @property
    def is_running(self) -> bool:
        return self._subprocess is not None and self._subprocess.is_running

    async def start(self) -> None:
        """Create the venv, install deps, and start the subprocess."""
        if not self._setup_done:
            await self._setup_venv()

        # Find the entrypoint
        entrypoint = self._find_entrypoint()
        if entrypoint is None:
            raise SandboxError("venv", "No Python entrypoint found")

        # Determine the venv Python path
        if sys.platform == "win32":
            venv_python = self._venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = self._venv_dir / "bin" / "python"

        self._subprocess = SubprocessExecutor(
            entrypoint,
            python=str(venv_python),
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
