"""Tests for Orca Bridge Plugin, slotted domain models, and service registration."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.orca_bridge import (
    ORCA_BRIDGE_KEY,
    OrcaBridgeService,
    OrcaMailboxMessage,
    OrcaMessageConfig,
    OrcaRunConfig,
    OrcaTaskSettlement,
    OrcaWorkerConfig,
    OrcaWorktreeConfig,
    OrcaWorktreeInfo,
)
from plugins.agent_orchestration.orca_bridge.main import (
    OrcaBridgePlugin,
    orca_check_mailbox,
    orca_coordinate_task,
    orca_create_worktree,
    orca_send_message,
    orca_start_worker,
    plugin,
)
from plugins.agent_orchestration.orca_bridge.service import DefaultOrcaBridgeService


@pytest.mark.unit
def test_orca_slotted_frozen_dataclasses() -> None:
    """Verify slotted and frozen immutability on Orca domain models (Rule 12, Rule 43)."""
    wt_config = OrcaWorktreeConfig(name="feature-test", repo_id="repo-1")
    assert wt_config.name == "feature-test"
    assert wt_config.repo_id == "repo-1"

    # Immutability check via direct attribute assignment (Rule 43)
    with pytest.raises((AttributeError, TypeError)):
        wt_config.name = "mutated"  # type: ignore

    wt_info = OrcaWorktreeInfo(
        worktree_id="repo-1::/tmp/test",
        repo_id="repo-1",
        path="/tmp/test",
        branch="feature-test",
        display_name="Feature Test",
    )
    assert wt_info.worktree_id == "repo-1::/tmp/test"
    with pytest.raises((AttributeError, TypeError)):
        wt_info.branch = "mutated"  # type: ignore

    # Construction assertion check
    with pytest.raises(AssertionError):
        OrcaWorktreeConfig(name="")

    with pytest.raises(AssertionError):
        OrcaWorktreeInfo(
            worktree_id="invalid-id-without-colons",
            repo_id="repo-1",
            path="/tmp/test",
            branch="test",
            display_name="Test",
        )


@pytest.mark.unit
def test_orca_worker_and_message_models() -> None:
    """Verify worker config and settlement message validation rules."""
    worker_cfg = OrcaWorkerConfig(spec="Implement feature", agent="codex")
    assert worker_cfg.agent == "codex"

    with pytest.raises(AssertionError):
        OrcaWorkerConfig(agent="invalid_agent")

    msg_cfg = OrcaMessageConfig(
        subject="Task finished",
        message_type="worker_done",
        outcome="succeeded",
        task_id="task-1",
        dispatch_id="dispatch-1",
    )
    assert msg_cfg.outcome == "succeeded"

    # worker_done requires outcome
    with pytest.raises(AssertionError):
        OrcaMessageConfig(subject="Done", message_type="worker_done", outcome=None)


@pytest.mark.unit
def test_orca_settlement_and_mailbox_message_models() -> None:
    """Verify OrcaTaskSettlement and OrcaMailboxMessage slotted immutability per Rule 12 and Rule 43."""
    settlement = OrcaTaskSettlement(
        task_id="task-100",
        dispatch_id="dispatch-100",
        outcome="succeeded",
        worktree_id="repo-1::/wt-100",
        files_modified=("src/auth.py",),
        report="Task succeeded cleanly",
        elapsed_seconds=12.4,
    )
    assert settlement.task_id == "task-100"
    assert settlement.outcome == "succeeded"
    assert settlement.files_modified == ("src/auth.py",)

    # Immutability check via direct assignment (Rule 43)
    with pytest.raises((AttributeError, TypeError)):
        settlement.outcome = "failed"  # type: ignore

    # Construction checks
    with pytest.raises(AssertionError):
        OrcaTaskSettlement(
            task_id="",
            dispatch_id="dispatch-100",
            outcome="succeeded",
            worktree_id="repo-1::/wt-100",
        )

    with pytest.raises(AssertionError):
        OrcaTaskSettlement(
            task_id="task-100",
            dispatch_id="dispatch-100",
            outcome="invalid_outcome",  # must be succeeded or failed
            worktree_id="repo-1::/wt-100",
        )

    mail = OrcaMailboxMessage(
        id="msg-1",
        subject="Progress update",
        body="50% complete",
        message_type="status",
    )
    assert mail.subject == "Progress update"
    with pytest.raises((AttributeError, TypeError)):
        mail.subject = "New subject"  # type: ignore


@pytest.mark.unit
def test_orca_bridge_service_mock_lifecycle() -> None:
    """Verify in-memory fallback execution of DefaultOrcaBridgeService."""
    service = DefaultOrcaBridgeService(orca_bin=None)
    assert not service.is_cli_available

    # 1. Create worktree
    wt = service.create_worktree(
        OrcaWorktreeConfig(name="test-wt", repo_id="repo-alpha")
    )
    assert wt.repo_id == "repo-alpha"
    assert "repo-alpha::" in wt.worktree_id

    # 2. List worktrees
    wts = service.list_worktrees(repo_id="repo-alpha")
    assert len(wts) == 1
    assert wts[0].worktree_id == wt.worktree_id

    # 3. Create run
    run = service.create_run(
        OrcaRunConfig(objective="Refactor auth module", from_handle="coord-term")
    )
    assert run.objective == "Refactor auth module"
    assert run.coordinator_terminal == "coord-term"

    # 4. Start worker
    worker = service.start_worker(
        OrcaWorkerConfig(
            spec="Run lint checks",
            agent="claude",
            worktree=wt.worktree_id,
        )
    )
    assert worker.status == "ready"
    assert "TASK_ID=" in (worker.preamble or "")

    # 5. Send message and check mailbox
    send_receipt = service.send_message(
        OrcaMessageConfig(
            subject="Step completed",
            message_type="status",
            body="All unit tests passed",
            task_id=worker.task_id,
            dispatch_id=worker.dispatch_id,
        )
    )
    assert send_receipt["status"] == "ok"

    batch = service.check_mailbox()
    assert len(batch.messages) == 1
    assert batch.messages[0]["subject"] == "Step completed"

    # ACK clears mock inbox
    service.check_mailbox(ack_delivery_id=batch.delivery_id)
    cleared_batch = service.check_mailbox()
    assert len(cleared_batch.messages) == 0


@pytest.mark.unit
def test_orca_coordinate_worker_deep_seam() -> None:
    """Verify high-leverage coordinate_worker swarm execution seam."""
    service = DefaultOrcaBridgeService(orca_bin=None)

    settlement = service.coordinate_worker(
        task_spec="Deepen architecture seams across plugins",
        agent="codex",
        timeout_seconds=10.0,
    )
    assert isinstance(settlement, OrcaTaskSettlement)
    assert settlement.outcome == "succeeded"
    assert settlement.status == "settled"
    assert len(settlement.files_modified) > 0
    assert "task-" in settlement.task_id
    assert "dispatch-" in settlement.dispatch_id


@pytest.mark.unit
def test_orca_bridge_plugin_ioc_registration() -> None:
    """Verify plugin singleton and IoC container registration (Rule 45)."""
    assert isinstance(plugin, OrcaBridgePlugin)
    assert plugin.name == "plugin.orca_bridge"
    assert ORCA_BRIDGE_KEY in plugin.provides

    context = ServiceContext()
    plugin.on_load(context)

    # Resolution from container
    resolved = context.require(ORCA_BRIDGE_KEY)
    assert isinstance(resolved, OrcaBridgeService)

    # Invoke method on resolved service
    run = resolved.create_run(OrcaRunConfig(objective="IoC container test"))
    assert run.objective == "IoC container test"

    plugin.on_unload(context)


@pytest.mark.unit
def test_orca_module_tool_wrappers() -> None:
    """Verify synchronous tool wrappers for ReAct step dispatch."""
    # Coordinate task
    res_coord = orca_coordinate_task(
        task_spec="Run unit test suite", agent="claude", timeout_seconds=5.0
    )
    assert res_coord["status"] == "settled"
    assert res_coord["outcome"] == "succeeded"
    assert len(res_coord["files_modified"]) > 0

    # Create worktree
    res_wt = orca_create_worktree(name="hotfix-branch")
    assert res_wt["status"] == "ok"
    assert "hotfix-branch" in res_wt["worktree_id"]

    # Start worker
    res_worker = orca_start_worker(task_id="task-001", spec="Run security scan")
    assert res_worker["status"] == "ok"
    assert "task-001" in res_worker["task_id"]

    # Check mailbox
    res_box = orca_check_mailbox()
    assert res_box["status"] == "ok"

    # Send message
    res_msg = orca_send_message(subject="Status report", body="Task in progress")
    assert res_msg["status"] == "ok"


@pytest.mark.unit
def test_orca_bridge_manifest_validation() -> None:
    """Verify plugin manifest validation using PluginValidator (Rule 38)."""
    plugin_dir = Path("plugins/agent_orchestration/orca_bridge")
    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid, (
        f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
    )
    for check in report.checks:
        assert check.passed, f"Check '{check.rule}' failed: {check.message}"
