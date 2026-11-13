"""Thin CLI wrapper delegating to harness.services.multi_bot_desk (Rule 49, Rule 57)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.services.multi_bot_desk import (  # noqa: E402
    BotHopDispatchRequest,
    McpApprovalRequest,
    MultiBotDeskEngine,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-Bot Desk Orchestrator CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    hop_p = sub.add_parser("hop", help="Evaluate bot-to-bot hop dispatch")
    hop_p.add_argument("--from-bot", required=True)
    hop_p.add_argument("--to-bot", required=True)
    hop_p.add_argument("--message", default="")
    hop_p.add_argument("--depth", type=int, default=0)
    hop_p.add_argument("--max-depth", type=int, default=3)

    app_p = sub.add_parser("approval", help="Evaluate in-band MCP tool approval")
    app_p.add_argument("--bot-id", required=True)
    app_p.add_argument("--tool-name", required=True)
    app_p.add_argument("--read-only", action="store_true")
    app_p.add_argument("--always-allowed", default="")
    app_p.add_argument("--user-interrupted", action="store_true")

    lease_p = sub.add_parser("lease", help="Allocate isolated bot desk lease")
    lease_p.add_argument("--bot-id", required=True)
    lease_p.add_argument("--primary", action="store_true")
    lease_p.add_argument("--occupied-displays", default="")

    args = parser.parse_args(argv)
    engine = MultiBotDeskEngine()

    if args.command == "hop":
        req = BotHopDispatchRequest(
            from_bot_id=args.from_bot,
            to_bot_id=args.to_bot,
            message_text=args.message,
            current_depth=args.depth,
            max_depth=args.max_depth,
        )
        print(json.dumps(asdict(engine.evaluate_bot_hop_dispatch(req)), indent=2))
        return 0

    if args.command == "approval":
        allowed = tuple(s.strip() for s in args.always_allowed.split(",") if s.strip())
        req = McpApprovalRequest(
            bot_id=args.bot_id,
            tool_name=args.tool_name,
            is_read_only=args.read_only,
            always_allowed_tools=allowed,
            user_interrupted=args.user_interrupted,
        )
        print(json.dumps(asdict(engine.evaluate_mcp_tool_approval(req)), indent=2))
        return 0

    if args.command == "lease":
        occupied = tuple(
            int(s.strip()) for s in args.occupied_displays.split(",") if s.strip()
        )
        lease = engine.allocate_bot_desk_lease(
            args.bot_id,
            is_primary=args.primary,
            occupied_displays=occupied,
        )
        print(json.dumps(asdict(lease), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
