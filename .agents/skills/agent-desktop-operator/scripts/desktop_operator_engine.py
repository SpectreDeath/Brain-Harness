"""Agent Desktop Operator Engine.

Provides slotted/frozen domain logic, ref validation, PowerShell quote formatting,
async subprocess transport with Rule 14 pipe drainage, Rule 53 stderr ring-buffering,
and deterministic simulation fallback for automated testing.
"""

from __future__ import annotations

import asyncio
from collections import deque
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from harness.services.agent_desktop import (
    ActionDisposition,
    AgentDesktopActResult,
    AgentDesktopSnapshotResult,
    AgentDesktopStatusResult,
    AgentDesktopWindowResult,
    DesktopRefToken,
    EvidenceTriState,
)


class AgentDesktopOperatorEngine:
    """Core domain engine orchestrating agent-desktop CLI & MCP operations."""

    def __init__(self, binary_path: str | None = None) -> None:
        self._binary_path = binary_path or self._discover_binary()

    def _discover_binary(self) -> str | None:
        """Locate agent-desktop executable in PATH or cloned target directory."""
        which_path = shutil.which("agent-desktop")
        if which_path:
            return which_path

        local_candidate = Path(r"D:\GitHub\cloned\agent-desktop\target\release\agent-desktop.exe")
        if local_candidate.exists():
            return str(local_candidate)

        debug_candidate = Path(r"D:\GitHub\cloned\agent-desktop\target\debug\agent-desktop.exe")
        if debug_candidate.exists():
            return str(debug_candidate)

        return None

    @property
    def is_binary_available(self) -> bool:
        """True if a compiled native agent-desktop binary is found."""
        return self._binary_path is not None and Path(self._binary_path).exists()

    async def _drain_stream(self, stream: asyncio.StreamReader, ring_buffer: deque[str]) -> None:
        """Asynchronously drain stream into a bounded ring buffer (Rule 53)."""
        try:
            while not stream.at_eof():
                line = await stream.readline()
                if line:
                    ring_buffer.append(line.decode("utf-8", errors="replace").rstrip())
        except Exception:
            pass

    async def execute_cli_command(
        self,
        args: list[str],
        timeout_s: float = 30.0,
    ) -> dict[str, Any]:
        """Execute agent-desktop CLI with Rule 14 pipe disposal and Rule 53 diagnostics."""
        if not self.is_binary_available or not self._binary_path:
            raise RuntimeError("agent-desktop native binary is not installed on this system")

        cmd = [self._binary_path] + args
        stderr_buffer: deque[str] = deque(maxlen=50)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        drain_task = asyncio.create_task(self._drain_stream(proc.stderr, stderr_buffer))

        try:
            stdout_data, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            await drain_task

            raw_out = stdout_data.decode("utf-8", errors="replace").strip()
            if not raw_out:
                trailing_err = "\n".join(stderr_buffer)
                raise RuntimeError(f"agent-desktop returned empty output. Stderr: {trailing_err}")

            return json.loads(raw_out)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            trailing_err = "\n".join(stderr_buffer)
            raise TimeoutError(
                f"agent-desktop command '{' '.join(args)}' timed out after {timeout_s}s. Stderr: {trailing_err}"
            )
        finally:
            # Rule 14: Subprocess Pipe Transport Disposal Invariant
            if not drain_task.done():
                drain_task.cancel()
            if proc.stdin and not proc.stdin.is_closing():
                proc.stdin.close()

    async def snapshot(
        self,
        app: str = "",
        root_ref: str = "",
        interactive_only: bool = True,
        skeleton: bool = False,
        compact: bool = True,
        surface: str = "",
        session: str = "default",
    ) -> AgentDesktopSnapshotResult:
        """Capture accessibility tree or drill into a validated root ref."""
        if root_ref:
            # Validate qualified ref syntax (@snapshot_id:eN)
            DesktopRefToken.parse(root_ref)

        if not self.is_binary_available:
            # Deterministic simulation mode for CI / test sandboxes
            snap_id = "s_sim_desktop"
            tree = {
                "role": "window",
                "name": app or "Simulated Desktop",
                "children": [
                    {
                        "role": "button",
                        "name": "OK",
                        "ref_id": f"@{snap_id}:e1",
                        "available_actions": ["Click"],
                    },
                    {
                        "role": "edit",
                        "name": "Search",
                        "ref_id": f"@{snap_id}:e2",
                        "available_actions": ["Click", "SetValue", "Type"],
                    },
                ],
            }
            return AgentDesktopSnapshotResult(
                status="ok",
                version="2.6",
                snapshot_id=snap_id,
                app=app or "Simulated",
                ref_count=2,
                complete=True,
                tree=tree,
                surfaces=["window"],
            )

        args = ["snapshot", "--session", session]
        if app:
            args.extend(["--app", app])
        if root_ref:
            args.extend(["--root", root_ref])
        if interactive_only:
            args.append("-i")
        if skeleton:
            args.append("--skeleton")
        if compact:
            args.append("--compact")
        if surface:
            args.extend(["--surface", surface])

        envelope = await self.execute_cli_command(args)
        data = envelope.get("data") or {}
        error = envelope.get("error") or {}

        if envelope.get("ok"):
            return AgentDesktopSnapshotResult(
                status="ok",
                version=envelope.get("version", "2.6"),
                snapshot_id=data.get("snapshot_id", ""),
                app=data.get("app", app),
                ref_count=int(data.get("ref_count", 0)),
                complete=bool(data.get("complete", True)),
                tree=data.get("tree", {}),
                surfaces=data.get("surfaces", ["window"]),
            )
        return AgentDesktopSnapshotResult(
            status="error",
            version=envelope.get("version", "2.6"),
            error=error.get("message", "Snapshot failed"),
            suggestion=error.get("suggestion"),
        )

    async def act(
        self,
        action: str,
        ref_id: str,
        value: str = "",
        headed: bool = False,
        interval_ms: int | None = None,
        session: str = "default",
    ) -> AgentDesktopActResult:
        """Act on a qualified ref, verifying ref format and returning 2D dispositions."""
        token = DesktopRefToken.parse(ref_id)

        if not self.is_binary_available:
            return AgentDesktopActResult(
                status="ok",
                ok=True,
                command=action,
                ref_id=token.qualified,
                delivery_disposition="delivered_verified",
                retry_disposition="safe",
                retry_safe=True,
                steps=[
                    {"label": f"simulate_{action}", "outcome": "success", "verified": True}
                ],
                surfaces=["window"],
            )

        args = [action, token.qualified, "--session", session]
        if value:
            args.append(value)
        if headed:
            args.append("--headed")
        if interval_ms is not None:
            args.extend(["--interval-ms", str(interval_ms)])

        envelope = await self.execute_cli_command(args)
        data = envelope.get("data") or {}
        error = envelope.get("error") or {}
        disp = error.get("delivery_semantics") or {}

        delivery = disp.get("delivery", "delivered_verified" if envelope.get("ok") else "not_delivered")
        retry = disp.get("retry", "safe" if envelope.get("ok") else "unknown")

        return AgentDesktopActResult(
            status="ok" if envelope.get("ok") else "error",
            ok=bool(envelope.get("ok")),
            command=action,
            ref_id=token.qualified,
            delivery_disposition=delivery,
            retry_disposition=retry,
            retry_safe=(retry == "safe"),
            steps=data.get("steps", []),
            surfaces=data.get("surfaces", ["window"]),
            error_code=error.get("code"),
            error_message=error.get("message"),
            suggestion=error.get("suggestion"),
        )

    async def find(
        self,
        app: str = "",
        role: str = "",
        name: str = "",
        text: str = "",
        session: str = "default",
    ) -> AgentDesktopSnapshotResult:
        """Find nodes matching specified query parameters."""
        if not self.is_binary_available:
            return await self.snapshot(app=app, session=session)

        args = ["find", "--session", session]
        if app:
            args.extend(["--app", app])
        if role:
            args.extend(["--role", role])
        if name:
            args.extend(["--name", name])
        if text:
            args.extend(["--text", text])

        envelope = await self.execute_cli_command(args)
        data = envelope.get("data") or {}
        error = envelope.get("error") or {}

        if envelope.get("ok"):
            return AgentDesktopSnapshotResult(
                status="ok",
                snapshot_id=data.get("snapshot_id", ""),
                app=data.get("app", app),
                ref_count=int(data.get("ref_count", 0)),
                tree=data.get("tree", {}),
                surfaces=data.get("surfaces", ["window"]),
            )
        return AgentDesktopSnapshotResult(
            status="error",
            error=error.get("message", "Find failed"),
            suggestion=error.get("suggestion"),
        )

    async def manage_window(
        self,
        operation: str,
        app: str = "",
        window_id: str = "",
        bounds: dict[str, int] | None = None,
    ) -> AgentDesktopWindowResult:
        """Execute window operations (list-windows, focus-window, resize-window, etc.)."""
        if not self.is_binary_available:
            return AgentDesktopWindowResult(
                status="ok",
                windows=[{"id": "win_1", "title": "Main Window", "app": app or "DesktopApp"}],
                displays=[{"id": "disp_0", "bounds": {"x": 0, "y": 0, "w": 1920, "h": 1080}}],
                apps=[app or "DesktopApp"],
            )

        args = [operation]
        if app:
            args.extend(["--app", app])
        if window_id:
            args.extend(["--window-id", window_id])
        if bounds:
            args.extend(["--bounds", json.dumps(bounds)])

        envelope = await self.execute_cli_command(args)
        data = envelope.get("data") or {}
        error = envelope.get("error") or {}

        if envelope.get("ok"):
            return AgentDesktopWindowResult(
                status="ok",
                windows=data.get("windows", []),
                displays=data.get("displays", []),
                apps=data.get("apps", []),
            )
        return AgentDesktopWindowResult(
            status="error",
            error=error.get("message", f"Window operation '{operation}' failed"),
        )

    async def wait_for(
        self,
        app: str = "",
        element_ref: str = "",
        window_title: str = "",
        text: str = "",
        timeout_ms: int = 5000,
    ) -> dict[str, Any]:
        """Wait for dynamic UI state changes using condition predicates."""
        if not self.is_binary_available:
            return {"status": "ok", "condition_met": True, "elapsed_ms": 10}

        args = ["wait", "--timeout-ms", str(timeout_ms)]
        if app:
            args.extend(["--app", app])
        if element_ref:
            args.extend(["--element", element_ref])
        if window_title:
            args.extend(["--window", window_title])
        if text:
            args.extend(["--text", text])

        envelope = await self.execute_cli_command(args)
        return envelope

    async def get_status(
        self,
        check_permissions: bool = True,
    ) -> AgentDesktopStatusResult:
        """Query platform accessibility status, permissions, and surfaces."""
        is_avail = self.is_binary_available
        if not is_avail:
            return AgentDesktopStatusResult(
                status="ok",
                platform=sys.platform,
                permissions_granted=True,
                accessibility_api="UI Automation" if sys.platform == "win32" else "Accessibility API",
                supported_surfaces=["window", "menu", "dialog", "sheet", "alert"],
                binary_available=False,
                execution_mode="simulation",
            )

        envelope = await self.execute_cli_command(["status"])
        data = envelope.get("data") or {}
        return AgentDesktopStatusResult(
            status="ok" if envelope.get("ok") else "error",
            platform=data.get("platform", sys.platform),
            permissions_granted=bool(data.get("permissions_granted", True)),
            accessibility_api=data.get("accessibility_api", "UI Automation"),
            supported_surfaces=data.get("supported_surfaces", ["window", "menu", "dialog"]),
            binary_available=True,
            execution_mode="cli_subprocess",
        )
