"""Harness Spawner Plugin — IoC provider, lifecycle management, and tool entrypoints (Rule 45)."""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.agent_graph import ExecutionGraphExport  # noqa: E402
from harness.services.dock import DefaultDockService  # noqa: E402
from harness.services.harness_spawner import (  # noqa: E402
    DEFAULT_MAX_SPAWN_DEPTH,
    DEFAULT_MAX_TOKENS,
    HARNESS_SPAWNER_SERVICE_KEY,
    HarnessSpawnerProtocol,
    SpawnBudgetSpec,
    SpawnedHarnessRecord,
    SpawnLifecycleState,
    SpawnMergeProposal,
    SpawnSpec,
)
from harness.services.recursive_harnessing.models import BRAIN_SURFACE, SurfaceSpec, Tree  # noqa: E402

try:
    from .service import DefaultHarnessSpawnerService
except ImportError:
    from service import DefaultHarnessSpawnerService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class HarnessSpawnerPlugin(HarnessPlugin, HarnessSpawnerProtocol):
    """HarnessPlugin providing child harness spawning into the IoC container (Rules 1, 2, 45)."""

    name = "harness.plugin.harness_spawner"
    version = "0.1.0"
    description = (
        "First-class child harness spawning service with child ServiceContext isolation, "
        "k=1 probe trial gates, dual budgets, DAG tracking, and reviewed merge-back"
    )
    trusted = True

    def __init__(self, state_file: Path | str | None = None) -> None:
        super().__init__()
        self._state_file: Path | None = Path(state_file) if state_file is not None else None
        self._parent_context: ServiceContext | None = None
        self._service = DefaultHarnessSpawnerService(state_file=self._state_file)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [HARNESS_SPAWNER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    @property
    def engine(self) -> Any:
        return self._service.engine

    def for_state_file(self, state_file: Path | str | None) -> HarnessSpawnerPlugin:
        """Return a plugin-backed spawner scoped to ``state_file`` while preserving IoC context."""
        scoped = HarnessSpawnerPlugin(state_file=state_file)
        scoped._parent_context = self._parent_context
        if self._parent_context is not None:
            scoped._service = DefaultHarnessSpawnerService(
                parent_context=self._parent_context,
                state_file=state_file,
            )
        return scoped

    async def on_load(self, context: ServiceContext) -> None:
        self._parent_context = context
        self._service = DefaultHarnessSpawnerService(
            parent_context=context,
            state_file=self._state_file,
        )
        context.provide(HARNESS_SPAWNER_SERVICE_KEY, self, provider=self.name)
        logger.info("HarnessSpawnerPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        await self._service.aretire_all()

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    def spawn(
        self,
        spec: SpawnSpec,
        *,
        probe_fn: Callable[[SpawnSpec, ServiceContext], bool] | None = None,
        materialize_dir: Path | str | None = None,
        dock_service: Any = None,
        approve_dock: bool = False,
    ) -> SpawnedHarnessRecord:
        return self._service.spawn(
            spec,
            probe_fn=probe_fn,
            materialize_dir=materialize_dir,
            dock_service=dock_service,
            approve_dock=approve_dock,
        )

    def record_usage(
        self,
        spawn_id: str,
        *,
        tokens: int = 0,
        rollouts: int = 0,
        sessions: int = 0,
    ) -> SpawnedHarnessRecord:
        return self._service.record_usage(spawn_id, tokens=tokens, rollouts=rollouts, sessions=sessions)

    def complete(
        self,
        spawn_id: str,
        *,
        tokens_used: int = 0,
    ) -> SpawnedHarnessRecord:
        return self._service.complete(spawn_id, tokens_used=tokens_used)

    def retire(self, spawn_id: str) -> SpawnedHarnessRecord:
        return self._service.retire(spawn_id)

    def retire_all(self) -> list[SpawnedHarnessRecord]:
        return self._service.retire_all()

    def get_spawn(self, spawn_id: str) -> SpawnedHarnessRecord | None:
        return self._service.get_spawn(spawn_id)

    def list_spawns(self, *, state: SpawnLifecycleState | None = None) -> list[SpawnedHarnessRecord]:
        return self._service.list_spawns(state=state)

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
    ) -> SpawnMergeProposal:
        return self._service.propose_merge_back(
            spawn_id,
            task_id=task_id,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            tree=tree,
            ki_id=ki_id,
            proposal_kind=proposal_kind,
        )

    def adopt_merge_proposal(
        self,
        proposal_id: str,
        *,
        parent_library_root: Path | str | None = None,
        parent_knowledge_root: Path | str | None = None,
        reviewer: str = "human",
        review_note: str = "",
    ) -> dict[str, Any]:
        return self._service.adopt_merge_proposal(
            proposal_id,
            parent_library_root=parent_library_root,
            parent_knowledge_root=parent_knowledge_root,
            reviewer=reviewer,
            review_note=review_note,
        )

    def reject_merge_proposal(
        self,
        proposal_id: str,
        *,
        reviewer: str = "human",
        reason: str = "",
    ) -> SpawnMergeProposal:
        return self._service.reject_merge_proposal(
            proposal_id,
            reviewer=reviewer,
            reason=reason,
        )

    def list_proposals(self, *, status: str | None = None) -> list[SpawnMergeProposal]:
        return self._service.list_proposals(status=status)

    def materialize(
        self,
        surface: SurfaceSpec,
        tree: Mapping[str, str],
        target_dir: Path | str,
        *,
        name: str,
        description: str = "",
        dock_service: DefaultDockService | None = None,
        approve: bool = False,
    ) -> dict[str, Any]:
        """Materialize a validated tree as a dock-linked repo via the plugin service."""
        return self._service.materialize(
            surface,
            tree,
            target_dir,
            name=name,
            description=description,
            dock_service=dock_service,
            approve=approve,
        )

    def check_drift(
        self,
        target_dir: Path | str,
        surface: SurfaceSpec = BRAIN_SURFACE,
        *,
        expected_tree_sha256: str | None = None,
        dock_service: DefaultDockService | None = None,
        dock_name: str | None = None,
    ) -> dict[str, Any]:
        """Detect manifest or tree digest drift on a materialized repo via the plugin service."""
        return self._service.check_drift(
            target_dir,
            surface,
            expected_tree_sha256=expected_tree_sha256,
            dock_service=dock_service,
            dock_name=dock_name,
        )

    def export_dag(self, root_node_id: str | None = None) -> ExecutionGraphExport:
        """Export the ExecutionGraph for spawned child harnesses via the plugin service."""
        return self._service.export_dag(root_node_id)


plugin = HarnessSpawnerPlugin()


def spawn_child_harness(
    name: str,
    domain: str,
    task: str = "spawned_harness",
    max_tokens: int = DEFAULT_MAX_TOKENS,
    max_spawn_depth: int = DEFAULT_MAX_SPAWN_DEPTH,
    lifetime: str = "persistent",
    save_dir: str | Path = ".harness/spawns",
) -> dict[str, Any]:
    """Tool entrypoint spawning a child harness with default isolated ExperienceLibrary."""
    spec = SpawnSpec(
        name=name,
        domain=domain,
        task=task,
        tree={"AGENTS.md": f"# Spawned Harness: {name}\n\nDomain: {domain}\nTask: {task}\n"},
        budget=SpawnBudgetSpec(max_tokens=max_tokens),
        max_spawn_depth=max_spawn_depth,
        lifetime=lifetime,
        save_dir=Path(save_dir),
    )
    return plugin.spawn(spec).to_dict()
