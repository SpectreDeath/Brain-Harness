"""Composite DefaultOrcaBridgeService unifying worktrees, workers, mailbox, and coordinator."""

from __future__ import annotations

from harness.services.orca_bridge import OrcaBridgeService
from plugins.agent_orchestration.orca_bridge.service.coordinator import OrcaCoordinatorMixin
from plugins.agent_orchestration.orca_bridge.service.mailbox import OrcaMailboxMixin
from plugins.agent_orchestration.orca_bridge.service.transport import OrcaTransportMixin
from plugins.agent_orchestration.orca_bridge.service.worker import OrcaWorkerMixin
from plugins.agent_orchestration.orca_bridge.service.worktree import OrcaWorktreeMixin


class DefaultOrcaBridgeService(
    OrcaTransportMixin,
    OrcaWorktreeMixin,
    OrcaWorkerMixin,
    OrcaMailboxMixin,
    OrcaCoordinatorMixin,
    OrcaBridgeService,
):
    """Core implementation of OrcaBridgeService wrapping the orca CLI with in-memory fallback."""

    def __init__(self, orca_bin: str | None = None) -> None:
        super().__init__(orca_bin=orca_bin)
