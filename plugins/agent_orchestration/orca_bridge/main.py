"""Orca Bridge plugin providing Git worktree sandboxes and multi-agent orchestration."""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.orca_bridge import (
    ORCA_BRIDGE_KEY,
    OrcaBridgeService,
    OrcaDeliveryBatch,
    OrcaMessageConfig,
    OrcaRunConfig,
    OrcaRunInfo,
    OrcaTaskSettlement,
    OrcaWorkerConfig,
    OrcaWorkerDispatchReceipt,
    OrcaWorktreeConfig,
    OrcaWorktreeInfo,
)

from .service import DefaultOrcaBridgeService

logger = structlog.get_logger(__name__)


class OrcaBridgePlugin(HarnessPlugin, OrcaBridgeService):
    """Harness Plugin providing Orca Git worktree isolation and multi-agent swarm orchestration."""

    name = "plugin.orca_bridge"
    version = "1.0.0"
    description = "Orca Bridge plugin for worktree management, multi-agent dispatching, and coordinator inboxes"
    trusted = True

    def __init__(self, orca_bin: str | None = None) -> None:
        super().__init__()
        self._service = DefaultOrcaBridgeService(orca_bin=orca_bin)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ORCA_BRIDGE_KEY]

    def on_load(self, context: ServiceContext) -> None:
        context.provide(ORCA_BRIDGE_KEY, self, provider=self.name)
        logger.info("OrcaBridgePlugin registered into IoC container")

    def on_unload(self, context: ServiceContext) -> None:
        logger.info("OrcaBridgePlugin unloaded")

    # --- Delegated Service Methods ---

    def create_worktree(self, config: OrcaWorktreeConfig) -> OrcaWorktreeInfo:
        return self._service.create_worktree(config)

    def list_worktrees(self, repo_id: str | None = None) -> list[OrcaWorktreeInfo]:
        return self._service.list_worktrees(repo_id=repo_id)

    def create_run(self, config: OrcaRunConfig) -> OrcaRunInfo:
        return self._service.create_run(config)

    def start_worker(self, config: OrcaWorkerConfig) -> OrcaWorkerDispatchReceipt:
        return self._service.start_worker(config)

    def check_mailbox(
        self,
        terminal: str | None = None,
        wait: bool = False,
        timeout_ms: int = 15000,
        types: str | None = None,
        ack_delivery_id: str | None = None,
    ) -> OrcaDeliveryBatch:
        return self._service.check_mailbox(
            terminal=terminal,
            wait=wait,
            timeout_ms=timeout_ms,
            types=types,
            ack_delivery_id=ack_delivery_id,
        )

    def send_message(self, config: OrcaMessageConfig) -> dict[str, Any]:
        return self._service.send_message(config)

    def send_terminal_input(
        self, terminal: str, text: str, enter: bool = True
    ) -> dict[str, Any]:
        return self._service.send_terminal_input(
            terminal=terminal, text=text, enter=enter
        )

    def coordinate_worker(
        self,
        task_spec: str,
        agent: str = "codex",
        worktree_name: str | None = None,
        model: str | None = None,
        effort: str | None = None,
        timeout_seconds: float = 60.0,
    ) -> OrcaTaskSettlement:
        return self._service.coordinate_worker(
            task_spec=task_spec,
            agent=agent,
            worktree_name=worktree_name,
            model=model,
            effort=effort,
            timeout_seconds=timeout_seconds,
        )


# Module-level tool wrappers for ReAct step dispatch
def orca_coordinate_task(
    task_spec: str,
    agent: str = "codex",
    worktree_name: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    """Execute a task end-to-end via an isolated supervised worker with automated settlement."""
    settlement = plugin.coordinate_worker(
        task_spec=task_spec,
        agent=agent,
        worktree_name=worktree_name,
        model=model,
        effort=effort,
        timeout_seconds=timeout_seconds,
    )
    return {
        "status": settlement.status,
        "task_id": settlement.task_id,
        "dispatch_id": settlement.dispatch_id,
        "outcome": settlement.outcome,
        "worktree_id": settlement.worktree_id,
        "files_modified": list(settlement.files_modified),
        "report": settlement.report,
        "elapsed_seconds": settlement.elapsed_seconds,
    }


def orca_create_worktree(
    name: str,
    repo_id: str | None = None,
    agent: str | None = None,
    prompt: str | None = None,
) -> dict[str, Any]:
    """Create an isolated Git worktree sandbox."""
    wt = plugin.create_worktree(
        OrcaWorktreeConfig(
            name=name,
            repo_id=repo_id,
            agent=agent,
            prompt=prompt,
        )
    )
    return {
        "status": "ok",
        "worktree_id": wt.worktree_id,
        "repo_id": wt.repo_id,
        "path": wt.path,
        "branch": wt.branch,
        "display_name": wt.display_name,
    }


def orca_start_worker(
    task_id: str,
    spec: str,
    agent: str = "codex",
    worktree: str = "new-top-level",
    model: str | None = None,
    effort: str | None = None,
) -> dict[str, Any]:
    """Start a supervised agent worker in a dedicated worktree."""
    receipt = plugin.start_worker(
        OrcaWorkerConfig(
            task_id=task_id,
            spec=spec,
            agent=agent,
            worktree=worktree,
            model=model,
            effort=effort,
        )
    )
    return {
        "status": "ok",
        "dispatch_id": receipt.dispatch_id,
        "task_id": receipt.task_id,
        "terminal_handle": receipt.terminal_handle,
        "worktree_id": receipt.worktree_id,
        "preamble": receipt.preamble,
    }


def orca_check_mailbox(
    terminal: str | None = None,
    wait: bool = False,
    timeout_ms: int = 15000,
    ack_delivery_id: str | None = None,
) -> dict[str, Any]:
    """Inspect the coordinator FIFO mailbox for reports."""
    batch = plugin.check_mailbox(
        terminal=terminal,
        wait=wait,
        timeout_ms=timeout_ms,
        ack_delivery_id=ack_delivery_id,
    )
    return {
        "status": "ok",
        "delivery_id": batch.delivery_id,
        "messages": list(batch.messages),
        "count": len(batch.messages),
        "has_keepalive": batch.has_keepalive,
    }


def orca_send_message(
    subject: str,
    to: str | None = None,
    body: str | None = None,
    message_type: str = "status",
    outcome: str | None = None,
) -> dict[str, Any]:
    """Deliver an inter-agent message or settlement signal."""
    res = plugin.send_message(
        OrcaMessageConfig(
            subject=subject,
            to=to,
            body=body,
            message_type=message_type,
            outcome=outcome,
        )
    )
    return {
        "status": "ok",
        "result": res,
    }


# Export authoritative module-level singleton (Rule 45)
plugin = OrcaBridgePlugin()
