"""Asynchronous Stdio JSON-RPC 2.0 Transport.

Unified inter-process communication layer underlying both SubprocessExecutor
(Python sandbox plugins) and MCPClientPlugin (Model Context Protocol clients).
"""

from __future__ import annotations

import asyncio
import json
from collections import deque
from pathlib import Path
from typing import Any

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
        self._write_lock = asyncio.Lock()
        self._pending_futures: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._stderr_buffer: deque[str] = deque(maxlen=50)
        self._stderr_task: asyncio.Task[None] | None = None
        self._stdout_task: asyncio.Task[None] | None = None

    @property
    def _lock(self) -> asyncio.Lock:
        """Backward compatibility alias for write lock."""
        return self._write_lock

    @property
    def is_running(self) -> bool:
        """Whether the child process is currently alive."""
        return self._process is not None and self._process.returncode is None

    @property
    def pid(self) -> int | None:
        """Process ID of the running child process."""
        return self._process.pid if self._process else None

    @property
    def stderr_lines(self) -> list[str]:
        """Recent stderr lines captured from the child process."""
        return list(self._stderr_buffer)

    async def _drain_stderr(self) -> None:
        """Continuously read lines from stderr and keep in ring buffer."""
        if not self._process or not self._process.stderr:
            return
        try:
            while True:
                line = await self._process.stderr.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace").rstrip()
                if line_str:
                    self._stderr_buffer.append(line_str)
                    logger.debug("Subprocess stderr", command=self.command, output=line_str)
        except (asyncio.CancelledError, OSError):
            pass

    async def _read_stdout_loop(self) -> None:
        """Continuously read lines from stdout and fulfill pending JSON-RPC futures."""
        if not self._process or not self._process.stdout:
            return
        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    req_id = data.get("id")
                    if req_id is not None and req_id in self._pending_futures:
                        fut = self._pending_futures.pop(req_id)
                        if not fut.done():
                            fut.set_result(data)
                except Exception as e:
                    logger.debug("Failed parsing JSON-RPC line", command=self.command, output=line_str, error=str(e))
        except (asyncio.CancelledError, OSError):
            pass
        finally:
            recent_stderr = list(self._stderr_buffer)[-5:]
            suffix = f" (stderr: {'; '.join(recent_stderr)})" if recent_stderr else ""
            err_payload = {"error": f"Process stdout stream closed unexpectedly{suffix}"}
            for req_id, fut in list(self._pending_futures.items()):
                if not fut.done():
                    fut.set_result(err_payload)
            self._pending_futures.clear()

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

        if self._process.stdout is not None:
            self._stdout_task = asyncio.create_task(self._read_stdout_loop())

        if self._process.stderr is not None:
            self._stderr_task = asyncio.create_task(self._drain_stderr())

        logger.debug(
            "Stdio transport started",
            command=self.command,
            pid=self._process.pid,
        )

    async def stop(self, timeout: float = 3.0) -> None:
        """Terminate child process with graceful escalation to SIGKILL."""
        if self._stdout_task is not None:
            self._stdout_task.cancel()
            try:
                await self._stdout_task
            except (asyncio.CancelledError, Exception):
                pass
            self._stdout_task = None

        if self._stderr_task is not None:
            self._stderr_task.cancel()
            try:
                await self._stderr_task
            except (asyncio.CancelledError, Exception):
                pass
            self._stderr_task = None

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

        # Explicit stream and subprocess transport disposal to eliminate unclosed transport ResourceWarnings
        if proc.stdin is not None:
            try:
                proc.stdin.close()
            except Exception:
                pass
        if proc.stdout is not None and hasattr(proc.stdout, "_transport") and proc.stdout._transport is not None:
            try:
                proc.stdout._transport.close()
            except Exception:
                pass
        if proc.stderr is not None and hasattr(proc.stderr, "_transport") and proc.stderr._transport is not None:
            try:
                proc.stderr._transport.close()
            except Exception:
                pass
        if hasattr(proc, "_transport") and proc._transport is not None:
            try:
                proc._transport.close()
            except Exception:
                pass

        # Allow Windows proactor event loop to cleanly process pipe closures
        await asyncio.sleep(0.01)

        logger.debug("Stdio transport stopped", command=self.command)

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and await its response.

        Multiplexes requests over JSON-RPC IDs, allowing concurrent invocations
        without head-of-line blocking.

        Args:
            method: Method name to execute.
            params: Parameters dictionary.
            timeout: Maximum wait time in seconds.

        Returns:
            JSON-RPC response dictionary containing 'result' or 'error'.
        """
        if not self.is_running or not self._process or self._process.stdin is None or self._process.stdout is None:
            recent_stderr = list(self._stderr_buffer)[-5:]
            suffix = f" (stderr: {'; '.join(recent_stderr)})" if recent_stderr else ""
            raise TransportError(f"Process '{self.command}' is not running{suffix}")

        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()

        def _stderr_suffix() -> str:
            recent = list(self._stderr_buffer)[-5:]
            return f" (stderr: {'; '.join(recent)})" if recent else ""

        async with self._write_lock:
            self._req_id += 1
            req_id = self._req_id
            self._pending_futures[req_id] = fut
            payload = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params or {},
            }

            try:
                line_to_send = json.dumps(payload) + "\n"
                self._process.stdin.write(line_to_send.encode("utf-8"))
                await self._process.stdin.drain()
            except (OSError, RuntimeError) as err:
                self._pending_futures.pop(req_id, None)
                raise TransportError(
                    f"Transport communication failure: {err}{_stderr_suffix()}"
                ) from err

        try:
            res = await asyncio.wait_for(fut, timeout=timeout)
            if "id" not in res:
                res["id"] = req_id
            return res
        except asyncio.TimeoutError:
            self._pending_futures.pop(req_id, None)
            return {
                "id": req_id,
                "error": f"Call to '{method}' timed out after {timeout}s{_stderr_suffix()}",
            }

    async def send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send a one-way notification (no response expected)."""
        if not self.is_running or not self._process or self._process.stdin is None:
            raise TransportError(f"Process '{self.command}' is not running")

        async with self._write_lock:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
            }
            line_to_send = json.dumps(payload) + "\n"
            self._process.stdin.write(line_to_send.encode("utf-8"))
            await self._process.stdin.drain()
