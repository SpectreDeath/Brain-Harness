"""Shim Universal AI Harness Governor Service (Balanov/shim @ 3b5acfdf)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

__all__ = [
    "AGENTS_MD_MAX_BYTES",
    "AGENT_MAX_TOKENS",
    "ALLOWED_ROUTER_COMMANDS",
    "DISCOVERY_TIMEOUT_MS",
    "FILE_READ_MAX_BYTES",
    "FILE_READ_MAX_LINES",
    "MAX_AGENT_STEPS",
    "MCP_CALL_TIMEOUT_SECONDS",
    "MCP_INIT_TIMEOUT_SECONDS",
    "MCP_PROTOCOL_VERSION",
    "MCP_TOOL_MAX_LEN",
    "PERMISSION_MODES",
    "ROUTER_COMPILE_MAX_TOKENS",
    "SESSION_ID_MAX_LEN",
    "SESSION_SCAN_MAX_BYTES",
    "SHELL_OUTPUT_MAX_BYTES",
    "SHELL_TIMEOUT_SECONDS",
    "SHIM_HARNESS_GOVERNOR_KEY",
    "SKILL_MAX_BYTES",
    "SKILL_PRECEDENCE_TIERS",
    "SUPPORTED_PROVIDER_APIS",
    "TOOL_LEVELS",
    "CommandRouterValidationReport",
    "McpAndDiscoveryReport",
    "SessionAndSkillPolicyReport",
    "ShimHarnessGovernorEngine",
    "ShimHarnessGovernorProtocol",
    "WorkspaceToolSecurityReport",
]

TOOL_LEVELS: tuple[str, ...] = ("read", "write", "shell", "external")
PERMISSION_MODES: tuple[str, ...] = ("ask", "read-only", "auto")
SUPPORTED_PROVIDER_APIS: tuple[str, ...] = ("openai", "anthropic")
MAX_AGENT_STEPS: int = 16
AGENT_MAX_TOKENS: int = 8192
AGENTS_MD_MAX_BYTES: int = 64 << 10
FILE_READ_MAX_BYTES: int = 2 << 20
FILE_READ_MAX_LINES: int = 2000
SHELL_OUTPUT_MAX_BYTES: int = 1 << 20
SHELL_TIMEOUT_SECONDS: int = 120
ROUTER_COMPILE_MAX_TOKENS: int = 300
MCP_PROTOCOL_VERSION: str = "2025-03-26"
MCP_INIT_TIMEOUT_SECONDS: float = 30.0
MCP_CALL_TIMEOUT_SECONDS: float = 60.0
MCP_TOOL_MAX_LEN: int = 64
DISCOVERY_TIMEOUT_MS: int = 900
SESSION_ID_MAX_LEN: int = 64
SESSION_SCAN_MAX_BYTES: int = 16 << 20
SKILL_MAX_BYTES: int = 1 << 20
SKILL_PRECEDENCE_TIERS: tuple[str, ...] = (
    "global",
    ".shim/skills",
    ".agents/skills",
    ".claude/skills",
)
ALLOWED_ROUTER_COMMANDS: tuple[str, ...] = (
    "/help",
    "/status",
    "/doctor",
    "/models",
    "/skills",
    "/mcps",
    "/tools",
    "/discover",
    "/model",
    "/skill",
    "/mcp",
    "/session",
    "/router",
    "/permissions",
)

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MCP_SANITIZE_RE = re.compile(r"[^A-Za-z0-9_-]")
_USE_MODEL_RE = re.compile(
    r"^(?:use|switch to|select)\s+(?:the\s+)?(?:model\s+)?([A-Za-z0-9._:/-]+)$",
    re.IGNORECASE,
)

_DETERMINISTIC_READ_ONLY: dict[str, str] = {
    "help": "/help",
    "show help": "/help",
    "commands": "/help",
    "status": "/status",
    "show status": "/status",
    "doctor": "/doctor",
    "health": "/doctor",
    "models": "/models",
    "list models": "/models",
    "skills": "/skills",
    "list skills": "/skills",
    "tools": "/tools",
    "list tools": "/tools",
    "mcps": "/mcps",
    "mcp list": "/mcps",
    "list mcps": "/mcps",
    "discover": "/discover",
    "discover models": "/discover",
}

_DETERMINISTIC_MUTATING: dict[str, str] = {
    "discover and add": "/discover --add",
    "add discovered models": "/discover --add",
    "new session": "/session new",
    "start new session": "/session new",
    "reset session": "/session new",
}

_READ_ONLY_SINGLETON_CMDS = frozenset(
    {"/help", "/status", "/doctor", "/models", "/skills", "/mcps", "/tools", "/discover"}
)


def _resolve_with_ancestor_symlinks(path: Path) -> Path:
    """Resolve symlinks through the target or its deepest existing ancestor."""
    candidate = Path(os.path.abspath(str(path)))
    pending_parts: list[str] = []
    probe = candidate
    while not probe.exists():
        parent = probe.parent
        if parent == probe:
            break
        pending_parts.append(probe.name)
        probe = parent
    resolved_base = Path(os.path.realpath(str(probe)))
    for part in reversed(pending_parts):
        resolved_base = resolved_base / part
    return resolved_base


def _is_within(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_router_command(command_text: str) -> tuple[bool, bool, tuple[str, ...], str | None]:
    """Validate tokenized slash command against Shim's closed allowlist."""
    try:
        args = tuple(shlex.split(command_text, posix=True))
    except ValueError as exc:
        return False, False, (), f"unparseable router command: {exc}"
    if not args or not args[0].startswith("/"):
        return False, False, args, "router command must start with /"
    cmd = args[0]
    if cmd in _READ_ONLY_SINGLETON_CMDS:
        if cmd == "/discover" and args == ("/discover", "--add"):
            return True, True, args, None
        if len(args) != 1:
            return False, False, args, f"unexpected arguments for {cmd}"
        return True, False, args, None
    if cmd == "/model" and len(args) >= 2:
        sub = args[1]
        if sub == "test":
            return True, False, args, None
        if sub in {"use", "add", "remove"}:
            return True, True, args, None
    elif cmd == "/skill":
        if len(args) == 3 and args[1] == "show":
            return True, False, args, None
        if len(args) >= 2 and args[1] in {"add", "remove"}:
            return True, True, args, None
    elif cmd == "/mcp":
        if len(args) == 2 and args[1] == "list":
            return True, False, args, None
        if len(args) == 3 and args[1] == "tools":
            return True, False, args, None
        if len(args) >= 2 and args[1] in {"add", "remove"}:
            return True, True, args, None
    elif cmd == "/session" and len(args) == 2:
        if args[1] == "list":
            return True, False, args, None
        if args[1] == "new":
            return True, True, args, None
    elif cmd == "/router":
        if len(args) == 2 and args[1] in {"off", "show"}:
            return True, args[1] == "off", args, None
        if len(args) == 3 and args[1] == "use":
            return True, True, args, None
    elif cmd == "/permissions" and len(args) == 2 and args[1] in PERMISSION_MODES:
        return True, True, args, None
    return False, False, args, f"router produced a disallowed command: {command_text}"


