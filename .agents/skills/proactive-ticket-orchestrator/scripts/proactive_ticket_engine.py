"""Thin CLI wrapper delegating to harness.services.proactive_ticket (Rule 49, Rule 57)."""

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

from harness.services.proactive_ticket import (  # noqa: E402
    AdmissionRuleSet,
    ProactiveTicketEngine,
    TriggerEnvelope,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Proactive Ticket Orchestrator CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    gate_p = sub.add_parser("gate", help="Evaluate deterministic admission gate")
    gate_p.add_argument("--trigger-id", required=True)
    gate_p.add_argument("--thread-key", required=True)
    gate_p.add_argument("--sender-id", required=True)
    gate_p.add_argument("--source-kind", default="github")
    gate_p.add_argument("--addressed", action="store_true")
    gate_p.add_argument("--is-bot", action="store_true")
    gate_p.add_argument("--allowed-senders", default="")
    gate_p.add_argument("--accept-mode", default="on", choices=("on", "off", "record_only"))

    args = parser.parse_args(argv)
    engine = ProactiveTicketEngine()

    if args.command == "gate":
        trigger = TriggerEnvelope(
            trigger_id=args.trigger_id,
            source_kind=args.source_kind,
            thread_key=args.thread_key,
            sender_id=args.sender_id,
            addressed=args.addressed,
            is_bot=args.is_bot,
        )
        rules = AdmissionRuleSet(
            allowed_senders=tuple(s.strip() for s in args.allowed_senders.split(",") if s.strip()),
            accept_mode=args.accept_mode,
        )
        outcome = engine.evaluate_admission_gate(trigger, rules)
        print(json.dumps(asdict(outcome), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
