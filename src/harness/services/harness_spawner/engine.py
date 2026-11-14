"""HarnessSpawnerEngine coordinator implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    DefaultAgentExecutionGraphService,
)
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import BRAIN_SURFACE

from .models import (
    SpawnLifecycleState,
    SpawnMergeProposal,
    SpawnedHarnessRecord,
    _RuntimeHandle,
)
from .protocols import HarnessSpawnerProtocol
from .lifecycle_mixin import _SpawnerLifecycleMixin
from .tracking_mixin import _SpawnerTrackingMixin
from .merge_mixin import _SpawnerMergeMixin
from .persistence_mixin import _SpawnerPersistenceMixin


class HarnessSpawnerEngine(
    _SpawnerLifecycleMixin,
    _SpawnerTrackingMixin,
    _SpawnerMergeMixin,
    _SpawnerPersistenceMixin,
    HarnessSpawnerProtocol,
):
    """Micro-kernel coordinator for spawning, gating, supervising, and retiring child harnesses."""

    def __init__(
        self,
        parent_context: ServiceContext | None = None,
        graph_store: AgentExecutionGraphService | None = None,
        state_file: Path | str | None = None,
    ) -> None:
        self._parent_context = parent_context
        resolved_graph = graph_store
        if resolved_graph is None and parent_context is not None:
            resolved_graph = parent_context.optional(AGENT_GRAPH_STORE_KEY)
        self._graph_store: AgentExecutionGraphService = (
            resolved_graph if resolved_graph is not None else DefaultAgentExecutionGraphService()
        )
        self._state_file: Path | None = Path(state_file) if state_file is not None else None
        self._records: dict[str, SpawnedHarnessRecord] = {}
        self._handles: dict[str, _RuntimeHandle] = {}
        self._proposals: dict[str, SpawnMergeProposal] = {}
        self._effect_disposer: Any = None

        if parent_context is not None:

            def _register_cascade() -> Any:
                async def _cascade_inverse() -> None:
                    await self.aretire_all()

                return _cascade_inverse

            self._effect_disposer = parent_context.effect(_register_cascade)

        if self._state_file is not None and self._state_file.is_file():
            self._load_state()

    @property
    def graph_store(self) -> AgentExecutionGraphService:
        return self._graph_store

    def get_child_context(self, spawn_id: str) -> ServiceContext | None:
        """Return the outermost isolated ServiceContext for a spawned harness, if live in-memory."""
        handle = self._handles.get(spawn_id)
        if handle is None or not handle.contexts:
            return None
        return handle.contexts[-1]

    def get_child_library(self, spawn_id: str) -> ExperienceLibrary | None:
        """Return the child-scoped ExperienceLibrary for a spawn record."""
        handle = self._handles.get(spawn_id)
        if handle is not None:
            return handle.library
        rec = self._records.get(spawn_id)
        if rec is None:
            return None
        return ExperienceLibrary(
            root=Path(rec.save_dir) / "library",
            domain=rec.domain,
            surface=BRAIN_SURFACE,
        )

    def is_disposed(self, spawn_id: str) -> bool:
        handle = self._handles.get(spawn_id)
        if handle is not None:
            return handle.disposed
        rec = self._records.get(spawn_id)
        return rec is not None and rec.state in (SpawnLifecycleState.RETIRED, SpawnLifecycleState.FAILED)


__all__ = ["HarnessSpawnerEngine"]
