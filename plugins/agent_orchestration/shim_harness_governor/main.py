"""Shim Universal AI Harness Governor Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

from collections.abc import Iterable
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
from harness.services.shim_harness_governor import (  # noqa: E402
    DISCOVERY_TIMEOUT_MS,
    MAX_AGENT_STEPS,
    MCP_CALL_TIMEOUT_SECONDS,
    MCP_INIT_TIMEOUT_SECONDS,
    ROUTER_COMPILE_MAX_TOKENS,
    SESSION_SCAN_MAX_BYTES,
    SHIM_HARNESS_GOVERNOR_KEY,
    CommandRouterValidationReport,
    McpAndDiscoveryReport,
    SessionAndSkillPolicyReport,
    ShimHarnessGovernorProtocol,
    WorkspaceToolSecurityReport,
)

try:
    from .service import DefaultShimHarnessGovernorService
except ImportError:
    from service import DefaultShimHarnessGovernorService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class ShimHarnessGovernorPlugin(HarnessPlugin, ShimHarnessGovernorProtocol):
    """HarnessPlugin providing ShimHarnessGovernorProtocol in the IoC container (Rule 45)."""

    name = "plugin.shim_harness_governor"
    version = "1.0.0"
    description = (
        "Shim Universal AI Harness Governor plugin providing 4-tier tool gating, "
        "deterministic-first allowlisted routing, MCP namespacing, and layered skill governance"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultShimHarnessGovernorService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [SHIM_HARNESS_GOVERNOR_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(SHIM_HARNESS_GOVERNOR_KEY, self, provider=self.name)
        logger.info("ShimHarnessGovernorPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

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
        return self._service.audit_tool_execution(
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
        return self._service.route_command(
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
        return self._service.audit_mcp_and_discovery(
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
        return self._service.audit_session_and_skills(
            session_id=session_id,
            skill_candidates=skill_candidates,
            dir_mode=dir_mode,
            file_mode=file_mode,
            scanner_max_bytes=scanner_max_bytes,
            max_agent_steps=max_agent_steps,
            agents_md_bytes=agents_md_bytes,
        )


plugin = ShimHarnessGovernorPlugin()


def shim_audit_tool_execution(
    permission_mode: str,
    tool_level: str,
    workspace_root: str,
    target_path: str,
    tool_schema: dict[str, Any] | None = None,
    file_bytes: int = 0,
    line_count: int = 0,
    has_nul_bytes: bool = False,
    confirmed: bool = False,
    shell_output_bytes: int = 0,
) -> dict[str, Any]:
    """Audit tool permission level, closed schema, and symlink-safe workspace containment."""
    return asdict(
        plugin.audit_tool_execution(
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
    )


def shim_route_command(
    raw_input: str,
    llm_compiled_command: str | None = None,
    compiler_max_tokens: int = ROUTER_COMPILE_MAX_TOKENS,
) -> dict[str, Any]:
    """Route natural-language command deterministically before closed-allowlist verification."""
    return asdict(
        plugin.route_command(
            raw_input=raw_input,
            llm_compiled_command=llm_compiled_command,
            compiler_max_tokens=compiler_max_tokens,
        )
    )


def shim_audit_mcp_discovery(
    server_name: str,
    tool_names: list[str],
    init_timeout_seconds: float = MCP_INIT_TIMEOUT_SECONDS,
    call_timeout_seconds: float = MCP_CALL_TIMEOUT_SECONDS,
    config_payload: dict[str, Any] | None = None,
    discovery_timeout_ms: int = DISCOVERY_TIMEOUT_MS,
    discovered_endpoints: list[str] | None = None,
) -> dict[str, Any]:
    """Sanitize MCP tool identifiers and audit env-ref configuration and 900ms discovery."""
    return asdict(
        plugin.audit_mcp_and_discovery(
            server_name=server_name,
            tool_names=tool_names,
            init_timeout_seconds=init_timeout_seconds,
            call_timeout_seconds=call_timeout_seconds,
            config_payload=config_payload,
            discovery_timeout_ms=discovery_timeout_ms,
            discovered_endpoints=tuple(discovered_endpoints or ()),
        )
    )


def shim_audit_session_skills(
    session_id: str,
    skill_candidates: list[dict[str, Any]] | None = None,
    dir_mode: int = 0o700,
    file_mode: int = 0o600,
    scanner_max_bytes: int = SESSION_SCAN_MAX_BYTES,
    max_agent_steps: int = MAX_AGENT_STEPS,
    agents_md_bytes: int = 0,
) -> dict[str, Any]:
    """Audit JSONL session security bounds, step caps, and 4-tier skill precedence."""
    return asdict(
        plugin.audit_session_and_skills(
            session_id=session_id,
            skill_candidates=tuple(skill_candidates or ()),
            dir_mode=dir_mode,
            file_mode=file_mode,
            scanner_max_bytes=scanner_max_bytes,
            max_agent_steps=max_agent_steps,
            agents_md_bytes=agents_md_bytes,
        )
    )
