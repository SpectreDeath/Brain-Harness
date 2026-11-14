"""Contract tests for ui_behavior_primitive_architect plugin (Rule 34, Rule 38, Rule 45)."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.ui_behavior_architect import (  # noqa: E402
    UI_BEHAVIOR_ARCHITECT_KEY,
    UIBehaviorArchitectProtocol,
)
from plugins.software_engineering.ui_behavior_primitive_architect.main import (  # noqa: E402
    plugin,
    ui_audit_primitive,
    ui_evaluate_agent_step,
    ui_plan_expert_scope,
    ui_verify_tri_modal,
)


def test_ui_behavior_plugin_entrypoints() -> None:
    audit = ui_audit_primitive(
        "search-field",
        state_keys=["value"],
        api_methods=["set", "clear"],
        agent_actions=["set"],
        has_asleep_predicate=True,
    )
    assert audit["valid"] is True
    assert audit["root_data_slot"] == "search-field"

    step = ui_evaluate_agent_step(
        "c2",
        "select",
        "open",
        available_actions=["setOpen", "setValue"],
        value="secret-123",
        secret=True,
    )
    assert step["resolved_action"] == "setOpen"
    assert step["allowed"] is True
    assert step["redacted_value"] == "[redacted]"

    tri = ui_verify_tri_modal(
        "tabs",
        ltr_focus="tab a",
        rtl_focus="tab a",
        ltr_state={"direction": "left"},
        rtl_state={"direction": "right"},
    )
    assert tri["passed"] is True

    scope = ui_plan_expert_scope(["packages/core/src/index.ts"])
    assert scope["triggered_frameworks"] == ["react", "vue", "svelte", "solid", "web"]


@pytest.mark.asyncio
async def test_ui_behavior_plugin_lifecycle_and_validator() -> None:
    ctx = ServiceContext()
    await plugin.on_load(ctx)
    resolved = ctx.require(UI_BEHAVIOR_ARCHITECT_KEY)
    assert isinstance(resolved, UIBehaviorArchitectProtocol)

    report = await PluginValidator().validate(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
