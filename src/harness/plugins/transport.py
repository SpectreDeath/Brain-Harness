"""Asynchronous Stdio JSON-RPC 2.0 Transport.

Unified inter-process communication layer underlying both SubprocessExecutor
(Python sandbox plugins) and MCPClientPlugin (Model Context Protocol clients).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import structlog

logger = structlog.get_logger()


class TransportError(RuntimeError):
    """Raised when communication over the transport fails."""


class StdioJsonRpcTransport:
    """Manages an external child process communicating via line-delimited JSON-RPC over stdin/stdout."""

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        *,
        env: dict[str, str] | None = None,
        cwd: Path | str | None = None,
    ) -> None:
        self.command = command
        self.args = args or []
        self.env = env
        self.cwd = str(cwd) if cwd else None
        self._process: asyncio.subprocess.Process | None = None
        self._req_id = 0
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        """Whether the child process is currently alive."""
        return self._process is not None and self._process.returncode is None

    @property
    def pid(self) -> int | None:
        """Process ID of the running child process."""
        return self._process.pid if self._process else None

    async def start(self) -> None:
        """Spawn the child subprocess with piped standard streams."""
        if self.is_running:
            return

        self._process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
            cwd=self.cwd,
        )

        logger.debug(
            "Stdio transport started",
            command=self.command,
            pid=self._process.pid,
        )

    async def stop(self, timeout: float = 3.0) -> None:
        """Terminate child process with graceful escalation to SIGKILL."""
        if not self._process:
            return

        proc = self._process
        self._process = None

        if proc.returncode is None:
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=timeout)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    proc.kill()
                    await proc.wait()
                except ProcessLookupError:
                    pass

        logger.debug("Stdio transport stopped", command=self.command)

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and await its response.

        Args:
            method: Method name to execute.
            params: Parameters dictionary.
            timeout: Maximum wait time in seconds.

        Returns:
            JSON-RPC response dictionary containing 'result' or 'error'.
        """
        if not self.is_running or not self._process or self._process.stdin is None or self._process.stdout is None:
            raise TransportError(f"Process '{self.command}' is not running")

        async with self._lock:
            self._req_id += 1
            payload = {
                "jsonrpc": "2.0",
                "id": self._req_id,
                "method": method,
                "params": params or {},
            }

            try:
                line_to_send = json.dumps(payload) + "\n"
                self._process.stdin.write(line_to_send.encode("utf-8"))
                await self._process.stdin.drain()

                raw_line = await asyncio.wait_for(
                    self._process.stdout.readline(),
                    timeout=timeout,
                )

                if not raw_line:
                    return {"id": self._req_id, "error": "Process closed stdout stream unexpectedly"}

                return cast(dict[str, Any], json.loads(raw_line.decode("utf-8").strip()))
            except asyncio.TimeoutError:
                return {"id": self._req_id, "error": f"Call to '{method}' timed out after {timeout}s"}
            except json.JSONDecodeError as err:
                return {"id": self._req_id, "error": f"Invalid JSON response: {err}"}
            except (OSError, RuntimeError) as err:
                raise TransportError(f"Transport communication failure: {err}") from err

    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a one-way notification (no response expected)."""
        if not self.is_running or not self._process or self._process.stdin is None:
            raise TransportError(f"Process '{self.command}' is not running")

        async with self._lock:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
            }
            line_to_send = json.dumps(payload) + "\n"
            self._process.stdin.write(line_to_send.encode("utf-8"))
            await self._process.stdin.drain()
