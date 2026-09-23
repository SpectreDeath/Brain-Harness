"""Contract test suite for Context Course Bridge Plugin.

Verifies micro-kernel IoC service registration (Rule 2, Rule 45, Rule 49),
PluginValidator synchronous validation (Rule 34, Rule 38), and exported tool endpoints.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "context-engineering-architect" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Import the plugin module and singleton (Rule 45)
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.context_course import (
    CONTEXT_COURSE_SERVICE_KEY,
    ContextCourseService,
)
from plugins.agent_orchestration.context_course_bridge.main import (
    ContextCourseBridgePlugin,
    audit_context_surface,
    plan_subagent_topology,
    plugin,
    run_nano_harness,
    verify_context_snippets,
)


@pytest.mark.unit
class TestContextCourseBridgePluginProperties:
    """Verify plugin manifest metadata and singleton exports (Rule 45)."""

    def test_singleton_export(self) -> None:
        assert isinstance(plugin, ContextCourseBridgePlugin)
        assert isinstance(plugin, ContextCourseService)

    def test_plugin_metadata(self) -> None:
        assert plugin.name == "plugin.context_course_bridge"
        assert plugin.version == "1.0.0"
        assert CONTEXT_COURSE_SERVICE_KEY in plugin.provides
        assert len(plugin.requires) == 0


@pytest.mark.asyncio
async def test_ioc_registration_and_resolution() -> None:
    """Verify service registration and typed resolution in IoC ServiceContext (Rule 2, Rule 45)."""
    context = ServiceContext()

    # Load plugin into container
    await plugin.on_load(context)

    # Resolve typed service key
    resolved = context.require(CONTEXT_COURSE_SERVICE_KEY)
    assert resolved is plugin

    # Unload plugin
    await plugin.on_unload(context)


@pytest.mark.unit
def test_plugin_validator_compliance() -> None:
    """Verify plugin manifest and structure passes PluginValidator (Rule 34, Rule 38)."""
    plugin_dir = (
        Path(__file__).resolve().parents[1]
        / "plugins"
        / "agent_orchestration"
        / "context_course_bridge"
    )
    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True, (
        f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
    )


@pytest.mark.unit
class TestExportedToolEndpoints:
    """Verify top-level exported tool functions for headless CLI and agent dispatch."""

    def test_audit_context_surface_tool(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        res = audit_context_surface(str(workspace))
        assert isinstance(res, dict)
        assert "overall_score" in res
        assert "layers_evaluated" in res
        assert "token_budget_estimate" in res

    def test_run_nano_harness_tool(self, tmp_path: Path) -> None:
        res = run_nano_harness(
            task="Check workspace", workspace_root=str(tmp_path), max_steps=5
        )
        assert isinstance(res, dict)
        assert res["success"] is True
        assert res["steps_taken"] >= 1
        assert "final_answer" in res

    def test_verify_context_snippets_tool(self) -> None:
        markdown = """
```python
x = [1, 2, 3]
assert len(x) == 3
```
"""
        res = verify_context_snippets(markdown)
        assert isinstance(res, dict)
        assert res["passed"] is True
        assert res["snippets_count"] == 1

    def test_plan_subagent_topology_tool(self) -> None:
        res = plan_subagent_topology(files_count=18, task_type="code_review")
        assert isinstance(res, dict)
        assert res["topology"] == "FAN_OUT_FAN_IN"
        assert res["subagents_planned"] >= 2
        assert res["context_savings_percent"] > 0.0
