"""Contract tests for ui-behavior-primitive-architect skill and UIBehaviorArchitectEngine (Rule 12, Rule 43, Rule 57)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.exists() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from harness.services.ui_behavior_architect import (  # noqa: E402
    CONFIRM_MAX_CHARS,
    FRAMEWORK_EXPERTS,
    SUPPORTED_ARIA_PATTERNS,
    AgentBridgeStepDecision,
    ExpertScopeRoute,
    PrimitiveAuditReport,
    TriModalVerificationReport,
    UIBehaviorArchitectEngine,
)

ENGINE_SCRIPT = (
    _REPO_ROOT
    / ".agents"
    / "skills"
    / "ui-behavior-primitive-architect"
    / "scripts"
    / "ui_behavior_architect_engine.py"
)


def test_frozen_slotted_immutability_rule43() -> None:
    report = PrimitiveAuditReport(
        name="search-field",
        root_data_slot="search-field",
        valid=True,
        asleep_deferred=True,
    )
    decision = AgentBridgeStepDecision(
        ref="c1",
        component="select",
        action="open",
        resolved_action="setOpen",
        allowed=True,
        needs_person=False,
        visible_in_snapshot=True,
        redacted_value="us",
    )
    tri = TriModalVerificationReport(
        pattern="tabs",
        passed=True,
        aria_passed=True,
        ssr_passed=True,
        rtl_passed=True,
    )
    route = ExpertScopeRoute(framework="react", triggered=True)

    with pytest.raises((AttributeError, TypeError)):
        report.valid = False  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        decision.allowed = False  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        tri.passed = False  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        route.triggered = False  # type: ignore[misc]


def test_audit_primitive_definition() -> None:
    engine = UIBehaviorArchitectEngine()

    ok = engine.audit_primitive_definition(
        "search-field",
        state_keys=("value", "highlighted"),
        live_keys=("highlighted",),
        provided_options=("defaultValue",),
        api_methods=("set", "clear"),
        agent_actions=("set",),
        has_asleep_predicate=True,
    )
    assert ok.valid is True
    assert ok.root_data_slot == "search-field"
    assert ok.asleep_deferred is True
    assert ok.violations == ()

    bad = engine.audit_primitive_definition(
        "SearchField",
        state_keys=("value", "open"),
        live_keys=("open",),
        controlled_keys=("value", "open"),
        provided_options=("value", "defaultValue"),
        api_methods=("setOpen",),
        agent_actions=("setOpen", "setValue"),
        has_render_as_prop=True,
    )
    assert bad.valid is False
    assert bad.controlled_collisions == ("value",)
    assert bad.live_controlled_overlaps == ("open",)
    assert bad.missing_agent_actions == ("setValue",)
    assert any("as" in v for v in bad.violations)


def test_evaluate_agent_bridge_step() -> None:
    engine = UIBehaviorArchitectEngine()

    syn = engine.evaluate_agent_bridge_step(
        "c2",
        "select",
        "open",
        available_actions=("setOpen", "setValue"),
        value="de",
    )
    assert syn.resolved_action == "setOpen"
    assert syn.allowed is True
    assert syn.redacted_value == "de"
    assert syn.read_only_hint is False
    assert syn.untrusted_content_hint is True
    assert syn.consequential_hint is True

    hidden = engine.evaluate_agent_bridge_step("c3", "input", "setValue", hidden=True)
    assert hidden.visible_in_snapshot is False
    assert hidden.allowed is False
    assert hidden.reason == "hidden_off_limits"

    secret = engine.evaluate_agent_bridge_step("c4", "input", "setValue", value="sk-secret-token", secret=True)
    assert secret.redacted_value == "[redacted]"
    assert secret.allowed is True

    long_prompt = "x" * 260
    pending_confirm = engine.evaluate_agent_bridge_step(
        "c5",
        "button",
        "press",
        confirm_attr=long_prompt,
        person_approved=False,
    )
    assert pending_confirm.allowed is False
    assert pending_confirm.needs_person is True
    assert pending_confirm.reason == "needs_person"
    assert pending_confirm.confirm_prompt is not None
    assert len(pending_confirm.confirm_prompt) == CONFIRM_MAX_CHARS

    approved_confirm = engine.evaluate_agent_bridge_step(
        "c5",
        "button",
        "press",
        confirm_attr="   ",
        person_approved=True,
        tool_name="snapshot",
    )
    assert approved_confirm.allowed is True
    assert approved_confirm.confirm_prompt == "This needs a person."
    assert approved_confirm.read_only_hint is True
    assert approved_confirm.consequential_hint is False


def test_evaluate_tri_modal_check() -> None:
    engine = UIBehaviorArchitectEngine()
    assert len(SUPPORTED_ARIA_PATTERNS) == 15

    clean = engine.evaluate_tri_modal_check(
        "tabs",
        ltr_focus="tab b",
        rtl_focus="tab b",
        ltr_state={"id": "t1", "value": "b", "direction": "right"},
        rtl_state={"id": "t2", "value": "b", "direction": "left"},
    )
    assert clean.passed is True
    assert clean.aria_passed is True
    assert clean.ssr_passed is True
    assert clean.rtl_passed is True

    broken = engine.evaluate_tri_modal_check(
        "unknown-widget",
        aria_violations=("tablist missing accessible name",),
        ssr_globals_accessed=("Date.now", "window"),
        ltr_focus="tab b",
        rtl_focus="tab c",
        ltr_state={"side": "right"},
        rtl_state={"side": "right"},
    )
    assert broken.passed is False
    assert broken.aria_passed is False
    assert broken.ssr_passed is False
    assert broken.rtl_passed is False
    assert len(broken.problems) == 6


def test_plan_expert_scope() -> None:
    engine = UIBehaviorArchitectEngine()

    shared_routes = engine.plan_expert_scope(("packages/core/src/page/agent/agent.ts",))
    assert [r.framework for r in shared_routes] == list(FRAMEWORK_EXPERTS)
    assert all(r.triggered for r in shared_routes)
    assert all(r.shared_files == ("packages/core/src/page/agent/agent.ts",) for r in shared_routes)

    scoped_routes = {
        r.framework: r
        for r in engine.plan_expert_scope(
            (
                "packages/svelte/src/primitive.ts",
                "apps/docs/content/docs/web-components/tabs.mdx",
            )
        )
    }
    assert scoped_routes["svelte"].triggered is True
    assert scoped_routes["web"].triggered is True
    assert scoped_routes["react"].triggered is False
    assert scoped_routes["vue"].triggered is False
    assert scoped_routes["solid"].triggered is False


def test_cli_subcommands() -> None:
    r_audit = subprocess.run(
        [
            sys.executable,
            str(ENGINE_SCRIPT),
            "audit-primitive",
            "--name",
            "search-field",
            "--api-methods",
            "set,clear",
            "--agent-actions",
            "set",
            "--asleep",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(r_audit.stdout)["valid"] is True

    r_step = subprocess.run(
        [
            sys.executable,
            str(ENGINE_SCRIPT),
            "agent-step",
            "--ref",
            "c1",
            "--component",
            "select",
            "--action",
            "open",
            "--available-actions",
            "setOpen",
            "--secret",
            "--value",
            "secret-val",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    step_data = json.loads(r_step.stdout)
    assert step_data["resolved_action"] == "setOpen"
    assert step_data["redacted_value"] == "[redacted]"

    r_tri = subprocess.run(
        [
            sys.executable,
            str(ENGINE_SCRIPT),
            "tri-modal",
            "--pattern",
            "tabs",
            "--ltr-focus",
            "tab b",
            "--rtl-focus",
            "tab b",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(r_tri.stdout)["passed"] is True

    r_scope = subprocess.run(
        [
            sys.executable,
            str(ENGINE_SCRIPT),
            "expert-scope",
            "--files",
            "packages/svelte/src/index.ts",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    scope_data = {item["framework"]: item for item in json.loads(r_scope.stdout)}
    assert scope_data["svelte"]["triggered"] is True
    assert scope_data["react"]["triggered"] is False
