"""Subprocess-isolated service adapter for Shim Universal AI Harness Governor."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from pathlib import Path
import sys
from typing import Any

from harness.services.shim_harness_governor import (
    DISCOVERY_TIMEOUT_MS,
    MAX_AGENT_STEPS,
    MCP_CALL_TIMEOUT_SECONDS,
    MCP_INIT_TIMEOUT_SECONDS,
    ROUTER_COMPILE_MAX_TOKENS,
    SESSION_SCAN_MAX_BYTES,
    CommandRouterValidationReport,
    McpAndDiscoveryReport,
    SessionAndSkillPolicyReport,
    ShimHarnessGovernorEngine,
    ShimHarnessGovernorProtocol,
    WorkspaceToolSecurityReport,
)


class DefaultShimHarnessGovernorService(ShimHarnessGovernorProtocol):
    """Service adapter delegating to ShimHarnessGovernorEngine with Rule 14 pipe cleanup."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = ShimHarnessGovernorEngine()

    def audit_tool_execution(
        self,
        permission_mode: str,
        tool_level: str,
        workspace_root: str | Path,
        target_path: str | Path,
        tool_schema: dict[str, Any] | None = None,
        file_bytes: int = 0,
        line_count: int = 0,
        has_nul_bytes: bool = False,
        confirmed: bool = False,
        shell_output_bytes: int = 0,
    ) -> WorkspaceToolSecurityReport:
        return self._engine.audit_tool_execution(
            permission_mode=permission_mode,
            tool_level=tool_level,
            workspace_root=workspace_root,
            target_path=target_path,
            tool_schema=tool_schema,
            file_bytes=file_bytes,
            line_count=line_count,
            has_nul_bytes=has_nul_bytes,
            confirmed=confirmed,
            shell_output_bytes=shell_output_bytes,
        )

    def route_command(
        self,
        raw_input: str,
        llm_compiled_command: str | None = None,
        compiler_max_tokens: int = ROUTER_COMPILE_MAX_TOKENS,
    ) -> CommandRouterValidationReport:
        return self._engine.route_command(
            raw_input=raw_input,
            llm_compiled_command=llm_compiled_command,
            compiler_max_tokens=compiler_max_tokens,
        )

    def audit_mcp_and_discovery(
        self,
        server_name: str,
        tool_names: Iterable[str],
        init_timeout_seconds: float = MCP_INIT_TIMEOUT_SECONDS,
        call_timeout_seconds: float = MCP_CALL_TIMEOUT_SECONDS,
        config_payload: dict[str, Any] | None = None,
        discovery_timeout_ms: int = DISCOVERY_TIMEOUT_MS,
        discovered_endpoints: Iterable[str] = (),
    ) -> McpAndDiscoveryReport:
        return self._engine.audit_mcp_and_discovery(
            server_name=server_name,
            tool_names=tool_names,
            init_timeout_seconds=init_timeout_seconds,
            call_timeout_seconds=call_timeout_seconds,
            config_payload=config_payload,
            discovery_timeout_ms=discovery_timeout_ms,
            discovered_endpoints=discovered_endpoints,
        )

    def audit_session_and_skills(
        self,
        session_id: str,
        skill_candidates: Iterable[dict[str, Any]] = (),
        dir_mode: int = 0o700,
        file_mode: int = 0o600,
        scanner_max_bytes: int = SESSION_SCAN_MAX_BYTES,
        max_agent_steps: int = MAX_AGENT_STEPS,
        agents_md_bytes: int = 0,
    ) -> SessionAndSkillPolicyReport:
        return self._engine.audit_session_and_skills(
            session_id=session_id,
            skill_candidates=skill_candidates,
            dir_mode=dir_mode,
            file_mode=file_mode,
            scanner_max_bytes=scanner_max_bytes,
            max_agent_steps=max_agent_steps,
            agents_md_bytes=agents_md_bytes,
        )

    async def run_cli_subprocess(self, args: list[str], *, timeout: float = 30.0) -> dict[str, Any]:
        """Execute the skill CLI wrapper in a subprocess with explicit Rule 14 pipe cleanup."""
        script_path = (
            self._root_dir / ".agents" / "skills" / "shim-harness-governor" / "scripts" / "shim_governor_engine.py"
        )
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "returncode": proc.returncode,
                "stdout": stdout_data.decode("utf-8", errors="replace"),
                "stderr": stderr_data.decode("utf-8", errors="replace"),
            }
        finally:
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                close_fn = getattr(pipe, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:
                        pass
