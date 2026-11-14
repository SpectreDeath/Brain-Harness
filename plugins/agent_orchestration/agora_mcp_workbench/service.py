"""Subprocess-isolated service adapter for Agora MCP Workbench."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

from harness.services.agora_workbench import (
    AgoraWorkbenchEngine,
    AgoraWorkbenchProtocol,
    ConnectorRoutingDecision,
    DataLakeTransferReport,
    SidecarAuditReport,
    StateGraphPlanResult,
)


class DefaultAgoraWorkbenchService(AgoraWorkbenchProtocol):
    """Service adapter delegating to AgoraWorkbenchEngine with Rule 14 subprocess pipe cleanup."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = AgoraWorkbenchEngine()

    def audit_sidecar_config(
        self,
        name: str,
        command: list[str] | tuple[str, ...],
        url_env_var: str,
        port: int,
        host: str = "127.0.0.1",
        health_path: str = "/health",
        use_env_python: bool = True,
        kernel_python_path: str = "/opt/venv/bin/python",
        env_overrides: dict[str, str] | None = None,
        existing_names: list[str] | tuple[str, ...] = (),
    ) -> SidecarAuditReport:
        return self._engine.audit_sidecar_config(
            name=name,
            command=command,
            url_env_var=url_env_var,
            port=port,
            host=host,
            health_path=health_path,
            use_env_python=use_env_python,
            kernel_python_path=kernel_python_path,
            env_overrides=env_overrides,
            existing_names=existing_names,
        )

    def plan_state_graph_workflow(
        self,
        source_state: str,
        target_state: str,
        tools: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        bridges: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
        skills: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> StateGraphPlanResult:
        return self._engine.plan_state_graph_workflow(
            source_state=source_state,
            target_state=target_state,
            tools=tools,
            bridges=bridges,
            skills=skills,
        )

    def evaluate_connector_call(
        self,
        mode: str,
        code: str = "",
        blocked_tools: list[str] | tuple[str, ...] = (),
        allowed_tools: list[str] | tuple[str, ...] | None = None,
        calls_in_last_minute: int = 0,
        max_calls_per_minute: int | None = None,
        workers: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        healthy_workers: list[str] | tuple[str, ...] = (),
        strategy: str = "round_robin",
        round_robin_index: int = 0,
        session_affinity_worker: str | None = None,
        worker_failure_policy: str = "reroute",
    ) -> ConnectorRoutingDecision:
        return self._engine.evaluate_connector_call(
            mode=mode,
            code=code,
            blocked_tools=blocked_tools,
            allowed_tools=allowed_tools,
            calls_in_last_minute=calls_in_last_minute,
            max_calls_per_minute=max_calls_per_minute,
            workers=workers,
            healthy_workers=healthy_workers,
            strategy=strategy,
            round_robin_index=round_robin_index,
            session_affinity_worker=session_affinity_worker,
            worker_failure_policy=worker_failure_policy,
        )

    def validate_datalake_and_transfer(
        self,
        policy_mode: str,
        has_per_artifact_enforcer: bool,
        requested_sources: list[str] | tuple[str, ...],
        permitted_sources: list[str] | tuple[str, ...],
        has_cursor: bool = False,
        target_source_permitted: bool = True,
        size_bytes: int = 1024,
        transfer_version: str = "2",
        envelope_bytes: int = 256,
        has_duplicate_json_keys: bool = False,
        correlation_id: str | None = None,
    ) -> DataLakeTransferReport:
        return self._engine.validate_datalake_and_transfer(
            policy_mode=policy_mode,
            has_per_artifact_enforcer=has_per_artifact_enforcer,
            requested_sources=requested_sources,
            permitted_sources=permitted_sources,
            has_cursor=has_cursor,
            target_source_permitted=target_source_permitted,
            size_bytes=size_bytes,
            transfer_version=transfer_version,
            envelope_bytes=envelope_bytes,
            has_duplicate_json_keys=has_duplicate_json_keys,
            correlation_id=correlation_id,
        )

    async def run_cli_subprocess(self, args: list[str], *, timeout: float = 30.0) -> dict[str, Any]:
        """Execute the skill CLI engine in a subprocess with explicit Rule 14 pipe closure."""
        script_path = (
            self._root_dir
            / ".agents"
            / "skills"
            / "agora-mcp-workbench-architect"
            / "scripts"
            / "agora_workbench_engine.py"
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
