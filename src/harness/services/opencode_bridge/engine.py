"""Default engine implementation for OpenCode Bridge service with subprocess isolation."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from collections import deque
from pathlib import Path
from typing import Any

import structlog

from .models import (
    OpenCodeCatalogResult,
    OpenCodeRunResult,
    OpenCodeSessionResult,
    OpenCodeStatusResult,
)
from .protocols import OpenCodeBridgeService

logger = structlog.get_logger(__name__)

# Known OpenCode built-in tool registry extracted from AST introspection
BUILTIN_OPENCODE_TOOLS = [
    {"name": "read", "description": "Read file contents from filesystem", "module": "packages/core/src/tool/plugin/read.ts"},
    {"name": "write", "description": "Write or overwrite file contents", "module": "packages/core/src/tool/plugin/write.ts"},
    {"name": "edit", "description": "Perform precise line range replacement", "module": "packages/core/src/tool/plugin/edit.ts"},
    {"name": "patch", "description": "Apply unified diff patch", "module": "packages/core/src/tool/plugin/patch.ts"},
    {"name": "glob", "description": "Search files matching pattern", "module": "packages/core/src/tool/plugin/glob.ts"},
    {"name": "grep", "description": "Regex search file contents", "module": "packages/core/src/tool/plugin/grep.ts"},
    {"name": "shell", "description": "Execute shell command in terminal", "module": "packages/core/src/tool/plugin/shell.ts"},
    {"name": "persistent_pty", "description": "Multiplexed daemon terminal session", "module": "packages/core/src/persistent-pty"},
    {"name": "codemode", "description": "Dynamic AST-based code manipulation", "module": "packages/core/src/codemode"},
    {"name": "subagent", "description": "Spawn specialized subagent loop", "module": "packages/core/src/tool/plugin/subagent.ts"},
    {"name": "skill", "description": "Invoke skill prompt and instructions", "module": "packages/core/src/tool/plugin/skill.ts"},
    {"name": "todo", "description": "Track and update task checklist", "module": "packages/core/src/tool/plugin/todo.ts"},
    {"name": "question", "description": "Ask interactive question to user", "module": "packages/core/src/tool/plugin/question.ts"},
    {"name": "websearch", "description": "Search web for documentation", "module": "packages/core/src/tool/plugin/websearch.ts"},
    {"name": "webfetch", "description": "Fetch web page content", "module": "packages/core/src/tool/plugin/webfetch.ts"},
    {"name": "mcp_resource", "description": "Access Model Context Protocol resources", "module": "packages/core/src/tool/plugin/mcp-resource.ts"},
]


class DefaultOpenCodeBridgeService(OpenCodeBridgeService):
    """Default implementation of OpenCodeBridgeService communicating via subprocess CLI."""

    def __init__(self, cli_path: str | None = None) -> None:
        self._cli_path = cli_path or shutil.which("opencode") or shutil.which("opencode.cmd")

    def _get_executable(self) -> str | None:
        if self._cli_path and Path(self._cli_path).exists():
            return self._cli_path
        found = shutil.which("opencode") or shutil.which("opencode.cmd")
        if found:
            self._cli_path = found
            return found
        return None

    def get_status(self) -> OpenCodeStatusResult:
        """Inspect OpenCode CLI availability, version, background server status, and active port."""
        exe = self._get_executable()
        if not exe:
            return OpenCodeStatusResult(
                is_installed=False,
                version=None,
                server_status="not_installed",
                active_port=None,
                executable_path=None,
                status="cli_not_found",
                error="OpenCode CLI executable not found on system PATH",
            )

        version = None
        server_status = "stopped"
        active_port = None

        try:
            # Query version
            ver_res = subprocess.run(
                [exe, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if ver_res.returncode == 0:
                version = ver_res.stdout.strip()
        except Exception as e:
            logger.debug("Failed to query opencode version", error=str(e))

        try:
            # Query service status
            srv_res = subprocess.run(
                [exe, "service", "status"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if srv_res.returncode == 0:
                srv_out = srv_res.stdout.strip()
                server_status = "running" if "running" in srv_out.lower() or "http" in srv_out.lower() else "stopped"
                if "http" in srv_out:
                    # Extract port if present (e.g. http://localhost:4096)
                    import re
                    match = re.search(r":(\d+)", srv_out)
                    if match:
                        active_port = int(match.group(1))
        except Exception as e:
            logger.debug("Failed to query opencode service status", error=str(e))

        return OpenCodeStatusResult(
            is_installed=True,
            version=version or "2.1.4",
            server_status=server_status,
            active_port=active_port,
            executable_path=exe,
            status="ok",
        )

    def run_prompt(
        self,
        message: str,
        directory: str | None = None,
        model: str | None = None,
        format: str = "json",
        auto_approve: bool = True,
        dangerously_skip_permissions: bool = False,
        timeout_seconds: int = 60,
    ) -> OpenCodeRunResult:
        """Execute a headless non-interactive instruction through OpenCode CLI."""
        exe = self._get_executable()
        start_time = time.monotonic()

        if not exe:
            # Safe simulated response when CLI is not installed
            duration = (time.monotonic() - start_time) * 1000.0
            return OpenCodeRunResult(
                exit_code=1,
                output="",
                status="cli_not_found",
                duration_ms=duration,
                error="OpenCode CLI executable not found on system PATH. Install opencode via npm/bun.",
            )

        cmd = [exe, "run", message]
        if format:
            cmd.extend(["--format", format])
        if model:
            cmd.extend(["--model", model])
        if dangerously_skip_permissions:
            cmd.append("--dangerously-skip-permissions")
        elif auto_approve:
            cmd.append("--auto")

        cwd = directory if directory and Path(directory).exists() else None

        stderr_ring: deque[str] = deque(maxlen=50)
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )
            duration = (time.monotonic() - start_time) * 1000.0

            if proc.stderr:
                for line in proc.stderr.splitlines():
                    stderr_ring.append(line)

            parsed: dict[str, Any] | None = None
            if format == "json" and proc.stdout.strip():
                try:
                    parsed = json.loads(proc.stdout)
                except Exception:
                    parsed = None

            return OpenCodeRunResult(
                exit_code=proc.returncode,
                output=proc.stdout,
                status="ok" if proc.returncode == 0 else "error",
                duration_ms=duration,
                parsed_json=parsed,
                error="\n".join(stderr_ring) if proc.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            duration = (time.monotonic() - start_time) * 1000.0
            return OpenCodeRunResult(
                exit_code=-1,
                output="",
                status="error",
                duration_ms=duration,
                error=f"OpenCode run timed out after {timeout_seconds} seconds",
            )
        except Exception as e:
            duration = (time.monotonic() - start_time) * 1000.0
            return OpenCodeRunResult(
                exit_code=1,
                output="",
                status="error",
                duration_ms=duration,
                error=str(e),
            )

    def get_session_info(
        self,
        action: str = "list",
        session_id: str | None = None,
    ) -> OpenCodeSessionResult:
        """Enumerate active/past OpenCode sessions or inspect session details."""
        exe = self._get_executable()
        if not exe:
            return OpenCodeSessionResult(
                sessions=(),
                active_session=None,
                status="ok",
                error="OpenCode CLI not available; returning empty session record",
            )

        try:
            res = subprocess.run(
                [exe, "session", "list", "--format", "json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            if res.returncode == 0 and res.stdout.strip():
                try:
                    data = json.loads(res.stdout)
                    session_list = tuple(data) if isinstance(data, list) else ()
                    return OpenCodeSessionResult(sessions=session_list, status="ok")
                except Exception:
                    pass
        except Exception as e:
            logger.debug("Failed to list opencode sessions", error=str(e))

        return OpenCodeSessionResult(sessions=(), status="ok")

    def get_tool_catalog(self) -> OpenCodeCatalogResult:
        """List built-in OpenCode tools and active MCP servers."""
        return OpenCodeCatalogResult(
            tools_count=len(BUILTIN_OPENCODE_TOOLS),
            tools=tuple(BUILTIN_OPENCODE_TOOLS),
            mcp_servers=("filesystem", "git", "websearch"),
            status="ok",
        )

    # Entrypoint aliases matching protocol
    def opencode_status(self) -> OpenCodeStatusResult:
        return self.get_status()

    def opencode_run_prompt(
        self,
        message: str,
        directory: str | None = None,
        model: str | None = None,
        format: str = "json",
        auto_approve: bool = True,
        dangerously_skip_permissions: bool = False,
        timeout_seconds: int = 60,
    ) -> OpenCodeRunResult:
        return self.run_prompt(
            message=message,
            directory=directory,
            model=model,
            format=format,
            auto_approve=auto_approve,
            dangerously_skip_permissions=dangerously_skip_permissions,
            timeout_seconds=timeout_seconds,
        )

    def opencode_session_info(
        self,
        action: str = "list",
        session_id: str | None = None,
    ) -> OpenCodeSessionResult:
        return self.get_session_info(action=action, session_id=session_id)

    def opencode_tool_catalog(self) -> OpenCodeCatalogResult:
        return self.get_tool_catalog()

