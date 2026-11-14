"""Agora MCP Workbench Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.agora_workbench import (  # noqa: E402
    AGORA_WORKBENCH_SERVICE_KEY,
    AgoraWorkbenchProtocol,
    ConnectorRoutingDecision,
    DataLakeTransferReport,
    SidecarAuditReport,
    StateGraphPlanResult,
)

try:
    from .service import DefaultAgoraWorkbenchService
except ImportError:
    from service import DefaultAgoraWorkbenchService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class AgoraMcpWorkbenchPlugin(HarnessPlugin, AgoraWorkbenchProtocol):
    """HarnessPlugin providing AgoraWorkbenchProtocol in the IoC container (Rule 45)."""

    name = "plugin.agora_mcp_workbench"
    version = "1.0.0"
    description = (
        "Agora Workbench MCP sidecar lifecycle auditor, unified StateGraph planner, "
        "Gateway/Dispatcher router, and Data Lake/v2 streaming transfer validator"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultAgoraWorkbenchService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGORA_WORKBENCH_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(AGORA_WORKBENCH_SERVICE_KEY, self, provider=self.name)
        logger.info("AgoraMcpWorkbenchPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

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
        return self._service.audit_sidecar_config(
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
        return self._service.plan_state_graph_workflow(
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
        return self._service.evaluate_connector_call(
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
        return self._service.validate_datalake_and_transfer(
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


plugin = AgoraMcpWorkbenchPlugin()


def agora_audit_sidecar(
    name: str,
    command: list[str],
    url_env_var: str,
    port: int,
    host: str = "127.0.0.1",
    health_path: str = "/health",
    use_env_python: bool = True,
    kernel_python_path: str = "/opt/venv/bin/python",
    env_overrides: dict[str, str] | None = None,
    existing_names: list[str] | None = None,
) -> dict[str, Any]:
    """Validate SidecarConfig and SIDECAR_HOST/PORT locking."""
    return asdict(
        plugin.audit_sidecar_config(
            name=name,
            command=command,
            url_env_var=url_env_var,
            port=port,
            host=host,
            health_path=health_path,
            use_env_python=use_env_python,
            kernel_python_path=kernel_python_path,
            env_overrides=env_overrides,
            existing_names=tuple(existing_names or ()),
        )
    )


def agora_plan_state_workflow(
    source_state: str,
    target_state: str,
    tools: list[dict[str, Any]],
    bridges: list[dict[str, str]] | None = None,
    skills: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Plan shortest BFS workflow path across StateGraph tools and bridges."""
    return asdict(
        plugin.plan_state_graph_workflow(
            source_state=source_state,
            target_state=target_state,
            tools=tools,
            bridges=tuple(bridges or ()),
            skills=tuple(skills or ()),
        )
    )


def agora_evaluate_connector(
    mode: str,
    code: str = "",
    blocked_tools: list[str] | None = None,
    allowed_tools: list[str] | None = None,
    calls_in_last_minute: int = 0,
    max_calls_per_minute: int | None = None,
    workers: list[dict[str, Any]] | None = None,
    healthy_workers: list[str] | None = None,
    strategy: str = "round_robin",
    round_robin_index: int = 0,
    session_affinity_worker: str | None = None,
    worker_failure_policy: str = "reroute",
) -> dict[str, Any]:
    """Evaluate GatewayServer policies or DispatcherServer worker selection."""
    return asdict(
        plugin.evaluate_connector_call(
            mode=mode,
            code=code,
            blocked_tools=tuple(blocked_tools or ()),
            allowed_tools=allowed_tools,
            calls_in_last_minute=calls_in_last_minute,
            max_calls_per_minute=max_calls_per_minute,
            workers=tuple(workers or ()),
            healthy_workers=tuple(healthy_workers or ()),
            strategy=strategy,
            round_robin_index=round_robin_index,
            session_affinity_worker=session_affinity_worker,
            worker_failure_policy=worker_failure_policy,
        )
    )


def agora_validate_datalake_transfer(
    policy_mode: str,
    has_per_artifact_enforcer: bool,
    requested_sources: list[str],
    permitted_sources: list[str],
    has_cursor: bool = False,
    target_source_permitted: bool = True,
    size_bytes: int = 1024,
    transfer_version: str = "2",
    envelope_bytes: int = 256,
    has_duplicate_json_keys: bool = False,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Validate PolicyEnforcedCatalogProvider scope/cursor guards and v2 object transfer limits."""
    return asdict(
        plugin.validate_datalake_and_transfer(
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
    )
