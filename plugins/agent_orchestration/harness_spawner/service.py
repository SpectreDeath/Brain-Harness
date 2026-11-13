"""Service facade for the harness_spawner plugin delegating to HarnessSpawnerEngine (Rule 49)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext
from harness.services.agent_graph import AgentExecutionGraphService
from harness.services.harness_spawner import (
    DEFAULT_MAX_SPAWN_DEPTH,
    DEFAULT_MAX_TOKENS,
    HarnessSpawnerEngine,
    HarnessSpawnerProtocol,
    SpawnBudgetSpec,
    SpawnedHarnessRecord,
    SpawnLifecycleState,
    SpawnMergeProposal,
    SpawnSpec,
)
from harness.services.recursive_harnessing.models import Tree


class DefaultHarnessSpawnerService(HarnessSpawnerProtocol):
    """Thin plugin service adapter over HarnessSpawnerEngine."""

    def __init__(
        self,
        parent_context: ServiceContext | None = None,
        graph_store: AgentExecutionGraphService | None = None,
        state_file: Path | str | None = None,
    ) -> None:
        self._engine = HarnessSpawnerEngine(
            parent_context=parent_context,
            graph_store=graph_store,
            state_file=state_file,
        )

    @property
    def engine(self) -> HarnessSpawnerEngine:
        return self._engine

    def spawn(
        self,
        spec: SpawnSpec,
        *,
        probe_fn: Callable[[SpawnSpec, ServiceContext], bool] | None = None,
    ) -> SpawnedHarnessRecord:
        return self._engine.spawn(spec, probe_fn=probe_fn)

    def record_usage(
        self,
        spawn_id: str,
        *,
        tokens: int = 0,
        rollouts: int = 0,
        sessions: int = 0,
    ) -> SpawnedHarnessRecord:
        return self._engine.record_usage(
            spawn_id, tokens=tokens, rollouts=rollouts, sessions=sessions
        )

    def complete(
        self,
        spawn_id: str,
        *,
        tokens_used: int = 0,
    ) -> SpawnedHarnessRecord:
        return self._engine.complete(spawn_id, tokens_used=tokens_used)

    def retire(self, spawn_id: str) -> SpawnedHarnessRecord:
        return self._engine.retire(spawn_id)

    def retire_all(self) -> list[SpawnedHarnessRecord]:
        return self._engine.retire_all()

    async def aretire_all(self) -> list[SpawnedHarnessRecord]:
        return await self._engine.aretire_all()

    def get_spawn(self, spawn_id: str) -> SpawnedHarnessRecord | None:
        return self._engine.get_spawn(spawn_id)

    def list_spawns(
        self, *, state: SpawnLifecycleState | None = None
    ) -> list[SpawnedHarnessRecord]:
        return self._engine.list_spawns(state=state)

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
    ) -> SpawnMergeProposal:
        return self._engine.propose_merge_back(
            spawn_id,
            task_id=task_id,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            tree=tree,
            ki_id=ki_id,
        )

    def adopt_merge_proposal(
        self,
        proposal_id: str,
        *,
        parent_library_root: Path | str | None = None,
        parent_knowledge_root: Path | str | None = None,
    ) -> dict[str, Any]:
        return self._engine.adopt_merge_proposal(
            proposal_id,
            parent_library_root=parent_library_root,
            parent_knowledge_root=parent_knowledge_root,
        )

    def list_proposals(self, *, status: str | None = None) -> list[SpawnMergeProposal]:
        return self._engine.list_proposals(status=status)

    def execute(self, action: str, **kwargs: Any) -> Any:
        """Generic action dispatcher for plugin entrypoint calls."""
        if action == "spawn":
            spec = kwargs.get("spec")
            if spec is None:
                name = str(kwargs["name"])
                domain = str(kwargs["domain"])
                task = str(kwargs.get("task", "spawned_harness"))
                tree = dict(kwargs.get("tree") or {"AGENTS.md": f"# {name}\nDomain: {domain}\nTask: {task}\n"})
                spec = SpawnSpec(
                    name=name,
                    domain=domain,
                    task=task,
                    tree=tree,
                    budget=SpawnBudgetSpec(
                        max_tokens=int(kwargs.get("max_tokens", DEFAULT_MAX_TOKENS)),
                    ),
                    max_spawn_depth=int(kwargs.get("max_spawn_depth", DEFAULT_MAX_SPAWN_DEPTH)),
                    lifetime=str(kwargs.get("lifetime", "persistent")),
                    save_dir=Path(kwargs.get("save_dir", ".harness/spawns")),
                )
            return self.spawn(spec, probe_fn=kwargs.get("probe_fn")).to_dict()
        if action == "list":
            return [r.to_dict() for r in self.list_spawns()]
        if action == "retire":
            return self.retire(str(kwargs["spawn_id"])).to_dict()
        if action == "retire_all":
            return [r.to_dict() for r in self.retire_all()]
        if action == "adopt":
            return self.adopt_merge_proposal(
                str(kwargs["proposal_id"]),
                parent_library_root=kwargs.get("parent_library_root"),
                parent_knowledge_root=kwargs.get("parent_knowledge_root"),
            )
        raise ValueError(f"Unsupported harness_spawner action: {action!r}")
