"""Harness Spawner Plugin — IoC provider, lifecycle management, and tool entrypoints (Rule 45)."""

from __future__ import annotations

import sys
from collections.abc import Callable
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
from harness.services.recursive_harnessing.models import Tree  # noqa: E402

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

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultHarnessSpawnerService()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [HARNESS_SPAWNER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    @property
    def engine(self) -> Any:
        return self._service.engine

    async def on_load(self, context: ServiceContext) -> None:
        self._service = DefaultHarnessSpawnerService(parent_context=context)
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
    ) -> SpawnedHarnessRecord:
        return self._service.spawn(spec, probe_fn=probe_fn)

    def record_usage(
        self,
        spawn_id: str,
        *,
        tokens: int = 0,
        rollouts: int = 0,
        sessions: int = 0,
    ) -> SpawnedHarnessRecord:
        return self._service.record_usage(
            spawn_id, tokens=tokens, rollouts=rollouts, sessions=sessions
        )

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

    def list_spawns(
        self, *, state: SpawnLifecycleState | None = None
    ) -> list[SpawnedHarnessRecord]:
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
        )

    def adopt_merge_proposal(
        self,
        proposal_id: str,
        *,
        parent_library_root: Path | str | None = None,
        parent_knowledge_root: Path | str | None = None,
    ) -> dict[str, Any]:
        return self._service.adopt_merge_proposal(
            proposal_id,
            parent_library_root=parent_library_root,
            parent_knowledge_root=parent_knowledge_root,
        )

    def list_proposals(self, *, status: str | None = None) -> list[SpawnMergeProposal]:
        return self._service.list_proposals(status=status)


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
