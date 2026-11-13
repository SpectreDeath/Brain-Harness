"""Proactive Ticket Orchestrator Service — deterministic gate, mandate routing, and serialized outbox planning.

Distilled from deepseek-ai/dsh-superagent-prototype:
- Two-layer admission gate (explicit | inferred | ignore) with bot-list bounds
- Follow-up ownership routing for subscribed Threads vs fresh Eval queues
- Per-(ticket_id, channel_id) serialized outbox delivery planning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

AdmissionStrength = Literal["explicit", "inferred", "ignore"]
AcceptMode = Literal["on", "off", "record_only"]
TriggerKind = Literal["mention", "direct", "comment", "ci", "system"]


@dataclass(slots=True, frozen=True)
class TriggerEnvelope:
    """Immutable normalized event from an external Source (GitHub, Feishu, etc.)."""

    trigger_id: str
    source_kind: str
    thread_key: str
    sender_id: str
    kind: TriggerKind = "comment"
    addressed: bool = False
    is_bot: bool = False
    body: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.trigger_id.strip():
            raise ValueError("trigger_id must be non-empty")
        if not self.thread_key.strip():
            raise ValueError("thread_key must be non-empty")
        if not self.sender_id.strip():
            raise ValueError("sender_id must be non-empty")


@dataclass(slots=True, frozen=True)
class AdmissionRuleSet:
    """Per-source deterministic admission matrix and allowlists."""

    allowed_senders: tuple[str, ...] = ()
    allowed_bots: tuple[str, ...] = ()
    accept_mode: AcceptMode = "on"
    listed_unaddressed: Literal["inferred", "ignore"] = "inferred"
    unlisted_addressed: Literal["explicit", "inferred", "ignore"] = "ignore"
    unlisted_unaddressed: Literal["inferred", "ignore"] = "ignore"
    policy_version: str = "v1"

    def __post_init__(self) -> None:
        if self.accept_mode not in ("on", "off", "record_only"):
            raise ValueError(f"Invalid accept_mode: {self.accept_mode!r}")
        if not self.policy_version.strip():
            raise ValueError("policy_version must be non-empty")


@dataclass(slots=True, frozen=True)
class GateOutcome:
    """Result of evaluating a TriggerEnvelope against an AdmissionRuleSet."""

    trigger_id: str
    strength: AdmissionStrength
    admitted: bool
    reason: str
    policy_version: str
    record_only: bool = False


@dataclass(slots=True, frozen=True)
class TicketRouteOutcome:
    """Routing disposition for a Trigger relative to active Thread Subscriptions."""

    trigger_id: str
    thread_key: str
    disposition: Literal["deliver_to_ticket", "queue_eval", "drop_ignored"]
    owner_ticket_ids: tuple[str, ...] = ()
    eval_strength: AdmissionStrength = "ignore"
    main_session_actions: tuple[str, ...] = ()
    reason: str = ""


@dataclass(slots=True, frozen=True)
class OutboxReplyItem:
    """Immutable outbound channel message scheduled by the outbox delivery planner."""

    message_id: str
    channel_id: str
    kind: Literal["acknowledgement", "reply", "notice"]
    text: str
    ticket_id: str | None = None
    sequence: int = 0

    def __post_init__(self) -> None:
        if not self.message_id.strip():
            raise ValueError("message_id must be non-empty")
        if not self.channel_id.strip():
            raise ValueError("channel_id must be non-empty")


@dataclass(slots=True, frozen=True)
class OutboxDeliveryPlan:
    """Ordered outbox delivery batches preserving per-(ticket_id, channel_id) sequence."""

    ready_to_send: tuple[OutboxReplyItem, ...] = ()
    blocked_behind_head: tuple[OutboxReplyItem, ...] = ()
    lane_keys: tuple[str, ...] = ()


class ProactiveTicketEngine:
    """Pure, deterministic domain engine for proactive ticket orchestration."""

    def evaluate_admission_gate(
        self,
        trigger: TriggerEnvelope,
        rules: AdmissionRuleSet,
        *,
        thread_has_tickets: bool = False,
    ) -> GateOutcome:
        """Classify trigger strength deterministically before semantic LLM assessment."""
        if trigger.is_bot:
            if trigger.sender_id in rules.allowed_bots and (
                trigger.addressed or trigger.kind == "ci"
            ):
                strength: AdmissionStrength = "inferred"
                reason = "allowed_bot_candidate"
            else:
                return GateOutcome(
                    trigger_id=trigger.trigger_id,
                    strength="ignore",
                    admitted=False,
                    reason="unlisted_or_unaddressed_bot",
                    policy_version=rules.policy_version,
                )
        elif trigger.sender_id in rules.allowed_senders:
            if trigger.addressed or thread_has_tickets:
                strength = "explicit"
                reason = "allowed_sender_explicit"
            else:
                strength = rules.listed_unaddressed
                reason = "allowed_sender_unaddressed_matrix"
        else:
            if trigger.addressed:
                strength = rules.unlisted_addressed
                reason = "unlisted_addressed_matrix"
            elif thread_has_tickets:
                strength = "inferred"
                reason = "unlisted_followup_on_ticket_thread"
            else:
                strength = rules.unlisted_unaddressed
                reason = "unlisted_unaddressed_matrix"

        if strength == "ignore":
            return GateOutcome(
                trigger_id=trigger.trigger_id,
                strength="ignore",
                admitted=False,
                reason=reason,
                policy_version=rules.policy_version,
            )

        if strength == "inferred" and rules.accept_mode == "off":
            return GateOutcome(
                trigger_id=trigger.trigger_id,
                strength="ignore",
                admitted=False,
                reason="inferred_blocked_when_accept_mode_off",
                policy_version=rules.policy_version,
            )

        return GateOutcome(
            trigger_id=trigger.trigger_id,
            strength=strength,
            admitted=True,
            reason=reason,
            policy_version=rules.policy_version,
            record_only=(strength == "inferred" and rules.accept_mode == "record_only"),
        )

    def route_trigger_disposition(
        self,
        trigger: TriggerEnvelope,
        rules: AdmissionRuleSet,
        *,
        subscribed_ticket_ids: tuple[str, ...] = (),
        handed_back_by: tuple[str, ...] = (),
    ) -> TicketRouteOutcome:
        """Route a trigger to owning Ticket Executors or to a fresh Eval queue."""
        active_owners = tuple(
            tid for tid in subscribed_ticket_ids if tid not in handed_back_by
        )
        gate = self.evaluate_admission_gate(
            trigger, rules, thread_has_tickets=bool(active_owners)
        )

        # Human follow-ups on a thread with live/resumable tickets belong to those Executors.
        if active_owners and not trigger.is_bot:
            return TicketRouteOutcome(
                trigger_id=trigger.trigger_id,
                thread_key=trigger.thread_key,
                disposition="deliver_to_ticket",
                owner_ticket_ids=active_owners,
                eval_strength=gate.strength,
                main_session_actions=("stop",) if gate.admitted else (),
                reason="owned_by_subscribed_ticket_executor",
            )

        if gate.admitted:
            return TicketRouteOutcome(
                trigger_id=trigger.trigger_id,
                thread_key=trigger.thread_key,
                disposition="queue_eval",
                owner_ticket_ids=(),
                eval_strength=gate.strength,
                main_session_actions=("accept", "attach", "ignore", "stop"),
                reason=gate.reason,
            )

        return TicketRouteOutcome(
            trigger_id=trigger.trigger_id,
            thread_key=trigger.thread_key,
            disposition="drop_ignored",
            owner_ticket_ids=(),
            eval_strength="ignore",
            main_session_actions=(),
            reason=gate.reason,
        )

    def plan_outbox_delivery(
        self,
        pending_items: tuple[OutboxReplyItem, ...],
        *,
        in_flight_lanes: tuple[str, ...] = (),
    ) -> OutboxDeliveryPlan:
        """Serialize outbound replies per (ticket_id, channel_id) while allowing parallel independent lanes."""
        ordered = sorted(pending_items, key=lambda item: (item.sequence, item.message_id))
        busy_lanes: set[str] = set(in_flight_lanes)
        ready: list[OutboxReplyItem] = []
        blocked: list[OutboxReplyItem] = []
        seen_lanes: list[str] = []

        for item in ordered:
            if item.ticket_id:
                lane = f"{item.ticket_id}::{item.channel_id}"
                if lane not in seen_lanes:
                    seen_lanes.append(lane)
                if lane in busy_lanes:
                    blocked.append(item)
                else:
                    busy_lanes.add(lane)
                    ready.append(item)
            else:
                ready.append(item)

        return OutboxDeliveryPlan(
            ready_to_send=tuple(ready),
            blocked_behind_head=tuple(blocked),
            lane_keys=tuple(seen_lanes),
        )


@runtime_checkable
class ProactiveTicketProtocol(Protocol):
    """Typed IoC service protocol for proactive ticket orchestration."""

    def evaluate_admission_gate(
        self,
        trigger: TriggerEnvelope,
        rules: AdmissionRuleSet,
        *,
        thread_has_tickets: bool = False,
    ) -> GateOutcome: ...

    def route_trigger_disposition(
        self,
        trigger: TriggerEnvelope,
        rules: AdmissionRuleSet,
        *,
        subscribed_ticket_ids: tuple[str, ...] = (),
        handed_back_by: tuple[str, ...] = (),
    ) -> TicketRouteOutcome: ...

    def plan_outbox_delivery(
        self,
        pending_items: tuple[OutboxReplyItem, ...],
        *,
        in_flight_lanes: tuple[str, ...] = (),
    ) -> OutboxDeliveryPlan: ...


PROACTIVE_TICKET_SERVICE_KEY: ServiceKey[ProactiveTicketProtocol] = ServiceKey(
    "service.proactive_ticket_orchestrator"
)

__all__ = [
    "AcceptMode",
    "AdmissionRuleSet",
    "AdmissionStrength",
    "GateOutcome",
    "OutboxDeliveryPlan",
    "OutboxReplyItem",
    "PROACTIVE_TICKET_SERVICE_KEY",
    "ProactiveTicketEngine",
    "ProactiveTicketProtocol",
    "TicketRouteOutcome",
    "TriggerEnvelope",
    "TriggerKind",
]
