"""Top-level contract tests for ui-behavior-primitive-architect skill & UIBehaviorArchitectEngine (Rule 12, Rule 43, Rule 57)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from harness.services.ui_behavior_architect import (
    CONFIRM_MAX_CHARS,
    FRAMEWORK_EXPERTS,
    RETIRED_REF_LIMIT,
    SUPPORTED_ARIA_PATTERNS,
    AgentBridgeStepDecision,
    ExpertScopeRoute,
    PrimitiveAuditReport,
    TriModalVerificationReport,
    UIBehaviorArchitectEngine,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_SCRIPT = (
    REPO_ROOT / ".agents" / "skills" / "ui-behavior-primitive-architect" / "scripts" / "ui_behavior_architect_engine.py"
)


def test_constants_and_frozen_immutability_rule43() -> None:
    assert RETIRED_REF_LIMIT == 500
    assert CONFIRM_MAX_CHARS == 200
    assert len(SUPPORTED_ARIA_PATTERNS) == 15
    assert FRAMEWORK_EXPERTS == ("react", "vue", "svelte", "solid", "web")

    report = PrimitiveAuditReport(
        name="tabs",
        root_data_slot="tabs",
        valid=True,
        asleep_deferred=False,
    )
    decision = AgentBridgeStepDecision(
        ref="c1",
        component="tabs",
        action="select",
        resolved_action="setValue",
        allowed=True,
        needs_person=False,
        visible_in_snapshot=True,
        redacted_value="billing",
    )
    tri = TriModalVerificationReport(
        pattern="tabs",
        passed=True,
        aria_passed=True,
        ssr_passed=True,
        rtl_passed=True,
    )
    route = ExpertScopeRoute(framework="vue", triggered=False)

    with pytest.raises((AttributeError, TypeError)):
        report.valid = False  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        decision.needs_person = True  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        tri.ssr_passed = False  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        route.triggered = True  # type: ignore[misc]


def test_primitive_audit_edge_cases() -> None:
    engine = UIBehaviorArchitectEngine()
    res = engine.audit_primitive_definition(
        "BadPrimitive",
        state_keys=("open",),
        live_keys=("open",),
        provided_options=("open", "defaultOpen"),
        api_methods=("toggle",),
        agent_actions=("setOpen",),
        has_render_as_prop=True,
    )
    assert res.valid is False
    assert res.controlled_collisions == ("open",)
    assert res.live_controlled_overlaps == ("open",)
    assert res.missing_agent_actions == ("setOpen",)
    assert len(res.violations) == 5


def test_agent_bridge_marks_and_synonyms() -> None:
    engine = UIBehaviorArchitectEngine()

    unavailable = engine.evaluate_agent_bridge_step(
        "c9",
        "button",
        "delete",
        available_actions=("press",),
    )
    assert unavailable.allowed is False
    assert unavailable.reason == "action_not_available"

    confirm = engine.evaluate_agent_bridge_step(
        "c10",
        "dialog",
        "close",
        available_actions=("setOpen",),
        confirm_attr="Delete workspace permanently?",
        person_approved=None,
    )
    assert confirm.resolved_action == "setOpen"
    assert confirm.allowed is False
    assert confirm.needs_person is True
    assert confirm.reason == "needs_person"


def test_tri_modal_and_expert_scope_fanout() -> None:
    engine = UIBehaviorArchitectEngine()
    report = engine.evaluate_tri_modal_check(
        "menu",
        ssr_globals_accessed=("Math.random",),
        ltr_focus="item a",
        rtl_focus="item a",
    )
    assert report.passed is False
    assert report.aria_passed is True
    assert report.ssr_passed is False
    assert report.rtl_passed is True

    routes = {r.framework: r for r in engine.plan_expert_scope(("tests/fixtures.ts", "examples/menu/react/index.tsx"))}
    assert all(r.triggered for r in routes.values())
    assert routes["react"].own_files == ("examples/menu/react/index.tsx",)
    assert routes["vue"].own_files == ()


def test_skill_cli_entrypoint() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ENGINE_SCRIPT),
            "tri-modal",
            "--pattern",
            "dialog",
            "--ssr-globals",
            "window",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["ssr_passed"] is False
