"""Typed service protocol and ServiceKey for Harness Spawner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import (
    ServiceContext,
    ServiceKey,
)
from harness.services.agent_graph import ExecutionGraphExport
from harness.services.recursive_harnessing.models import Tree

from .models import (
    SpawnLifecycleState,
    SpawnMergeProposal,
    SpawnSpec,
    SpawnedHarnessRecord,
)


@runtime_checkable
class HarnessSpawnerProtocol(Protocol):
    """Protocol for micro-kernel child harness spawning and lifecycle governance."""

    def spawn(
        self,
        spec: SpawnSpec,
        *,
        probe_fn: Callable[[SpawnSpec, ServiceContext], bool] | None = None,
        materialize_dir: Path | str | None = None,
        dock_service: Any = None,
        approve_dock: bool = False,
    ) -> SpawnedHarnessRecord: ...

    def record_usage(
        self,
        spawn_id: str,
        *,
        tokens: int = 0,
        rollouts: int = 0,
        sessions: int = 0,
    ) -> SpawnedHarnessRecord: ...

    def complete(
        self,
        spawn_id: str,
        *,
        tokens_used: int = 0,
    ) -> SpawnedHarnessRecord: ...

    def retire(self, spawn_id: str) -> SpawnedHarnessRecord: ...

    def retire_all(self) -> list[SpawnedHarnessRecord]: ...

    def get_spawn(self, spawn_id: str) -> SpawnedHarnessRecord | None: ...

    def list_spawns(self, *, state: SpawnLifecycleState | None = None) -> list[SpawnedHarnessRecord]: ...

    def propose_merge_back(
        self,
        spawn_id: str,
        *,
        task_id: str,
        cue: str,
        lesson: str,
        evidence: str,
        why: str = "",
        tree: Tree | None = None,
        ki_id: str = "",
        proposal_kind: str = "ki",
    ) -> SpawnMergeProposal: ...

    def adopt_merge_proposal(
        self,
        proposal_id: str,
        *,
        parent_library_root: Path | str | None = None,
        parent_knowledge_root: Path | str | None = None,
        reviewer: str = "human",
        review_note: str = "",
    ) -> dict[str, Any]: ...

    def reject_merge_proposal(
        self,
        proposal_id: str,
        *,
        reviewer: str = "human",
        reason: str = "",
    ) -> SpawnMergeProposal: ...

    def list_proposals(self, *, status: str | None = None) -> list[SpawnMergeProposal]: ...

    def export_dag(self, root_node_id: str | None = None) -> ExecutionGraphExport: ...


HARNESS_SPAWNER_SERVICE_KEY: ServiceKey[HarnessSpawnerProtocol] = ServiceKey("service.harness_spawner")

__all__ = ["HarnessSpawnerProtocol", "HARNESS_SPAWNER_SERVICE_KEY"]