@dataclass(slots=True, frozen=True)
class WorkspaceToolSecurityReport:
    """Result of Shim 4-tier tool permission, closed schema, and symlink containment check."""

    allowed: bool
    permission_mode: str
    tool_level: str
    requires_confirmation: bool
    within_workspace: bool
    resolved_path: str
    schema_closed: bool
    file_size_ok: bool
    line_count_ok: bool
    has_nul_bytes: bool
    violations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.permission_mode not in PERMISSION_MODES:
            raise ValueError(f"permission_mode must be one of {PERMISSION_MODES}")
        if self.tool_level not in TOOL_LEVELS:
            raise ValueError(f"tool_level must be one of {TOOL_LEVELS}")


@dataclass(slots=True, frozen=True)
class CommandRouterValidationReport:
    """Result of deterministic-first and allowlisted slash command routing."""

    raw_input: str
    resolved_command: str
    matched_deterministically: bool
    allowlisted: bool
    mutating: bool
    compiler_max_tokens: int
    args: tuple[str, ...]
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.compiler_max_tokens <= 0:
            raise ValueError("compiler_max_tokens must be positive")


@dataclass(slots=True, frozen=True)
class McpAndDiscoveryReport:
    """Audit result for MCP client tool namespacing, timeouts, env-ref config, and local discovery."""

    mcp_protocol_version: str
    normalized_tools: tuple[str, ...]
    collisions: tuple[str, ...]
    max_tool_len: int
    init_timeout_seconds: float
    call_timeout_seconds: float
    config_version: int
    uses_env_key_only: bool
    config_mode_valid: bool
    discovery_timeout_ms: int
    discovered_endpoints: tuple[str, ...]
    violations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.max_tool_len <= 0 or self.discovery_timeout_ms <= 0:
            raise ValueError("max_tool_len and discovery_timeout_ms must be positive")


