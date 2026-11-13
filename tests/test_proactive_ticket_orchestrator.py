"""Contract tests for Proactive Ticket Orchestrator skill, models, and service."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.services.proactive_ticket import (
    PROACTIVE_TICKET_SERVICE_KEY,
    AdmissionRuleSet,
    OutboxReplyItem,
    ProactiveTicketEngine,
    ProactiveTicketProtocol,
    TriggerEnvelope,
)


@pytest.mark.unit
class TestProactiveTicketModelsAndEngine:
    def test_frozen_slotted_immutability(self) -> None:
        """Verify Rule 12 & Rule 43 immutability via direct attribute assignment."""
        trigger = TriggerEnvelope(
            trigger_id="t-1",
            source_kind="github",
            thread_key="gh:issue:10",
            sender_id="alice",
            addressed=True,
        )
        with pytest.raises((AttributeError, TypeError)):
            trigger.sender_id = "bob"  # type: ignore[misc]

        rules = AdmissionRuleSet(allowed_senders=("alice",))
        with pytest.raises((AttributeError, TypeError)):
            rules.accept_mode = "off"  # type: ignore[misc]

    def test_admission_gate_bot_ceiling_and_accept_modes(self) -> None:
        engine = ProactiveTicketEngine()
        rules = AdmissionRuleSet(
            allowed_senders=("alice",),
            allowed_bots=("ci-bot",),
            accept_mode="record_only",
        )

        # Allowed human addressing agent -> explicit, even in record_only
        human = TriggerEnvelope(
            trigger_id="t-h1",
            source_kind="github",
            thread_key="gh:pr:1",
            sender_id="alice",
            addressed=True,
        )
        h_out = engine.evaluate_admission_gate(human, rules)
        assert h_out.admitted is True
        assert h_out.strength == "explicit"
        assert h_out.record_only is False

        # Allowed bot -> capped at inferred and marked record_only
        bot = TriggerEnvelope(
            trigger_id="t-b1",
            source_kind="github",
            thread_key="gh:pr:1",
            sender_id="ci-bot",
            kind="ci",
            is_bot=True,
        )
        b_out = engine.evaluate_admission_gate(bot, rules)
        assert b_out.admitted is True
        assert b_out.strength == "inferred"
        assert b_out.record_only is True

        # Unlisted bot -> always ignored
        evil_bot = TriggerEnvelope(
            trigger_id="t-b2",
            source_kind="github",
            thread_key="gh:pr:1",
            sender_id="spam-bot",
            addressed=True,
            is_bot=True,
        )
        assert engine.evaluate_admission_gate(evil_bot, rules).admitted is False

    def test_followup_ownership_and_handback(self) -> None:
        engine = ProactiveTicketEngine()
        rules = AdmissionRuleSet(allowed_senders=("alice",))
        followup = TriggerEnvelope(
            trigger_id="t-f1",
            source_kind="github",
            thread_key="gh:issue:99",
            sender_id="alice",
            addressed=True,
        )

        # Owned by tkt-1 -> Main Session may only stop
        owned = engine.route_trigger_disposition(
            followup, rules, subscribed_ticket_ids=("tkt-1",)
        )
        assert owned.disposition == "deliver_to_ticket"
        assert owned.owner_ticket_ids == ("tkt-1",)
        assert owned.main_session_actions == ("stop",)

        # Handed back by tkt-1 -> enters fresh Eval
        released = engine.route_trigger_disposition(
            followup,
            rules,
            subscribed_ticket_ids=("tkt-1",),
            handed_back_by=("tkt-1",),
        )
        assert released.disposition == "queue_eval"
        assert "accept" in released.main_session_actions

    def test_serialized_outbox_lanes(self) -> None:
        engine = ProactiveTicketEngine()
        items = (
            OutboxReplyItem("m2", "gh:1", "reply", "done", ticket_id="tkt-1", sequence=2),
            OutboxReplyItem("m1", "gh:1", "acknowledgement", "ack", ticket_id="tkt-1", sequence=1),
            OutboxReplyItem("m3", "gh:2", "acknowledgement", "ack2", ticket_id="tkt-2", sequence=1),
        )
        plan = engine.plan_outbox_delivery(items)
        assert [i.message_id for i in plan.ready_to_send] == ["m1", "m3"]
        assert [i.message_id for i in plan.blocked_behind_head] == ["m2"]
        assert isinstance(engine, ProactiveTicketProtocol)
        assert PROACTIVE_TICKET_SERVICE_KEY.name == "service.proactive_ticket_orchestrator"

    def test_skill_package_validation(self) -> None:
        from harness.creator.skills import SkillValidator

        skill_dir = (
            Path(__file__).resolve().parent.parent
            / ".agents"
            / "skills"
            / "proactive-ticket-orchestrator"
        )
        report = SkillValidator().validate(skill_dir)
        assert report.valid, f"Skill validation failed: {[c.message for c in report.checks if not c.passed]}"
