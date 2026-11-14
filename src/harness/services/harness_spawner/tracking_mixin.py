"""HarnessSpawnerEngine mixin module: tracking_mixin."""

from __future__ import annotations

import dataclasses

from harness.services.agent_graph import ThreadSpawnStatus

from .models import (
    SpawnLifecycleState,
    SpawnedHarnessRecord,
)
from .helpers import (
    _dispose_contexts_async,
    _dispose_contexts_sync,
)


class _SpawnerTrackingMixin:
    """Mixin supplying tracking mixin operations."""

    def record_usage(
        self,
        spawn_id: str,
        *,
        tokens: int = 0,
        rollouts: int = 0,
        sessions: int = 0,
    ) -> SpawnedHarnessRecord:
        """Increment dual budget counters and fail closed if any budget ceiling is exceeded."""
        rec = self._require_record(spawn_id)
        if rec.state in (SpawnLifecycleState.FAILED, SpawnLifecycleState.RETIRED):
            raise RuntimeError(f"Cannot record usage on inactive spawn '{spawn_id}' ({rec.state.value})")
        if tokens < 0 or rollouts < 0 or sessions < 0:
            raise ValueError("Usage increments must be non-negative")

        new_tokens = rec.tokens_used + tokens
        new_rollouts = rec.rollouts_used + rollouts
        new_sessions = rec.sessions_used + sessions

        breach: str | None = None
        if new_tokens > rec.budget.max_tokens:
            breach = f"Token budget exceeded: {new_tokens} > {rec.budget.max_tokens}"
        elif new_rollouts > rec.budget.max_rollouts:
            breach = f"Rollout budget exceeded: {new_rollouts} > {rec.budget.max_rollouts}"
        elif new_sessions > rec.budget.max_sessions:
            breach = f"Session budget exceeded: {new_sessions} > {rec.budget.max_sessions}"

        if breach is not None:
            failed_rec = dataclasses.replace(
                rec,
                state=SpawnLifecycleState.FAILED,
                tokens_used=new_tokens,
                rollouts_used=new_rollouts,
                sessions_used=new_sessions,
                error=breach,
            )
            self._records[spawn_id] = failed_rec
            handle = self._handles.get(spawn_id)
            if handle is not None and not handle.disposed:
                _dispose_contexts_sync(handle.contexts)
                handle.disposed = True
            self._safe_update_graph(rec, "failed", tokens_delta=tokens, edge_status=ThreadSpawnStatus.FAILED)
            self._save_state()
            raise RuntimeError(breach)

        updated = dataclasses.replace(
            rec,
            tokens_used=new_tokens,
            rollouts_used=new_rollouts,
            sessions_used=new_sessions,
        )
        self._records[spawn_id] = updated
        if tokens and rec.node_id in getattr(self._graph_store, "_nodes", {}):
            self._graph_store.update_thread_status(rec.node_id, "open", tokens_used=tokens)
        self._save_state()
        return updated

    def complete(
        self,
        spawn_id: str,
        *,
        tokens_used: int = 0,
    ) -> SpawnedHarnessRecord:
        """Mark a running child harness completed; task-scoped children auto-retire."""
        rec = self._require_record(spawn_id)
        if tokens_used:
            rec = self.record_usage(spawn_id, tokens=tokens_used)

        final_state = SpawnLifecycleState.RETIRED if rec.lifetime == "task" else SpawnLifecycleState.COMPLETED
        updated = dataclasses.replace(rec, state=final_state)
        self._records[spawn_id] = updated
        self._safe_update_graph(
            rec,
            "completed",
            tokens_delta=0,
            completed=True,
            edge_status=ThreadSpawnStatus.COMPLETED,
        )
        if rec.lifetime == "task":
            handle = self._handles.get(spawn_id)
            if handle is not None and not handle.disposed:
                _dispose_contexts_sync(handle.contexts)
                handle.disposed = True
        self._save_state()
        return updated

    def retire(self, spawn_id: str) -> SpawnedHarnessRecord:
        """Dispose child contexts, close DAG spawn edge, and mark RETIRED."""
        rec = self._require_record(spawn_id)
        handle = self._handles.get(spawn_id)
        if handle is not None and not handle.disposed:
            _dispose_contexts_sync(handle.contexts)
            handle.disposed = True
        target_state = (
            SpawnLifecycleState.FAILED if rec.state == SpawnLifecycleState.FAILED else SpawnLifecycleState.RETIRED
        )
        updated = dataclasses.replace(rec, state=target_state)
        self._records[spawn_id] = updated
        self._safe_update_graph(
            rec,
            "completed" if target_state == SpawnLifecycleState.RETIRED else "failed",
            completed=(target_state == SpawnLifecycleState.RETIRED),
            edge_status=ThreadSpawnStatus.CLOSED,
        )
        self._save_state()
        return updated

    def retire_all(self) -> list[SpawnedHarnessRecord]:
        """Retire every active child harness synchronously."""
        retired: list[SpawnedHarnessRecord] = []
        for spawn_id, rec in list(self._records.items()):
            if rec.state in (
                SpawnLifecycleState.SPAWNED,
                SpawnLifecycleState.VALIDATED,
                SpawnLifecycleState.RUNNING,
                SpawnLifecycleState.COMPLETED,
            ):
                retired.append(self.retire(spawn_id))
        return retired

    async def aretire_all(self) -> list[SpawnedHarnessRecord]:
        """Async cascade disposal helper executed by ``parent_context.effect``."""
        retired: list[SpawnedHarnessRecord] = []
        for spawn_id, rec in list(self._records.items()):
            if rec.state in (
                SpawnLifecycleState.SPAWNED,
                SpawnLifecycleState.VALIDATED,
                SpawnLifecycleState.RUNNING,
                SpawnLifecycleState.COMPLETED,
            ):
                handle = self._handles.get(spawn_id)
                if handle is not None and not handle.disposed:
                    await _dispose_contexts_async(handle.contexts)
                    handle.disposed = True
                updated = dataclasses.replace(rec, state=SpawnLifecycleState.RETIRED)
                self._records[spawn_id] = updated
                self._safe_update_graph(
                    rec,
                    "completed",
                    completed=True,
                    edge_status=ThreadSpawnStatus.CLOSED,
                )
                retired.append(updated)
        if retired:
            self._save_state()
        return retired

    def get_spawn(self, spawn_id: str) -> SpawnedHarnessRecord | None:
        return self._records.get(spawn_id)

    def list_spawns(
        self,
        *,
        state: SpawnLifecycleState | None = None,
    ) -> list[SpawnedHarnessRecord]:
        items = list(self._records.values())
        if state is not None:
            items = [r for r in items if r.state == state]
        return items


__all__ = ["_SpawnerTrackingMixin"]
