"""Contract test suite for OrcaBridgeService decomposition per AGENTS.md Rule 11, Rule 14, Rule 18, Rule 23."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.orca_bridge import (
    ORCA_BRIDGE_KEY,
    OrcaBridgeService,
    OrcaMessageConfig,
    OrcaRunConfig,
    OrcaWorkerConfig,
    OrcaWorktreeConfig,
)
from plugins.agent_orchestration.orca_bridge.main import OrcaBridgePlugin, plugin
from plugins.agent_orchestration.orca_bridge.service import (
    DefaultOrcaBridgeService,
    OrcaCoordinatorMixin,
    OrcaMailboxMixin,
    OrcaTransportMixin,
    OrcaWorkerMixin,
    OrcaWorktreeMixin,
)


@pytest.mark.unit
class TestOrcaBridgeDecomposition:
    """Verifies subpackage architecture, line limits, and service execution."""

    def test_submodule_line_counts(self) -> None:
        """Rule 11: All decomposed submodules in orca_bridge/service must be <= 200 lines."""
        service_dir = (
            Path(__file__).parent.parent
            / "plugins"
            / "agent_orchestration"
            / "orca_bridge"
            / "service"
        )
        assert service_dir.exists() and service_dir.is_dir()

        py_files = list(service_dir.glob("*.py"))
        assert len(py_files) >= 6

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert line_count <= 200, f"{py_file.name} has {line_count} lines (> 200 limit)"

    def test_direct_and_submodule_imports(self) -> None:
        """Verify all symbols can be imported from root package and submodules."""
        from plugins.agent_orchestration.orca_bridge.service.coordinator import (
            OrcaCoordinatorMixin as OCM,
        )
        from plugins.agent_orchestration.orca_bridge.service.default_service import (
            DefaultOrcaBridgeService as DOBS,
        )
        from plugins.agent_orchestration.orca_bridge.service.mailbox import (
            OrcaMailboxMixin as OMM,
        )
        from plugins.agent_orchestration.orca_bridge.service.transport import (
            OrcaTransportMixin as OTM,
        )
        from plugins.agent_orchestration.orca_bridge.service.worker import (
            OrcaWorkerMixin as OWM,
        )
        from plugins.agent_orchestration.orca_bridge.service.worktree import (
            OrcaWorktreeMixin as OWTM,
        )

        assert DOBS is DefaultOrcaBridgeService
        assert OTM is OrcaTransportMixin
        assert OWTM is OrcaWorktreeMixin
        assert OWM is OrcaWorkerMixin
        assert OMM is OrcaMailboxMixin
        assert OCM is OrcaCoordinatorMixin

    def test_plugin_module_singleton_and_keys(self) -> None:
        """Rule 45: Plugin singleton exported and declares typed service keys."""
        assert isinstance(plugin, OrcaBridgePlugin)
        assert ORCA_BRIDGE_KEY in plugin.provides
        assert plugin.trusted is True

    def test_ioc_registration_and_delegation(self) -> None:
        """Rule 2 & Rule 58: Service context resolution and method delegation."""
        ctx = ServiceContext()
        custom_plugin = OrcaBridgePlugin()
        custom_plugin.on_load(ctx)

        assert ctx.has(ORCA_BRIDGE_KEY)
        resolved = ctx.require(ORCA_BRIDGE_KEY)
        assert isinstance(resolved, OrcaBridgeService)

        # Worktree delegation
        wt = resolved.create_worktree(OrcaWorktreeConfig(name="test-ioc-wt"))
        assert wt.branch == "test-ioc-wt"
        assert len(resolved.list_worktrees()) >= 1

        # Run and worker delegation
        run = resolved.create_run(OrcaRunConfig(objective="IOC Test Run"))
        assert run.status == "active"

        worker = resolved.start_worker(
            OrcaWorkerConfig(task_id="task-01", agent="codex", worktree=wt.worktree_id)
        )
        assert worker.status == "ready"
        assert "ORCA SUPERVISED WORKER PREAMBLE" in (worker.preamble or "")

    def test_high_leverage_coordination_and_settlement(self) -> None:
        """Verify coordinator_worker end-to-end swarm execution and FIFO settlement."""
        service = DefaultOrcaBridgeService(orca_bin=None)

        settlement = service.coordinate_worker(
            task_spec="Verify decomposed orca architecture",
            agent="codex",
            timeout_seconds=5.0,
        )
        assert settlement.status == "settled"
        assert settlement.outcome == "succeeded"
        assert len(settlement.files_modified) == 2
        assert settlement.task_id.startswith("task-")

    def test_messaging_and_mailbox_fifo(self) -> None:
        """Verify send_message, check_mailbox, and auto-ack semantics."""
        service = DefaultOrcaBridgeService(orca_bin=None)

        msg_result = service.send_message(
            OrcaMessageConfig(
                subject="Test Signal",
                to="coordinator",
                body="Execution update",
                message_type="status_report",
            )
        )
        assert msg_result["status"] == "ok"
        assert msg_result["accepted"] is True

        batch = service.check_mailbox(terminal="coordinator")
        assert len(batch.messages) == 1
        assert batch.messages[0]["subject"] == "Test Signal"

        # Ack delivery clears mock inbox
        service.check_mailbox(ack_delivery_id=batch.delivery_id)
        cleared_batch = service.check_mailbox(terminal="coordinator")
        assert len(cleared_batch.messages) == 0
