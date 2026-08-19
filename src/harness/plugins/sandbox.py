"""Sandbox executors — isolation strategies for untrusted plugins.

Provides multiple execution isolation levels:
    - InProcessExecutor: direct Python calls (trusted only)
    - SubprocessExecutor: JSON-RPC over stdin/stdout (default)
    - VenvExecutor: isolated virtualenv + subprocess

All executors implement the same async interface so the harness can
swap isolation strategies without changing calling code.
"""

from __future__ import annotations

import asyncio
import sys
import textwrap
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from harness.plugins.transport import StdioJsonRpcTransport

logger = structlog.get_logger()


class SandboxError(Exception):
    """Raised when sandbox execution fails."""

    def __init__(self, executor: str, reason: str) -> None:
        self.executor = executor
        self.reason = reason
        super().__init__(f"Sandbox error ({executor}): {reason}")


class SandboxExecutor(ABC):
    """Abstract sandbox executor interface.

    All executors expose the same ``execute`` method so the plugin system
    can swap isolation strategies transparently.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Executor name for logging."""

    @abstractmethod
    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Execute a method on the sandboxed plugin.

        Args:
            method: Name of the method/function to call.
            params: Parameters to pass to the method.
            timeout: Maximum execution time in seconds.

        Returns:
            Dict with ``status`` ("ok" or "error") and ``result`` or ``error``.
        """

    @abstractmethod
    async def start(self) -> None:
        """Start the sandbox environment."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the sandbox and clean up resources."""

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the sandbox is currently active."""


class InProcessExecutor(SandboxExecutor):
    """Execute plugin code directly in the harness process.

    ⚠️  Only for trusted, built-in plugins. No isolation is provided.
    """

    def __init__(self, module: Any) -> None:
        """Initialize with a Python module or object.

        Args:
            module: The module or object containing callable methods.
        """
        self._module = module
        self._running = False

    @property
    def name(self) -> str:
        return "in_process"

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        if not self._running:
            return {"status": "error", "error": "Executor not running"}

        func = getattr(self._module, method, None)
        if func is None:
            return {"status": "error", "error": f"Method not found: {method}"}

        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(**(params or {})), timeout=timeout
                )
            else:
                result = func(**(params or {}))

            return {"status": "ok", "result": result}
        except asyncio.TimeoutError:
            return {"status": "error", "error": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


class SubprocessExecutor(SandboxExecutor):
    """Execute plugin code in a separate Python subprocess via JSON-RPC over stdin/stdout."""

    def __init__(
        self,
        script_path: Path,
        *,
        python: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._script_path = script_path
        self._python = python or sys.executable
        self._env = env
        self._transport: StdioJsonRpcTransport | None = None

    @property
    def name(self) -> str:
        return "subprocess"

    @property
    def is_running(self) -> bool:
        return self._transport is not None and self._transport.is_running

    async def start(self) -> None:
        """Start the subprocess with the JSON-RPC bridge wrapper."""
        from harness.plugins.transport import StdioJsonRpcTransport

        wrapper_code = textwrap.dedent(f"""\
            import sys
            import json
            import importlib.util

            # Load the plugin module
            spec = importlib.util.spec_from_file_location("plugin", {str(self._script_path)!r})
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # JSON-RPC loop
            for line in sys.stdin:
                try:
                    request = json.loads(line.strip())
                    method = request.get("method", "")
                    params = request.get("params", {{}})
                    req_id = request.get("id", 0)

                    func = getattr(module, method, None)
                    if func is None:
                        response = {{"jsonrpc": "2.0", "id": req_id, "error": f"Method not found: {{method}}"}}
                    else:
                        try:
                            result = func(**params)
                            response = {{"jsonrpc": "2.0", "id": req_id, "result": result}}
                        except Exception as e:
                            response = {{"jsonrpc": "2.0", "id": req_id, "error": str(e)}}

                    sys.stdout.write(json.dumps(response) + "\\n")
                    sys.stdout.flush()
                except Exception as e:
                    sys.stdout.write(json.dumps({{"jsonrpc": "2.0", "id": 0, "error": str(e)}}) + "\\n")
                    sys.stdout.flush()
        """)

        self._transport = StdioJsonRpcTransport(
            self._python,
            ["-c", wrapper_code],
            env=self._env,
        )
        await self._transport.start()

        logger.info(
            "Subprocess sandbox started",
            script=str(self._script_path),
            pid=self._transport.pid,
        )

    async def stop(self) -> None:
        """Terminate the subprocess."""
        if self._transport:
            await self._transport.stop()
            self._transport = None

        logger.info("Subprocess sandbox stopped", script=str(self._script_path))

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        if not self.is_running or self._transport is None:
            return {"status": "error", "error": "Subprocess not running"}

        try:
            resp = await self._transport.call(method, params, timeout=timeout)
            if "error" in resp:
                return {"status": "error", "error": resp["error"]}
            return {"status": "ok", "result": resp.get("result")}
        except Exception as e:
            return {"status": "error", "error": str(e)}


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
        self._venv_dir = venv_dir or plugin_dir / ".venv"
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
            _, stderr = await proc.communicate()

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


class ContainerExecutor(SandboxExecutor):
    """Execute plugin code inside an isolated Docker / Podman container via JSON-RPC.

    Provides OS-level isolation, resource bounds (CPU quota, memory limits),
    network air-gapping, and read-only filesystem controls.
    """

    def __init__(
        self,
        plugin_dir: Path,
        entrypoint: Path | None = None,
        *,
        config: Any | None = None,
        runtime: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._plugin_dir = Path(plugin_dir).resolve()
        self._entrypoint = Path(entrypoint).resolve() if entrypoint else None
        self._config = config
        self._runtime_binary = runtime or self._detect_runtime()
        self._env = env or {}
        self._transport: StdioJsonRpcTransport | None = None
        self._container_name: str | None = None

    @classmethod
    def _detect_runtime(cls) -> str | None:
        """Detect available container runtime binary (docker or podman)."""
        import shutil

        for candidate in ("docker", "podman"):
            if shutil.which(candidate):
                return candidate
        return None

    @property
    def name(self) -> str:
        return "docker"

    @property
    def is_running(self) -> bool:
        return self._transport is not None and self._transport.is_running

    def _find_entrypoint(self) -> Path | None:
        if self._entrypoint and self._entrypoint.exists():
            return self._entrypoint
        candidates = ["main.py", "__main__.py", "plugin.py", "app.py"]
        for c in candidates:
            p = self._plugin_dir / c
            if p.exists():
                return p
        py_files = sorted(self._plugin_dir.glob("*.py"))
        return py_files[0] if py_files else None

    async def start(self) -> None:
        """Start the container and attach JSON-RPC bridge."""
        from harness.plugins.transport import StdioJsonRpcTransport
        import uuid

        if not self._runtime_binary:
            raise SandboxError("docker", "Container runtime (docker/podman) not found in system PATH")

        entrypoint = self._find_entrypoint()
        if not entrypoint:
            raise SandboxError("docker", "No Python entrypoint found for container sandbox")

        try:
            ep_rel = entrypoint.relative_to(self._plugin_dir)
        except ValueError:
            ep_rel = Path(entrypoint.name)

        self._container_name = f"harness_plugin_{uuid.uuid4().hex[:8]}"

        image = getattr(self._config, "image", "python:3.11-slim") if self._config else "python:3.11-slim"
        memory = getattr(self._config, "memory_limit", "256m") if self._config else "256m"
        cpu_limit = str(getattr(self._config, "cpu_limit", 1.0)) if self._config else "1.0"
        network = getattr(self._config, "network", "none") if self._config else "none"
        read_only = getattr(self._config, "read_only_root", True) if self._config else True

        wrapper_code = textwrap.dedent(f"""\
            import sys
            import json
            import importlib.util

            spec = importlib.util.spec_from_file_location("plugin", "/app/{ep_rel.as_posix()}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for line in sys.stdin:
                try:
                    request = json.loads(line.strip())
                    method = request.get("method", "")
                    params = request.get("params", {{}})
                    req_id = request.get("id", 0)

                    func = getattr(module, method, None)
                    if func is None:
                        response = {{"jsonrpc": "2.0", "id": req_id, "error": f"Method not found: {{method}}"}}
                    else:
                        try:
                            result = func(**params)
                            response = {{"jsonrpc": "2.0", "id": req_id, "result": result}}
                        except Exception as e:
                            response = {{"jsonrpc": "2.0", "id": req_id, "error": str(e)}}

                    sys.stdout.write(json.dumps(response) + "\\n")
                    sys.stdout.flush()
                except Exception as e:
                    sys.stdout.write(json.dumps({{"jsonrpc": "2.0", "id": 0, "error": str(e)}}) + "\\n")
                    sys.stdout.flush()
        """)

        args = [
            "run",
            "-i",
            "--rm",
            "--name",
            self._container_name,
            f"--memory={memory}",
            f"--cpus={cpu_limit}",
            f"--network={network}",
            "-v",
            f"{str(self._plugin_dir)}:/app:ro",
            "-w",
            "/app",
        ]

        if read_only:
            args.extend(["--read-only", "--tmpfs", "/tmp"])

        cfg_env = getattr(self._config, "environment", {}) if self._config else {}
        merged_env = {**cfg_env, **self._env}
        for k, v in merged_env.items():
            args.extend(["-e", f"{k}={v}"])

        args.extend([image, "python", "-u", "-c", wrapper_code])

        self._transport = StdioJsonRpcTransport(
            self._runtime_binary,
            args,
        )
        await self._transport.start()

        logger.info(
            "Container sandbox started",
            runtime=self._runtime_binary,
            image=image,
            container=self._container_name,
            pid=self._transport.pid,
        )

    async def stop(self) -> None:
        """Stop container execution."""
        if self._transport:
            await self._transport.stop()
            self._transport = None

        logger.info("Container sandbox stopped", container=self._container_name)

    async def execute(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        if not self.is_running or self._transport is None:
            return {"status": "error", "error": "Container executor not running"}

        try:
            resp = await self._transport.call(method, params, timeout=timeout)
            if "error" in resp:
                return {"status": "error", "error": resp["error"]}
            return {"status": "ok", "result": resp.get("result")}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Backward compatibility alias
DockerExecutor = ContainerExecutor


class SandboxExecutorFactory:
    """Authoritative factory for constructing appropriate SandboxExecutor instances.

    Consolidates isolation strategy resolution, entrypoint discovery, and
    dependency-driven sandbox provisioning across the plugin and ingestion subsystems.
    """

    @classmethod
    def find_entrypoint(cls, manifest: Any, root: Path) -> Path | None:
        """Find the main Python entrypoint script in the plugin root."""
        root_path = Path(root)
        if getattr(manifest, "entrypoint", None):
            ep = root_path / manifest.entrypoint
            if ep.exists():
                return ep

        candidates = ["main.py", "__main__.py", "plugin.py", "app.py"]
        for c in candidates:
            p = root_path / c
            if p.exists():
                return p

        py_files = sorted(root_path.glob("*.py"))
        return py_files[0] if py_files else None

    @classmethod
    def create(
        cls,
        manifest: Any,
        root: Path,
        *,
        force_isolation: Any = None,
    ) -> SandboxExecutor | None:
        """Construct the appropriate SandboxExecutor for a manifest and filesystem root.

        Args:
            manifest: PluginManifest instance.
            root: Root path of the plugin.
            force_isolation: Optional override for isolation mode.

        Returns:
            Configured SandboxExecutor or None if no valid strategy/entrypoint found.
        """
        import importlib.util
        from harness.plugins.manifest import IsolationMode

        root_path = Path(root).resolve()
        entrypoint = cls.find_entrypoint(manifest, root_path)
        isolation = force_isolation if force_isolation is not None else getattr(manifest, "isolation", IsolationMode.SUBPROCESS)
        trusted = getattr(manifest, "trusted", False)
        deps = getattr(manifest, "dependencies", []) or []
        name = getattr(manifest, "name", root_path.name)
        container_cfg = getattr(manifest, "container", None)

        if isolation == IsolationMode.IN_PROCESS:
            if trusted and entrypoint and entrypoint.exists():
                try:
                    module_name = f"sandboxed_inproc_{name.replace('.', '_')}"
                    spec = importlib.util.spec_from_file_location(module_name, entrypoint)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        return InProcessExecutor(mod)
                except Exception as e:
                    logger.warning(
                        "Failed in-process plugin import, falling back to subprocess",
                        plugin=name,
                        error=str(e),
                    )
            elif not trusted:
                logger.warning(
                    "Untrusted plugin requested in-process isolation; enforcing subprocess sandbox",
                    plugin=name,
                )

        if isolation == IsolationMode.DOCKER:
            runtime_bin = ContainerExecutor._detect_runtime()
            if runtime_bin:
                return ContainerExecutor(
                    plugin_dir=root_path,
                    entrypoint=entrypoint,
                    config=container_cfg,
                    runtime=runtime_bin,
                )
            logger.warning(
                "Container runtime (docker/podman) not available in PATH; falling back to SubprocessExecutor",
                plugin=name,
            )
            if entrypoint and entrypoint.exists():
                return SubprocessExecutor(entrypoint)
            return None

        if isolation == IsolationMode.VENV or len(deps) > 0:
            return VenvExecutor(
                plugin_dir=root_path,
                dependencies=deps,
            )

        if entrypoint and entrypoint.exists():
            return SubprocessExecutor(entrypoint)

        return None

