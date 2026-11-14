"""CLI entrypoint delegating to AgoraWorkbenchEngine (Rule 49 & Rule 57)."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.services.agora_workbench import AgoraWorkbenchEngine  # noqa: E402


def _parse_json_arg(raw: str, default: Any) -> Any:
    if not raw:
        return default
    return json.loads(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agora MCP Workbench Architect Engine CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sidecar = sub.add_parser("audit-sidecar", help="Audit a SidecarConfig and env locks")
    p_sidecar.add_argument("--name", required=True)
    p_sidecar.add_argument("--cmd", nargs="+", default=None)
    p_sidecar.add_argument("--cmd-json", default=None)
    p_sidecar.add_argument("--url-env-var", required=True)
    p_sidecar.add_argument("--port", type=int, required=True)
    p_sidecar.add_argument("--host", default="127.0.0.1")
    p_sidecar.add_argument("--health-path", default="/health")
    p_sidecar.add_argument("--use-env-python", action="store_true", default=True)
    p_sidecar.add_argument("--no-env-python", dest="use_env_python", action="store_false")
    p_sidecar.add_argument("--kernel-python-path", default="/opt/venv/bin/python")
    p_sidecar.add_argument("--env-overrides-json", default="{}")
    p_sidecar.add_argument("--existing-names", nargs="*", default=[])

    p_plan = sub.add_parser("plan-workflow", help="Plan shortest workflow path across StateGraph")
    p_plan.add_argument("--source", required=True)
    p_plan.add_argument("--target", required=True)
    p_plan.add_argument("--tools-json", required=True)
    p_plan.add_argument("--bridges-json", default="[]")
    p_plan.add_argument("--skills-json", default="[]")

    p_conn = sub.add_parser("evaluate-connector", help="Evaluate Gateway or Dispatcher connector policy/routing")
    p_conn.add_argument("--mode", required=True, choices=("gateway", "dispatcher"))
    p_conn.add_argument("--code", default="")
    p_conn.add_argument("--blocked-tools", nargs="*", default=[])
    p_conn.add_argument("--allowed-tools", nargs="*", default=None)
    p_conn.add_argument("--calls-in-last-minute", type=int, default=0)
    p_conn.add_argument("--max-calls-per-minute", type=int, default=None)
    p_conn.add_argument("--workers-json", default="[]")
    p_conn.add_argument("--healthy-workers", nargs="*", default=[])
    p_conn.add_argument("--strategy", default="round_robin")
    p_conn.add_argument("--round-robin-index", type=int, default=0)
    p_conn.add_argument("--session-affinity-worker", default=None)
    p_conn.add_argument("--worker-failure-policy", default="reroute")

    p_dl = sub.add_parser("validate-transfer", help="Validate Data Lake policy scope and v2 streaming transfer")
    p_dl.add_argument("--policy-mode", required=True)
    p_dl.add_argument("--has-per-artifact-enforcer", action="store_true")
    p_dl.add_argument("--requested-sources", nargs="+", required=True)
    p_dl.add_argument("--permitted-sources", nargs="*", default=[])
    p_dl.add_argument("--has-cursor", action="store_true")
    p_dl.add_argument("--target-denied", action="store_true")
    p_dl.add_argument("--size-bytes", type=int, default=1024)
    p_dl.add_argument("--transfer-version", default="2")
    p_dl.add_argument("--envelope-bytes", type=int, default=256)
    p_dl.add_argument("--duplicate-json-keys", action="store_true")
    p_dl.add_argument("--correlation-id", default=None)

    args = parser.parse_args(argv)
    engine = AgoraWorkbenchEngine()

    if args.command == "audit-sidecar":
        cmd = _parse_json_arg(args.cmd_json, []) if args.cmd_json else (args.cmd or [])
        report = engine.audit_sidecar_config(
            name=args.name,
            command=cmd,
            url_env_var=args.url_env_var,
            port=args.port,
            host=args.host,
            health_path=args.health_path,
            use_env_python=args.use_env_python,
            kernel_python_path=args.kernel_python_path,
            env_overrides=_parse_json_arg(args.env_overrides_json, {}),
            existing_names=args.existing_names,
        )
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.valid else 1

    if args.command == "plan-workflow":
        plan = engine.plan_state_graph_workflow(
            source_state=args.source,
            target_state=args.target,
            tools=_parse_json_arg(args.tools_json, []),
            bridges=_parse_json_arg(args.bridges_json, []),
            skills=_parse_json_arg(args.skills_json, []),
        )
        print(json.dumps(asdict(plan), indent=2))
        return 0 if plan.reachable else 1

    if args.command == "evaluate-connector":
        decision = engine.evaluate_connector_call(
            mode=args.mode,
            code=args.code,
            blocked_tools=args.blocked_tools,
            allowed_tools=args.allowed_tools,
            calls_in_last_minute=args.calls_in_last_minute,
            max_calls_per_minute=args.max_calls_per_minute,
            workers=_parse_json_arg(args.workers_json, []),
            healthy_workers=args.healthy_workers,
            strategy=args.strategy,
            round_robin_index=args.round_robin_index,
            session_affinity_worker=args.session_affinity_worker,
            worker_failure_policy=args.worker_failure_policy,
        )
        print(json.dumps(asdict(decision), indent=2))
        return 0 if decision.allowed else 1

    transfer = engine.validate_datalake_and_transfer(
        policy_mode=args.policy_mode,
        has_per_artifact_enforcer=args.has_per_artifact_enforcer,
        requested_sources=args.requested_sources,
        permitted_sources=args.permitted_sources,
        has_cursor=args.has_cursor,
        target_source_permitted=not args.target_denied,
        size_bytes=args.size_bytes,
        transfer_version=args.transfer_version,
        envelope_bytes=args.envelope_bytes,
        has_duplicate_json_keys=args.duplicate_json_keys,
        correlation_id=args.correlation_id,
    )
    print(json.dumps(asdict(transfer), indent=2))
    return 0 if transfer.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
