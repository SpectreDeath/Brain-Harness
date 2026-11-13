"""Subprocess-isolated service implementation for Proactive Ticket Orchestrator."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from harness.services.proactive_ticket import (
    AdmissionRuleSet,
    GateOutcome,
    OutboxDeliveryPlan,
    OutboxReplyItem,
    ProactiveTicketEngine,
    ProactiveTicketProtocol,
    TicketRouteOutcome,
    TriggerEnvelope,
)


class DefaultProactiveTicketService(ProactiveTicketProtocol):
    """Service adapter delegating to ProactiveTicketEngine with Rule 14 subprocess runner support."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = ProactiveTicketEngine()

    def evaluate_admission_gate(
        self,
        trigger: TriggerEnvelope,
        rules: AdmissionRuleSet,
        *,
        thread_has_tickets: bool = False,
    ) -> GateOutcome:
        return self._engine.evaluate_admission_gate(
            trigger, rules, thread_has_tickets=thread_has_tickets
        )

    def route_trigger_disposition(
        self,
        trigger: TriggerEnvelope,
        rules: AdmissionRuleSet,
        *,
        subscribed_ticket_ids: tuple[str, ...] = (),
        handed_back_by: tuple[str, ...] = (),
    ) -> TicketRouteOutcome:
        return self._engine.route_trigger_disposition(
            trigger,
            rules,
            subscribed_ticket_ids=subscribed_ticket_ids,
            handed_back_by=handed_back_by,
        )

    def plan_outbox_delivery(
        self,
        pending_items: tuple[OutboxReplyItem, ...],
        *,
        in_flight_lanes: tuple[str, ...] = (),
    ) -> OutboxDeliveryPlan:
        return self._engine.plan_outbox_delivery(
            pending_items, in_flight_lanes=in_flight_lanes
        )

    async def run_cli_subprocess(
        self, args: list[str], *, timeout: float = 30.0
    ) -> dict[str, Any]:
        """Execute the skill CLI script in an isolated subprocess with Rule 14 pipe cleanup."""
        script_path = (
            self._root_dir
            / ".agents"
            / "skills"
            / "proactive-ticket-orchestrator"
            / "scripts"
            / "proactive_ticket_engine.py"
        )
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return {
                "returncode": proc.returncode,
                "stdout": stdout_data.decode("utf-8", errors="replace"),
                "stderr": stderr_data.decode("utf-8", errors="replace"),
            }
        finally:
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                close_fn = getattr(pipe, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:
                        pass
