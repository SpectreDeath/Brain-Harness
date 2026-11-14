"""Thin CLI wrapper delegating Shim Harness Governor checks to the micro-kernel service."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.exists() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from harness.services.shim_harness_governor import (  # noqa: E402
    DISCOVERY_TIMEOUT_MS,
    MCP_CALL_TIMEOUT_SECONDS,
    MCP_INIT_TIMEOUT_SECONDS,
    ROUTER_COMPILE_MAX_TOKENS,
    ShimHarnessGovernorEngine,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shim Harness Governor CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    tool_p = sub.add_parser("audit-tool")
    tool_p.add_argument("--mode", required=True, choices=("ask", "read-only", "auto"))
    tool_p.add_argument("--level", required=True, choices=("read", "write", "shell", "external"))
    tool_p.add_argument("--root", required=True)
    tool_p.add_argument("--target", required=True)
    tool_p.add_argument("--confirmed", action="store_true")

    route_p = sub.add_parser("route-command")
    route_p.add_argument("--input", required=True)
    route_p.add_argument("--compiled")
    route_p.add_argument("--max-tokens", type=int, default=ROUTER_COMPILE_MAX_TOKENS)

    mcp_p = sub.add_parser("audit-mcp")
    mcp_p.add_argument("--server", required=True)
    mcp_p.add_argument("--tools", nargs="*", default=[])
    mcp_p.add_argument("--init-timeout", type=float, default=MCP_INIT_TIMEOUT_SECONDS)
    mcp_p.add_argument("--call-timeout", type=float, default=MCP_CALL_TIMEOUT_SECONDS)
    mcp_p.add_argument("--discovery-ms", type=int, default=DISCOVERY_TIMEOUT_MS)

    sess_p = sub.add_parser("audit-session")
    sess_p.add_argument("--session-id", required=True)
    sess_p.add_argument("--agents-bytes", type=int, default=0)

    args = parser.parse_args(argv)
    engine = ShimHarnessGovernorEngine()

    if args.cmd == "audit-tool":
        res = engine.audit_tool_execution(
            permission_mode=args.mode,
            tool_level=args.level,
            workspace_root=args.root,
            target_path=args.target,
            confirmed=args.confirmed,
        )
    elif args.cmd == "route-command":
        res = engine.route_command(
            raw_input=args.input,
            llm_compiled_command=args.compiled,
            compiler_max_tokens=args.max_tokens,
        )
    elif args.cmd == "audit-mcp":
        res = engine.audit_mcp_and_discovery(
            server_name=args.server,
            tool_names=args.tools,
            init_timeout_seconds=args.init_timeout,
            call_timeout_seconds=args.call_timeout,
            discovery_timeout_ms=args.discovery_ms,
        )
    else:
        res = engine.audit_session_and_skills(
            session_id=args.session_id,
            agents_md_bytes=args.agents_bytes,
        )

    print(json.dumps(asdict(res), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