@dataclass(slots=True, frozen=True)
class SessionAndSkillPolicyReport:
    """Audit result for cryptographic JSONL session store, step budget, and 4-tier skill precedence."""

    session_id: str
    session_id_valid: bool
    dir_mode: int
    file_mode: int
    scanner_max_bytes: int
    max_agent_steps: int
    agents_md_bytes: int
    agents_md_truncated: bool
    winning_skills: tuple[str, ...]
    rejected_skills: tuple[str, ...]
    total_skill_files: int
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.total_skill_files < 0:
            raise ValueError("total_skill_files must be non-negative")


@runtime_checkable
class ShimHarnessGovernorProtocol(Protocol):
    """Protocol for Shim Universal AI Harness Governor policies."""

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
    ) -> WorkspaceToolSecurityReport: ...

    def route_command(
        self,
        raw_input: str,
        llm_compiled_command: str | None = None,
        compiler_max_tokens: int = ROUTER_COMPILE_MAX_TOKENS,
    ) -> CommandRouterValidationReport: ...

    def audit_mcp_and_discovery(
        self,
        server_name: str,
        tool_names: Iterable[str],
        init_timeout_seconds: float = MCP_INIT_TIMEOUT_SECONDS,
        call_timeout_seconds: float = MCP_CALL_TIMEOUT_SECONDS,
        config_payload: dict[str, Any] | None = None,
        discovery_timeout_ms: int = DISCOVERY_TIMEOUT_MS,
        discovered_endpoints: Iterable[str] = (),
    ) -> McpAndDiscoveryReport: ...

    def audit_session_and_skills(
        self,
        session_id: str,
        skill_candidates: Iterable[dict[str, Any]] = (),
        dir_mode: int = 0o700,
        file_mode: int = 0o600,
        scanner_max_bytes: int = SESSION_SCAN_MAX_BYTES,
        max_agent_steps: int = MAX_AGENT_STEPS,
        agents_md_bytes: int = 0,
    ) -> SessionAndSkillPolicyReport: ...


SHIM_HARNESS_GOVERNOR_KEY: ServiceKey[ShimHarnessGovernorProtocol] = ServiceKey("service.shim_harness_governor")


