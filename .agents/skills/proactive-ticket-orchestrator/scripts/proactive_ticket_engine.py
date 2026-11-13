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
    OutboxReplyItem,
    ProactiveTicketEngine,
    TriggerEnvelope,
)


def _split_csv(raw: str) -> tuple[str, ...]:
    return tuple(s.strip() for s in raw.split(",") if s.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Proactive Ticket Orchestrator CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd_name, help_text in (
        ("gate", "Evaluate deterministic admission gate"),
        ("route", "Route trigger disposition and follow-up ownership"),
    ):
        p = sub.add_parser(cmd_name, help=help_text)
        p.add_argument("--trigger-id", required=True)
        p.add_argument("--thread-key", required=True)
        p.add_argument("--sender-id", required=True)
        p.add_argument("--source-kind", default="github")
        p.add_argument("--addressed", action="store_true")
        p.add_argument("--is-bot", action="store_true")
        p.add_argument("--allowed-senders", default="")
        p.add_argument("--accept-mode", default="on", choices=("on", "off", "record_only"))
        if cmd_name == "route":
            p.add_argument("--subscribed-tickets", default="")
            p.add_argument("--handed-back-by", default="")

    outbox_p = sub.add_parser("outbox", help="Plan serialized per-(ticket, channel) outbox delivery")
    outbox_p.add_argument("--items-json", required=True, help="JSON list of OutboxReplyItem dicts")
    outbox_p.add_argument("--in-flight-lanes", default="")

    args = parser.parse_args(argv)
    engine = ProactiveTicketEngine()

    if args.command in ("gate", "route"):
        trigger = TriggerEnvelope(
            trigger_id=args.trigger_id,
            source_kind=args.source_kind,
            thread_key=args.thread_key,
            sender_id=args.sender_id,
            addressed=args.addressed,
            is_bot=args.is_bot,
        )
        rules = AdmissionRuleSet(
            allowed_senders=_split_csv(args.allowed_senders),
            accept_mode=args.accept_mode,
        )
        if args.command == "gate":
            outcome = engine.evaluate_admission_gate(trigger, rules)
        else:
            outcome = engine.route_trigger_disposition(
                trigger,
                rules,
                subscribed_ticket_ids=_split_csv(args.subscribed_tickets),
                handed_back_by=_split_csv(args.handed_back_by),
            )
        print(json.dumps(asdict(outcome), indent=2))
        return 0

    if args.command == "outbox":
        raw_items = json.loads(args.items_json)
        items = tuple(OutboxReplyItem(**entry) for entry in raw_items)
        plan = engine.plan_outbox_delivery(
            items, in_flight_lanes=_split_csv(args.in_flight_lanes)
        )
        print(json.dumps(asdict(plan), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
