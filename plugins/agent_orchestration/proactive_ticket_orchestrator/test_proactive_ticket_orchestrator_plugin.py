"""Contract tests for Proactive Ticket Orchestrator Plugin."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.proactive_ticket import PROACTIVE_TICKET_SERVICE_KEY  # noqa: E402
from plugins.agent_orchestration.proactive_ticket_orchestrator.main import (  # noqa: E402
    plugin,
    proactive_evaluate_gate,
    proactive_plan_outbox,
    proactive_route_trigger,
)


def test_proactive_entrypoints() -> None:
    gate = proactive_evaluate_gate(
        trigger_id="trig-1",
        thread_key="gh:issue:42",
        sender_id="alice",
        addressed=True,
        allowed_senders=["alice"],
    )
    assert gate["admitted"] is True
    assert gate["strength"] == "explicit"

    route = proactive_route_trigger(
        trigger_id="trig-2",
        thread_key="gh:issue:42",
        sender_id="alice",
        subscribed_ticket_ids=["tkt-1"],
    )
    assert route["disposition"] == "deliver_to_ticket"
    assert route["main_session_actions"] == ("stop",)

    plan = proactive_plan_outbox(
        pending_items=[
            {"message_id": "m2", "channel_id": "gh:42", "kind": "reply", "text": "done", "ticket_id": "tkt-1", "sequence": 2},
            {"message_id": "m1", "channel_id": "gh:42", "kind": "acknowledgement", "text": "ack", "ticket_id": "tkt-1", "sequence": 1},
        ]
    )
    assert [m["message_id"] for m in plan["ready_to_send"]] == ["m1"]
    assert [m["message_id"] for m in plan["blocked_behind_head"]] == ["m2"]


@pytest.mark.asyncio
async def test_proactive_plugin_lifecycle_and_validator() -> None:
    context = ServiceContext()
    await plugin.enable(context)
    resolved = context.require(PROACTIVE_TICKET_SERVICE_KEY)
    assert resolved is plugin
    await plugin.disable(context)

    report = PluginValidator().validate_sync(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