class ShimHarnessGovernorEngine(ShimHarnessGovernorProtocol):
    """Pure Python governor distilled from Balanov/shim architectural invariants."""

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
        """Audit 4-tier permissions, closed JSON schema, ancestor symlink containment, and I/O limits."""
        if permission_mode not in PERMISSION_MODES:
            raise ValueError(f"Unsupported permission_mode: {permission_mode}")
        if tool_level not in TOOL_LEVELS:
            raise ValueError(f"Unsupported tool_level: {tool_level}")

        violations: list[str] = []
        root_resolved = _resolve_with_ancestor_symlinks(Path(workspace_root))
        raw_target = Path(target_path)
        candidate = raw_target if raw_target.is_absolute() else root_resolved / raw_target
        target_resolved = _resolve_with_ancestor_symlinks(candidate)
        within_ws = _is_within(root_resolved, target_resolved)
        if not within_ws:
            violations.append(f"path escapes workspace root: {target_resolved}")

        schema_closed = True
        if tool_schema is not None:
            schema_closed = tool_schema.get("additionalProperties") is False
            if not schema_closed:
                violations.append("tool schema must set additionalProperties=false")

        file_size_ok = file_bytes <= FILE_READ_MAX_BYTES
        if not file_size_ok:
            violations.append(f"file size {file_bytes} exceeds {FILE_READ_MAX_BYTES} bytes")
        line_count_ok = line_count <= FILE_READ_MAX_LINES
        if not line_count_ok:
            violations.append(f"line count {line_count} exceeds {FILE_READ_MAX_LINES} lines")
        if has_nul_bytes:
            violations.append("binary file with NUL bytes rejected")
        if shell_output_bytes > SHELL_OUTPUT_MAX_BYTES:
            violations.append(f"shell output {shell_output_bytes} exceeds {SHELL_OUTPUT_MAX_BYTES} bytes")

        requires_confirmation = permission_mode == "ask" and tool_level != "read"
        if permission_mode == "read-only" and tool_level != "read":
            violations.append(f"read-only mode denies '{tool_level}' tool")
        elif requires_confirmation and not confirmed:
            violations.append(f"ask mode requires confirmation for '{tool_level}' tool")

        return WorkspaceToolSecurityReport(
            allowed=not violations,
            permission_mode=permission_mode,
            tool_level=tool_level,
            requires_confirmation=requires_confirmation,
            within_workspace=within_ws,
            resolved_path=str(target_resolved),
            schema_closed=schema_closed,
            file_size_ok=file_size_ok,
            line_count_ok=line_count_ok,
            has_nul_bytes=has_nul_bytes,
            violations=tuple(violations),
        )

    def route_command(
        self,
        raw_input: str,
        llm_compiled_command: str | None = None,
        compiler_max_tokens: int = ROUTER_COMPILE_MAX_TOKENS,
    ) -> CommandRouterValidationReport:
        """Route operator text deterministically first, then enforce closed slash allowlist."""
        normalized = " ".join(raw_input.strip().split())
        lower = normalized.lower()
        reasons: list[str] = []
        matched_det = False
        candidate = ""

        if lower in _DETERMINISTIC_READ_ONLY:
            candidate = _DETERMINISTIC_READ_ONLY[lower]
            matched_det = True
        elif lower in _DETERMINISTIC_MUTATING:
            candidate = _DETERMINISTIC_MUTATING[lower]
            matched_det = True
        else:
            use_match = _USE_MODEL_RE.match(normalized)
            if use_match:
                candidate = f"/model use {use_match.group(1)}"
                matched_det = True
            elif normalized.startswith("/"):
                candidate = normalized
                matched_det = True

        if not matched_det:
            if llm_compiled_command is not None:
                cleaned = llm_compiled_command.strip()
                if cleaned.startswith("```"):
                    lines = [line for line in cleaned.splitlines() if not line.strip().startswith("```")]
                    cleaned = " ".join(lines).strip()
                candidate = cleaned
            else:
                reasons.append("deterministic router miss and no compiled command supplied")

        if compiler_max_tokens > ROUTER_COMPILE_MAX_TOKENS:
            reasons.append(f"compiler_max_tokens {compiler_max_tokens} exceeds {ROUTER_COMPILE_MAX_TOKENS}")

        if candidate:
            allowlisted, mutating, args, err = _validate_router_command(candidate)
            if err:
                reasons.append(err)
        else:
            allowlisted, mutating, args = False, False, ()

        return CommandRouterValidationReport(
            raw_input=raw_input,
            resolved_command=candidate,
            matched_deterministically=matched_det,
            allowlisted=allowlisted and not reasons,
            mutating=mutating,
            compiler_max_tokens=compiler_max_tokens,
            args=args,
            reasons=tuple(reasons),
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
        """Normalize MCP tool names with <=64-char collision detection and audit env-ref config."""
        violations: list[str] = []
        seen: dict[str, str] = {}
        normalized_tools: list[str] = []
        collisions: list[str] = []

        safe_server = _MCP_SANITIZE_RE.sub("_", server_name.strip())
        if not safe_server:
            violations.append("server_name must contain identifier characters")

        for raw_tool in tool_names:
            safe_tool = _MCP_SANITIZE_RE.sub("_", raw_tool.strip())
            full = f"mcp_{safe_server}_{safe_tool}"[:MCP_TOOL_MAX_LEN]
            if full in seen and seen[full] != raw_tool:
                collisions.append(f"{full} <- ({seen[full]}, {raw_tool})")
            else:
                seen[full] = raw_tool
                normalized_tools.append(full)

        if collisions:
            violations.append(f"MCP tool name collisions after sanitization: {', '.join(collisions)}")
        if init_timeout_seconds > MCP_INIT_TIMEOUT_SECONDS or init_timeout_seconds <= 0:
            violations.append(
                f"init_timeout_seconds {init_timeout_seconds} must be within (0, {MCP_INIT_TIMEOUT_SECONDS}]"
            )
        if call_timeout_seconds > MCP_CALL_TIMEOUT_SECONDS or call_timeout_seconds <= 0:
            violations.append(
                f"call_timeout_seconds {call_timeout_seconds} must be within (0, {MCP_CALL_TIMEOUT_SECONDS}]"
            )
        if discovery_timeout_ms > DISCOVERY_TIMEOUT_MS:
            violations.append(f"discovery_timeout_ms {discovery_timeout_ms} exceeds {DISCOVERY_TIMEOUT_MS}ms budget")

        payload = config_payload or {}
        config_version = int(payload.get("version", 1))
        if config_version != 1:
            violations.append(f"unsupported config version {config_version}; expected 1")
        uses_env_key_only = not bool(payload.get("api_key") or payload.get("raw_secret"))
        if not uses_env_key_only:
            violations.append("raw api_key/secret prohibited; store api_key_env name only")

        perm = str(payload.get("permissions", "ask"))
        api_kind = str(payload.get("api", "openai"))
        config_mode_valid = perm in PERMISSION_MODES and api_kind in SUPPORTED_PROVIDER_APIS
        if perm not in PERMISSION_MODES:
            violations.append(f"invalid permissions setting: {perm}")
        if api_kind not in SUPPORTED_PROVIDER_APIS:
            violations.append(f"unsupported provider api: {api_kind}")

        endpoints = tuple(sorted({ep.strip() for ep in discovered_endpoints if ep.strip()}))

        return McpAndDiscoveryReport(
            mcp_protocol_version=MCP_PROTOCOL_VERSION,
            normalized_tools=tuple(normalized_tools),
            collisions=tuple(collisions),
            max_tool_len=MCP_TOOL_MAX_LEN,
            init_timeout_seconds=float(init_timeout_seconds),
            call_timeout_seconds=float(call_timeout_seconds),
            config_version=config_version,
            uses_env_key_only=uses_env_key_only,
            config_mode_valid=config_mode_valid,
            discovery_timeout_ms=discovery_timeout_ms,
            discovered_endpoints=endpoints,
            violations=tuple(violations),
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
        """Validate session ID/perms, step/AGENTS.md budgets, and 4-tier last-wins skill loading."""
        reasons: list[str] = []
        session_id_valid = bool(_SESSION_ID_RE.match(session_id))
        if not session_id_valid:
            reasons.append("session_id must be 1..64 characters of [A-Za-z0-9_-]")
        if dir_mode != 0o700:
            reasons.append(f"session dir_mode {oct(dir_mode)} must be 0o700")
        if file_mode != 0o600:
            reasons.append(f"session/config file_mode {oct(file_mode)} must be 0o600")
        if scanner_max_bytes > SESSION_SCAN_MAX_BYTES or scanner_max_bytes <= 0:
            reasons.append(f"scanner_max_bytes must be within (0, {SESSION_SCAN_MAX_BYTES}]")
        if max_agent_steps > MAX_AGENT_STEPS or max_agent_steps <= 0:
            reasons.append(f"max_agent_steps {max_agent_steps} must be within (0, {MAX_AGENT_STEPS}]")

        agents_md_truncated = agents_md_bytes > AGENTS_MD_MAX_BYTES
        tier_rank = {tier: idx for idx, tier in enumerate(SKILL_PRECEDENCE_TIERS)}
        winners: dict[str, tuple[int, str]] = {}
        rejected: list[str] = []
        total_files = 0

        for cand in skill_candidates:
            total_files += 1
            name = str(cand.get("name", "")).strip()
            tier = str(cand.get("tier", "")).strip()
            size_bytes = int(cand.get("size_bytes", 0))
            has_closed_frontmatter = bool(cand.get("has_closed_frontmatter", True))

            if not name or tier not in tier_rank:
                rejected.append(name or f"unknown@{tier}")
                reasons.append(f"invalid skill candidate name/tier: {name!r} ({tier!r})")
                continue
            if size_bytes > SKILL_MAX_BYTES:
                rejected.append(name)
                reasons.append(f"skill '{name}' exceeds {SKILL_MAX_BYTES} bytes")
                continue
            if not has_closed_frontmatter:
                rejected.append(name)
                reasons.append(f"skill '{name}' missing closed YAML frontmatter")
                continue

            rank = tier_rank[tier]
            prev = winners.get(name)
            if prev is None or rank >= prev[0]:
                winners[name] = (rank, tier)

        winning_labels = tuple(f"{name}@{winners[name][1]}" for name in sorted(winners))
        return SessionAndSkillPolicyReport(
            session_id=session_id,
            session_id_valid=session_id_valid,
            dir_mode=dir_mode,
            file_mode=file_mode,
            scanner_max_bytes=scanner_max_bytes,
            max_agent_steps=max_agent_steps,
            agents_md_bytes=agents_md_bytes,
            agents_md_truncated=agents_md_truncated,
            winning_skills=winning_labels,
            rejected_skills=tuple(rejected),
            total_skill_files=total_files,
            reasons=tuple(reasons),
        )
