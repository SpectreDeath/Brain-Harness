"""Container execution inside isolated Docker / Podman containers."""

from __future__ import annotations

from pathlib import Path
import textwrap
from typing import TYPE_CHECKING, Any

import structlog

from harness.plugins.sandbox.base import SandboxError, SandboxExecutor

if TYPE_CHECKING:
    from harness.plugins.transport import StdioJsonRpcTransport

logger = structlog.get_logger()


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
        import uuid

        from harness.plugins.transport import StdioJsonRpcTransport

        if not self._runtime_binary:
            raise SandboxError(
                "docker", "Container runtime (docker/podman) not found in system PATH"
            )

        entrypoint = self._find_entrypoint()
        if not entrypoint:
            raise SandboxError(
                "docker", "No Python entrypoint found for container sandbox"
            )

        try:
            ep_rel = entrypoint.relative_to(self._plugin_dir)
        except ValueError:
            ep_rel = Path(entrypoint.name)

        self._container_name = f"harness_plugin_{uuid.uuid4().hex[:8]}"

        image = (
            getattr(self._config, "image", "python:3.11-slim")
            if self._config
            else "python:3.11-slim"
        )
        memory = (
            getattr(self._config, "memory_limit", "256m") if self._config else "256m"
        )
        cpu_limit = (
            str(getattr(self._config, "cpu_limit", 1.0)) if self._config else "1.0"
        )
        network = getattr(self._config, "network", "none") if self._config else "none"
        read_only = (
            getattr(self._config, "read_only_root", True) if self._config else True
        )

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
            f"{self._plugin_dir!s}:/app:ro",
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

__all__ = [
    "ContainerExecutor",
    "DockerExecutor",
]
