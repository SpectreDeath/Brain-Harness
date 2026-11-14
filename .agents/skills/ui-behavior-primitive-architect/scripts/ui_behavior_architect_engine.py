"""Headless CLI engine for ui-behavior-primitive-architect skill."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.exists() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from harness.services.ui_behavior_architect import (  # noqa: E402
    UIBehaviorArchitectEngine,
)


def _csv_tuple(raw: str) -> tuple[str, ...]:
    if not raw.strip():
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def main() -> int:
    """Parse arguments and execute UI Behavior Primitive Architect subcommands."""
    parser = argparse.ArgumentParser(description="UI Behavior Primitive Architect CLI Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_audit = subparsers.add_parser("audit-primitive", help="Audit a headless definePrimitive contract.")
    p_audit.add_argument("--name", required=True, help="Primitive name (kebab-case).")
    p_audit.add_argument("--state-keys", default="", help="Comma-separated state keys.")
    p_audit.add_argument("--live-keys", default="", help="Comma-separated live keys.")
    p_audit.add_argument("--controlled-keys", default=None, help="Optional comma-separated controlled keys.")
    p_audit.add_argument("--provided-options", default="", help="Comma-separated initial option keys.")
    p_audit.add_argument("--api-methods", default="", help="Comma-separated API methods.")
    p_audit.add_argument("--agent-actions", default="", help="Comma-separated declared agent.actions.")
    p_audit.add_argument("--asleep", action="store_true", help="Whether primitive defines an asleep predicate.")
    p_audit.add_argument("--as-prop", action="store_true", help="Flag disallowed `as` prop usage.")

    p_step = subparsers.add_parser("agent-step", help="Evaluate WebMCP agent bridge step admissibility.")
    p_step.add_argument("--ref", required=True, help="Target component ref.")
    p_step.add_argument("--component", required=True, help="Component kind.")
    p_step.add_argument("--action", required=True, help="Requested action or synonym.")
    p_step.add_argument("--available-actions", default="", help="Comma-separated available actions.")
    p_step.add_argument("--value", default="", help="Raw value for redaction check.")
    p_step.add_argument("--confirm", default=None, help="Optional data-agent-confirm prompt.")
    p_step.add_argument("--hidden", action="store_true", help="Marked data-agent-hidden.")
    p_step.add_argument("--secret", action="store_true", help="Marked data-agent-secret.")
    p_step.add_argument("--approved", action="store_true", help="Explicit human approval given.")
    p_step.add_argument("--tool", default="act", help="WebMCP tool name (snapshot, act, query).")

    p_tri = subparsers.add_parser("tri-modal", help="Run WAI-ARIA, SSR isolation, and RTL direction checks.")
    p_tri.add_argument("--pattern", required=True, help="WAI-ARIA APG pattern name.")
    p_tri.add_argument("--aria-violations", default="", help="Comma-separated ARIA findings.")
    p_tri.add_argument("--ssr-globals", default="", help="Comma-separated SSR globals accessed.")
    p_tri.add_argument("--ltr-focus", default="", help="Focused element key in LTR.")
    p_tri.add_argument("--rtl-focus", default="", help="Focused element key in RTL.")
    p_tri.add_argument("--ltr-state", default="{}", help="JSON state object in LTR.")
    p_tri.add_argument("--rtl-state", default="{}", help="JSON state object in RTL.")

    p_scope = subparsers.add_parser("expert-scope", help="Compute framework expert review routing from changed paths.")
    p_scope.add_argument("--files", required=True, help="Comma-separated changed repository file paths.")

    args = parser.parse_args()
    engine = UIBehaviorArchitectEngine()

    if args.command == "audit-primitive":
        ctrl = _csv_tuple(args.controlled_keys) if args.controlled_keys is not None else None
        report = engine.audit_primitive_definition(
            args.name,
            state_keys=_csv_tuple(args.state_keys),
            live_keys=_csv_tuple(args.live_keys),
            controlled_keys=ctrl,
            provided_options=_csv_tuple(args.provided_options),
            api_methods=_csv_tuple(args.api_methods),
            agent_actions=_csv_tuple(args.agent_actions),
            has_asleep_predicate=args.asleep,
            has_render_as_prop=args.as_prop,
        )
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.valid else 1

    if args.command == "agent-step":
        decision = engine.evaluate_agent_bridge_step(
            args.ref,
            args.component,
            args.action,
            available_actions=_csv_tuple(args.available_actions),
            value=args.value,
            confirm_attr=args.confirm,
            hidden=args.hidden,
            secret=args.secret,
            person_approved=True if args.approved else None,
            tool_name=args.tool,
        )
        print(json.dumps(asdict(decision), indent=2))
        return 0

    if args.command == "tri-modal":
        ltr_state = json.loads(args.ltr_state)
        rtl_state = json.loads(args.rtl_state)
        report = engine.evaluate_tri_modal_check(
            args.pattern,
            aria_violations=_csv_tuple(args.aria_violations),
            ssr_globals_accessed=_csv_tuple(args.ssr_globals),
            ltr_focus=args.ltr_focus,
            rtl_focus=args.rtl_focus,
            ltr_state=ltr_state,
            rtl_state=rtl_state,
        )
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.passed else 1

    if args.command == "expert-scope":
        routes = engine.plan_expert_scope(_csv_tuple(args.files))
        print(json.dumps([asdict(r) for r in routes], indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
