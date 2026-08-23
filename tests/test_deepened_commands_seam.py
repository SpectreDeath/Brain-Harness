"""Tests for the deepened commands seam and CommandRegistry."""

import asyncio
from pathlib import Path
import pytest

from harness.commands import (
    CommandRegistry,
    ComputeAssessmentResult,
    ConfigApplyResult,
    ConfigValidationResult,
    EventQueryResult,
    McpServeResult,
    RuntimeRunResult,
    WorkspaceInitResult,
    apply_config_cmd,
    assess_compute_cmd,
    build_plugin_cmd,
    get_events_cmd,
    init_workspace_cmd,
    list_archetypes_cmd,
    remediate_plugin_cmd,
    run_harness_cmd,
    scaffold_plugin_cmd,
    serve_mcp_cmd,
    start_harness,
    validate_config_cmd,
    validate_plugin_cmd,
    watch_workspace_cmd,
)
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent


@pytest.mark.unit
def test_init_workspace_cmd(tmp_path: Path) -> None:
    """Verify workspace initialization via pure command seam."""
    ws = tmp_path / "test_workspace"
    res = init_workspace_cmd(ws)

    assert isinstance(res, WorkspaceInitResult)
    assert res.workspace_path == ws.resolve()
    assert res.plugins_dir.exists()
    assert res.config_dir.exists()
    assert res.config_file.exists()
    assert res.status == "initialized"
    assert res.to_dict()["workspace_path"] == str(ws.resolve())


@pytest.mark.unit
@pytest.mark.unit
def test_config_validation_cmd(tmp_path: Path) -> None:
    """Verify declarative config validation via command seam."""
    valid_cfg = tmp_path / "valid.json"
    valid_cfg.write_text('{"version": "0.1.0", "plugins": []}', encoding="utf-8")

    res = validate_config_cmd(valid_cfg)
    assert isinstance(res, ConfigValidationResult)
    assert res.valid is True
    assert res.version == "0.1.0"
    assert res.plugins_count == 0

    invalid_cfg = tmp_path / "invalid.json"
    invalid_cfg.write_text('{"version": "0.1.0", "plugins": "not_a_list"}', encoding="utf-8")
    res_inv = validate_config_cmd(invalid_cfg)
    assert res_inv.valid is False
    assert res_inv.error_message is not None


@pytest.mark.asyncio
async def test_run_harness_cmd_non_blocking() -> None:
    """Verify non-blocking runtime bootstrap and summary."""
    res = await run_harness_cmd(db_path=":memory:", blocking=False)
    assert isinstance(res, RuntimeRunResult)
    assert res.status == "running"
    assert res.services_count > 0
    assert len(res.summary) > 0
    await res.runtime.stop()


@pytest.mark.asyncio
async def test_start_harness_context_manager() -> None:
    """Verify start_harness async context manager auto-cleanup."""
    async with start_harness(db_path=":memory:") as rt:
        assert rt.is_running
        assert len(rt.context.list_services()) > 0
    assert not rt.is_running


@pytest.mark.asyncio
async def test_apply_config_cmd(tmp_path: Path) -> None:
    """Verify declarative config reconciliation via apply command."""
    cfg = tmp_path / "config.json"
    cfg.write_text('{"version": "0.1.0", "plugins": []}', encoding="utf-8")

    res = await apply_config_cmd(cfg)
    assert isinstance(res, ConfigApplyResult)
    assert res.reconciled is True
    assert res.status == "applied"


@pytest.mark.asyncio
async def test_serve_mcp_cmd_with_shutdown() -> None:
    """Verify MCP serve command initialization with shutdown event."""
    shutdown_ev = asyncio.Event()
    shutdown_ev.set()  # Immediately trigger shutdown

    res = await serve_mcp_cmd(stdio=False, db_path=":memory:", shutdown_event=shutdown_ev)
    assert isinstance(res, McpServeResult)
    assert res.tools_count > 0


@pytest.mark.unit
def test_assess_compute_cmd() -> None:
    """Verify compute assessor command and visual brief flag."""
    res = assess_compute_cmd(
        "Refactor database connector to use connection pooling",
        files_count=3,
        is_architecture=True,
        profile="reasoning_heavy",
        generate_html=True,
    )
    assert isinstance(res, ComputeAssessmentResult)
    assert res.assessment.thinking_level.value in ("high", "medium")
    assert "Recommendation" in res.recommendation_block
    assert res.html_path is not None
    assert Path(res.html_path).exists()


@pytest.mark.unit
def test_get_events_cmd(tmp_path: Path) -> None:
    """Verify reading and filtering append-only event stream."""
    log_file = tmp_path / "events.jsonl"
    bus = EventBus(log_file=log_file)
    bus.emit_sync(
        HarnessEvent(
            event_type=EventType.HARNESS_STARTED,
            source="test",
            payload={"mode": "test"},
        )
    )

    res = get_events_cmd(log_path=log_file)


    assert isinstance(res, EventQueryResult)
    assert res.total_count == 1
    assert len(res.events) == 1
    assert res.events[0].source == "test"


@pytest.mark.asyncio
async def test_creator_commands(tmp_path: Path) -> None:
    """Verify creator build, validate, and remediate command seams."""
    pdir = tmp_path / "my_plugin"
    res = await scaffold_plugin_cmd(
        name="my_plugin",
        target_dir=pdir,
        description="Test plugin",
        language="python",
    )
    assert (pdir / "plugin.json").exists()
    assert (pdir / "main.py").exists()

    val = await validate_plugin_cmd(pdir)
    assert val.valid is True

    rem = await remediate_plugin_cmd(pdir)
    assert rem.valid is True

    archetypes = list_archetypes_cmd()
    assert len(archetypes) > 0


@pytest.mark.asyncio
async def test_command_registry_dispatch() -> None:
    """Verify CommandRegistry lookup, listing, and automated telemetry dispatch."""
    cmds = CommandRegistry.list_commands()
    assert len(cmds) >= 25

    workspace_cmds = CommandRegistry.list_commands(category="workspace")
    assert any(c.name == "workspace.init" for c in workspace_cmds)

    descriptor = CommandRegistry.get("compute.assess")
    assert descriptor is not None
    assert descriptor.category == "compute"

    # Test dispatch
    res = await CommandRegistry.dispatch(
        "compute.assess",
        prompt="Fix a minor typo in README",
        files_count=1,
        profile="balanced",
    )
    assert isinstance(res, ComputeAssessmentResult)
    assert res.assessment.thinking_level.value in ("low", "off", "medium")

