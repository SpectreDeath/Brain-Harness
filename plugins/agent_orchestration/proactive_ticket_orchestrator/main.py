"""Proactive Ticket Orchestrator Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.proactive_ticket import (  # noqa: E402
    PROACTIVE_TICKET_SERVICE_KEY,
    AdmissionRuleSet,
    GateOutcome,
    OutboxDeliveryPlan,
    OutboxReplyItem,
    ProactiveTicketProtocol,
    TicketRouteOutcome,
    TriggerEnvelope,
)

try:
    from .service import DefaultProactiveTicketService
except ImportError:
    from service import DefaultProactiveTicketService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class ProactiveTicketOrchestratorPlugin(HarnessPlugin, ProactiveTicketProtocol):
    """HarnessPlugin providing ProactiveTicketProtocol in the IoC container (Rule 45)."""

    name = "plugin.proactive_ticket_orchestrator"
    version = "1.0.0"
    description = (
        "Proactive ticket orchestrator with deterministic admission gates, "
        "follow-up ownership routing, and serialized outbox planning"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultProactiveTicketService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [PROACTIVE_TICKET_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(PROACTIVE_TICKET_SERVICE_KEY, self, provider=self.name)
        logger.info("ProactiveTicketOrchestratorPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    def evaluate_admission_gate(
        self,
        trigger: TriggerEnvelope,
        rules: AdmissionRuleSet,
        *,
        thread_has_tickets: bool = False,
    ) -> GateOutcome:
        return self._service.evaluate_admission_gate(
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
        return self._service.route_trigger_disposition(
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
        return self._service.plan_outbox_delivery(
            pending_items, in_flight_lanes=in_flight_lanes
        )


plugin = ProactiveTicketOrchestratorPlugin()


# --- Subprocess JSON-RPC Entrypoint Functions ---


def proactive_evaluate_gate(
    trigger_id: str,
    thread_key: str,
    sender_id: str,
    source_kind: str = "github",
    addressed: bool = False,
    is_bot: bool = False,
    allowed_senders: list[str] | None = None,
    accept_mode: str = "on",
) -> dict[str, Any]:
    """Evaluate a trigger envelope against an admission rule set."""
    trigger = TriggerEnvelope(
        trigger_id=trigger_id,
        source_kind=source_kind,
        thread_key=thread_key,
        sender_id=sender_id,
        addressed=addressed,
        is_bot=is_bot,
    )
    rules = AdmissionRuleSet(
        allowed_senders=tuple(allowed_senders or []),
        accept_mode=accept_mode,  # type: ignore[arg-type]
    )
    return asdict(plugin.evaluate_admission_gate(trigger, rules))


def proactive_route_trigger(
    trigger_id: str,
    thread_key: str,
    sender_id: str,
    subscribed_ticket_ids: list[str] | None = None,
    handed_back_by: list[str] | None = None,
    addressed: bool = False,
    is_bot: bool = False,
    allowed_senders: list[str] | None = None,
) -> dict[str, Any]:
    """Route a trigger to owning Ticket Executors or a fresh Eval queue."""
    trigger = TriggerEnvelope(
        trigger_id=trigger_id,
        source_kind="github",
        thread_key=thread_key,
        sender_id=sender_id,
        addressed=addressed,
        is_bot=is_bot,
    )
    rules = AdmissionRuleSet(allowed_senders=tuple(allowed_senders or []))
    return asdict(
        plugin.route_trigger_disposition(
            trigger,
            rules,
            subscribed_ticket_ids=tuple(subscribed_ticket_ids or []),
            handed_back_by=tuple(handed_back_by or []),
        )
    )


def proactive_plan_outbox(
    pending_items: list[dict[str, Any]],
    in_flight_lanes: list[str] | None = None,
) -> dict[str, Any]:
    """Plan serialized outbox delivery per (ticket_id, channel_id) lane."""
    items = tuple(
        OutboxReplyItem(
            message_id=str(item["message_id"]),
            channel_id=str(item["channel_id"]),
            kind=item.get("kind", "reply"),
            text=str(item.get("text", "")),
            ticket_id=item.get("ticket_id"),
            sequence=int(item.get("sequence", 0)),
        )
        for item in pending_items
    )
    plan = plugin.plan_outbox_delivery(
        items, in_flight_lanes=tuple(in_flight_lanes or [])
    )
    return asdict(plan)
