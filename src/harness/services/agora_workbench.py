"""Agora Workbench Service — MCP sidecar lifecycle, unified state graph, gateway/dispatcher & data-lake guard.

Distilled from microsoft/agora-workbench @ a8ae030b:
- Co-located loopback sidecar lifecycle, SIDECAR_HOST/SIDECAR_PORT env locking, kernel Python parity & shutdown escalation
- Unified workflow StateGraph with synthetic cross-server BridgeEdge links, BFS planning & upstream skill disambiguation
- Stateless GatewayServer cascading tool blocks / 60s rate limits & DispatcherServer weighted/least-loaded/affinity routing
- Data Lake PolicyEnforcedCatalogProvider cursor-scope guard / non-enumerable denial masking & 256 MB v2 object transfer
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import re
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

TERMINATION_GRACE_SECONDS: float = 10.0
HEALTH_POLL_INTERVAL_SECONDS: float = 1.0
MAX_TRANSFER_SIZE_BYTES: int = 256 * 1024 * 1024
MAX_STREAMING_ENVELOPE_BYTES: int = 64 * 1024
MAX_CORRELATION_ID_LENGTH: int = 128
STREAMING_TRANSFER_VERSION: str = "2"

LOOPBACK_HOSTS: tuple[str, ...] = ("localhost", "127.0.0.1", "::1")
DISPATCHER_STRATEGIES: tuple[str, ...] = ("round_robin", "least_loaded", "sticky_session")
WORKER_FAILURE_POLICIES: tuple[str, ...] = ("reroute", "error")
CATALOG_POLICY_MODES: tuple[str, ...] = ("homogeneous_source", "per_artifact")
PARALLEL_COMPANION_TOOLS: tuple[str, ...] = ("poll_batch", "collect_batch", "cancel_batch")

_ENV_VAR_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_CORRELATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*\Z")


@dataclass(slots=True, frozen=True)
class SidecarAuditReport:
    """Immutable audit result for a co-located Agora Workbench sidecar specification."""

    name: str
    valid: bool
    resolved_argv: tuple[str, ...]
    base_url: str
    health_url: str
    locked_host: str
    locked_port: int
    env_override_attempted: bool
    loopback_bound: bool
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("SidecarAuditReport.name must be non-empty")


@dataclass(slots=True, frozen=True)
class StateGraphPlanResult:
    """Immutable workflow planning outcome across unified StateGraph tools and bridges."""

    source_state: str
    target_state: str
    reachable: bool
    steps: tuple[dict[str, str], ...]
    bridges_used: tuple[str, ...]
    invalid_bridges: tuple[str, ...] = ()
    duplicate_skills: tuple[str, ...] = ()
    inferred_domains: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_state or not self.target_state:
            raise ValueError("StateGraphPlanResult source_state and target_state must be non-empty")


@dataclass(slots=True, frozen=True)
class ConnectorRoutingDecision:
    """Immutable routing or policy decision for GatewayServer / DispatcherServer calls."""

    mode: str
    allowed: bool
    selected_worker: str | None
    suppressed_companions: tuple[str, ...]
    rate_limited: bool
    affinity_rerouted: bool
    reason: str

    def __post_init__(self) -> None:
        if self.mode not in ("gateway", "dispatcher"):
            raise ValueError(f"Unsupported connector mode: {self.mode!r}")


@dataclass(slots=True, frozen=True)
class DataLakeTransferReport:
    """Immutable authorization scope and v2 streaming envelope validation report."""

    valid: bool
    effective_sources: tuple[str, ...]
    cursor_rejected: bool
    masked_as_not_found: bool
    transfer_size_valid: bool
    envelope_valid: bool
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool):
            raise TypeError("DataLakeTransferReport.valid must be a bool")


@runtime_checkable
class AgoraWorkbenchProtocol(Protocol):
    """Typed IoC service contract for Agora Workbench orchestration and verification."""

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
    ) -> SidecarAuditReport: ...

    def plan_state_graph_workflow(
        self,
        source_state: str,
        target_state: str,
        tools: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        bridges: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
        skills: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> StateGraphPlanResult: ...

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
    ) -> ConnectorRoutingDecision: ...

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
    ) -> DataLakeTransferReport: ...


AGORA_WORKBENCH_SERVICE_KEY: ServiceKey[AgoraWorkbenchProtocol] = ServiceKey("service.agora_mcp_workbench")


class AgoraWorkbenchEngine:
    """Pure-Python domain engine modeling Agora Workbench invariants."""

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
        """Validate a SidecarConfig and enforce SIDECAR_HOST/SIDECAR_PORT address locks."""
        violations: list[str] = []
        clean_name = name.strip()
        if clean_name in set(existing_names):
            violations.append(f"duplicate_sidecar_name:{clean_name}")
        if not command:
            violations.append("empty_command")
        if not _ENV_VAR_RE.match(url_env_var):
            violations.append(f"invalid_url_env_var:{url_env_var}")
        if not (1 <= port <= 65535):
            violations.append(f"invalid_port:{port}")
        if not health_path.startswith("/"):
            violations.append(f"invalid_health_path:{health_path}")
        if use_env_python and not kernel_python_path.strip():
            violations.append("missing_kernel_python_path")

        loopback_bound = host in LOOPBACK_HOSTS
        if not loopback_bound:
            violations.append(f"non_loopback_host:{host}")

        overrides = env_overrides or {}
        env_override_attempted = False
        if "SIDECAR_HOST" in overrides and str(overrides["SIDECAR_HOST"]) != host:
            env_override_attempted = True
        if "SIDECAR_PORT" in overrides and str(overrides["SIDECAR_PORT"]) != str(port):
            env_override_attempted = True

        resolved_argv = (kernel_python_path, *command) if use_env_python else tuple(command)
        base_url = f"http://{host}:{port}"
        normalized_health = health_path if health_path.startswith("/") else f"/{health_path}"
        health_url = f"{base_url}{normalized_health}"

        return SidecarAuditReport(
            name=clean_name,
            valid=(len(violations) == 0),
            resolved_argv=resolved_argv,
            base_url=base_url,
            health_url=health_url,
            locked_host=host,
            locked_port=port,
            env_override_attempted=env_override_attempted,
            loopback_bound=loopback_bound,
            violations=tuple(violations),
        )

    def plan_state_graph_workflow(
        self,
        source_state: str,
        target_state: str,
        tools: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        bridges: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
        skills: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> StateGraphPlanResult:
        """Validate bridge edges and compute a shortest BFS tool path from source to target."""
        normalized_tools: list[dict[str, Any]] = []
        produced_states: set[str] = set()
        required_states: set[str] = set()
        all_tokens: set[str] = set()

        for tool in tools:
            reqs = tuple(tool.get("requires") or tool.get("state_requires") or ())
            prods = tuple(tool.get("produces") or tool.get("state_produces") or ())
            produced_states.update(prods)
            required_states.update(reqs)
            all_tokens.update(reqs)
            all_tokens.update(prods)
            normalized_tools.append(
                {
                    "name": str(tool.get("name", "")),
                    "server": str(tool.get("server") or tool.get("server_name") or ""),
                    "requires": reqs,
                    "produces": prods,
                }
            )

        invalid_bridges: list[str] = []
        for bridge in bridges:
            from_st = str(bridge.get("from_state", ""))
            to_st = str(bridge.get("to_state", ""))
            bridge_label = f"{from_st}->{to_st}"
            if from_st not in produced_states or to_st not in required_states:
                invalid_bridges.append(bridge_label)
                continue
            normalized_tools.append(
                {
                    "name": f"bridge:{bridge_label}",
                    "server": "(bridge)",
                    "requires": (from_st,),
                    "produces": (to_st,),
                }
            )
            all_tokens.add(from_st)
            all_tokens.add(to_st)

        skill_sources: dict[str, set[str]] = defaultdict(set)
        skill_counts: dict[str, int] = defaultdict(int)
        for skill in skills:
            s_name = str(skill.get("name", ""))
            if s_name:
                skill_counts[s_name] += 1
                src = str(skill.get("upstream") or skill.get("server") or skill.get("domain") or "")
                if src:
                    skill_sources[s_name].add(src)
            for st in skill.get("states") or ():
                all_tokens.add(str(st))

        duplicate_skills = tuple(
            sorted(name for name in skill_counts if len(skill_sources[name]) > 1 or skill_counts[name] > 1)
        )
        inferred_domains = tuple(sorted({tok.split(".", 1)[0] for tok in all_tokens if "." in tok}))

        if source_state == target_state:
            return StateGraphPlanResult(
                source_state=source_state,
                target_state=target_state,
                reachable=True,
                steps=(),
                bridges_used=(),
                invalid_bridges=tuple(invalid_bridges),
                duplicate_skills=duplicate_skills,
                inferred_domains=inferred_domains,
            )

        from_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for t in normalized_tools:
            for req in t["requires"]:
                from_state[req].append(t)

        visited: set[str] = {source_state}
        queue: deque[tuple[str, list[dict[str, str]]]] = deque([(source_state, [])])
        found_path: list[dict[str, str]] | None = None

        while queue and found_path is None:
            current, path = queue.popleft()
            for t in from_state.get(current, ()):
                for produced in t["produces"]:
                    if produced in visited:
                        continue
                    step = {
                        "tool": str(t["name"]),
                        "server": str(t["server"]),
                        "from_state": current,
                        "to_state": produced,
                    }
                    new_path = [*path, step]
                    if produced == target_state:
                        found_path = new_path
                        break
                    visited.add(produced)
                    queue.append((produced, new_path))
                if found_path is not None:
                    break

        steps_tuple = tuple(found_path) if found_path is not None else ()
        bridges_used = tuple(s["tool"] for s in steps_tuple if s.get("server") == "(bridge)")

        return StateGraphPlanResult(
            source_state=source_state,
            target_state=target_state,
            reachable=(found_path is not None),
            steps=steps_tuple,
            bridges_used=bridges_used,
            invalid_bridges=tuple(invalid_bridges),
            duplicate_skills=duplicate_skills,
            inferred_domains=inferred_domains,
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
        """Evaluate GatewayServer policy gates or DispatcherServer worker selection."""
        if mode == "gateway":
            blocked_set = set(blocked_tools)
            suppressed = PARALLEL_COMPANION_TOOLS if "parallel_execute" in blocked_set else ()

            for blocked in blocked_tools:
                if blocked in code:
                    return ConnectorRoutingDecision(
                        mode="gateway",
                        allowed=False,
                        selected_worker=None,
                        suppressed_companions=suppressed,
                        rate_limited=False,
                        affinity_rerouted=False,
                        reason=f"blocked_tool:{blocked}",
                    )

            if allowed_tools is not None and len(allowed_tools) > 0:
                if not any(tool in code for tool in allowed_tools):
                    return ConnectorRoutingDecision(
                        mode="gateway",
                        allowed=False,
                        selected_worker=None,
                        suppressed_companions=suppressed,
                        rate_limited=False,
                        affinity_rerouted=False,
                        reason="no_allowed_tool_used",
                    )

            if max_calls_per_minute is not None and calls_in_last_minute >= max_calls_per_minute:
                return ConnectorRoutingDecision(
                    mode="gateway",
                    allowed=False,
                    selected_worker=None,
                    suppressed_companions=suppressed,
                    rate_limited=True,
                    affinity_rerouted=False,
                    reason="rate_limit_exceeded",
                )

            return ConnectorRoutingDecision(
                mode="gateway",
                allowed=True,
                selected_worker=None,
                suppressed_companions=suppressed,
                rate_limited=False,
                affinity_rerouted=False,
                reason="gateway_allowed",
            )

        if mode != "dispatcher":
            raise ValueError(f"Unsupported connector mode: {mode!r}")
        if strategy not in DISPATCHER_STRATEGIES:
            raise ValueError(f"Unsupported dispatcher strategy: {strategy!r}")
        if worker_failure_policy not in WORKER_FAILURE_POLICIES:
            raise ValueError(f"Unsupported worker failure policy: {worker_failure_policy!r}")

        healthy_set = set(healthy_workers)
        affinity_rerouted = False
        if session_affinity_worker:
            if session_affinity_worker in healthy_set:
                return ConnectorRoutingDecision(
                    mode="dispatcher",
                    allowed=True,
                    selected_worker=session_affinity_worker,
                    suppressed_companions=(),
                    rate_limited=False,
                    affinity_rerouted=False,
                    reason="session_affinity_hit",
                )
            if worker_failure_policy == "error":
                return ConnectorRoutingDecision(
                    mode="dispatcher",
                    allowed=False,
                    selected_worker=None,
                    suppressed_companions=(),
                    rate_limited=False,
                    affinity_rerouted=False,
                    reason="affinity_worker_unhealthy_error",
                )
            affinity_rerouted = True

        healthy_candidates = [w for w in workers if str(w.get("name", "")) in healthy_set]
        if not healthy_candidates:
            return ConnectorRoutingDecision(
                mode="dispatcher",
                allowed=False,
                selected_worker=None,
                suppressed_companions=(),
                rate_limited=False,
                affinity_rerouted=affinity_rerouted,
                reason="no_healthy_workers",
            )

        if strategy == "least_loaded":
            chosen = min(healthy_candidates, key=lambda w: int(w.get("active_calls", 0)))
            selected_worker = str(chosen["name"])
        else:
            weighted: list[str] = []
            for w in healthy_candidates:
                weight = max(1, int(w.get("weight", 1)))
                weighted.extend([str(w["name"])] * weight)
            selected_worker = weighted[round_robin_index % len(weighted)]

        return ConnectorRoutingDecision(
            mode="dispatcher",
            allowed=True,
            selected_worker=selected_worker,
            suppressed_companions=(),
            rate_limited=False,
            affinity_rerouted=affinity_rerouted,
            reason="dispatcher_selected",
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
        """Validate PolicyEnforcedCatalogProvider constraints and v2 streaming transfer limits."""
        violations: list[str] = []
        if policy_mode not in CATALOG_POLICY_MODES:
            violations.append(f"invalid_policy_mode:{policy_mode}")
        elif policy_mode == "per_artifact" and not has_per_artifact_enforcer:
            violations.append("per_artifact_requires_enforcer")
        elif policy_mode == "homogeneous_source" and has_per_artifact_enforcer:
            violations.append("homogeneous_source_forbids_enforcer")

        permitted_set = set(permitted_sources)
        effective_sources = tuple(src for src in requested_sources if src in permitted_set)
        cursor_rejected = bool(has_cursor and effective_sources != tuple(requested_sources))
        if cursor_rejected:
            violations.append("cursor_scope_mismatch")

        masked_as_not_found = not target_source_permitted
        if masked_as_not_found:
            violations.append("target_source_masked_not_found")

        transfer_size_valid = 0 <= size_bytes <= MAX_TRANSFER_SIZE_BYTES
        if not transfer_size_valid:
            violations.append(f"transfer_size_out_of_bounds:{size_bytes}")

        envelope_ok = True
        if transfer_version != STREAMING_TRANSFER_VERSION:
            envelope_ok = False
            violations.append(f"unsupported_transfer_version:{transfer_version}")
        if not (0 < envelope_bytes <= MAX_STREAMING_ENVELOPE_BYTES):
            envelope_ok = False
            violations.append(f"invalid_envelope_bytes:{envelope_bytes}")
        if has_duplicate_json_keys:
            envelope_ok = False
            violations.append("duplicate_streaming_json_keys")
        if correlation_id not in (None, ""):
            if len(correlation_id) > MAX_CORRELATION_ID_LENGTH or _CORRELATION_ID_RE.fullmatch(correlation_id) is None:
                envelope_ok = False
                violations.append("invalid_correlation_id")

        return DataLakeTransferReport(
            valid=(len(violations) == 0),
            effective_sources=effective_sources,
            cursor_rejected=cursor_rejected,
            masked_as_not_found=masked_as_not_found,
            transfer_size_valid=transfer_size_valid,
            envelope_valid=envelope_ok,
            violations=tuple(violations),
        )
