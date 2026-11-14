"""HarnessSpawnerEngine mixin module: persistence_mixin."""

from __future__ import annotations

import json

from harness.services.agent_graph import (
    ExecutionGraphExport,
    ThreadSpawnStatus,
)

from .models import (
    DEFAULT_K,
    DEFAULT_MAX_ROLLOUTS,
    DEFAULT_MAX_SESSIONS,
    DEFAULT_MAX_SPAWN_DEPTH,
    DEFAULT_MAX_TOKENS,
    SpawnBudgetSpec,
    SpawnLifecycleState,
    SpawnMergeProposal,
    SpawnTrialResult,
    SpawnedHarnessRecord,
)
from .helpers import logger


class _SpawnerPersistenceMixin:
    """Mixin supplying persistence mixin operations."""

    def export_dag(self, root_node_id: str | None = None) -> ExecutionGraphExport:
        return self._graph_store.export_graph(root_node_id)

    def _require_record(self, spawn_id: str) -> SpawnedHarnessRecord:
        rec = self._records.get(spawn_id)
        if rec is None:
            raise KeyError(f"Unknown spawn_id: {spawn_id!r}")
        return rec

    def _ensure_parent_graph_node(self, parent_node_id: str) -> None:
        nodes = getattr(self._graph_store, "_nodes", None)
        if isinstance(nodes, dict) and parent_node_id not in nodes:
            self._graph_store.register_thread(
                node_id=parent_node_id,
                role="prime",
                task="Root harness coordinator",
                parent_id=None,
                metadata={"depth": 0},
            )

    def _safe_update_graph(
        self,
        rec: SpawnedHarnessRecord,
        status: str,
        *,
        tokens_delta: int = 0,
        completed: bool = False,
        edge_status: ThreadSpawnStatus | None = None,
    ) -> None:
        nodes = getattr(self._graph_store, "_nodes", None)
        if isinstance(nodes, dict) and rec.node_id in nodes:
            self._graph_store.update_thread_status(
                rec.node_id,
                status,
                tokens_used=tokens_delta,
                completed=completed,
            )
            parent_node = nodes[rec.node_id].parent_id
            if edge_status is not None and parent_node:
                self._graph_store.close_spawn_edge(parent_node, rec.node_id, edge_status)

    def _save_state(self) -> None:
        if self._state_file is None:
            return
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "spawns": [rec.to_dict() for rec in self._records.values()],
            "proposals": [prop.to_dict() for prop in self._proposals.values()],
        }
        self._state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_state(self) -> None:
        if self._state_file is None or not self._state_file.is_file():
            return
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            logger.warning("spawn_state_load_error", path=str(self._state_file), error=str(exc))
            return

        for item in raw.get("spawns") or []:
            b_raw = item.get("budget") or {}
            budget = SpawnBudgetSpec(
                max_tokens=int(b_raw.get("max_tokens", DEFAULT_MAX_TOKENS)),
                k=int(b_raw.get("k", DEFAULT_K)),
                max_rollouts=int(b_raw.get("max_rollouts", DEFAULT_MAX_ROLLOUTS)),
                max_sessions=int(b_raw.get("max_sessions", DEFAULT_MAX_SESSIONS)),
            )
            t_raw = item.get("trial")
            trial = (
                SpawnTrialResult(
                    passed=bool(t_raw.get("passed", False)),
                    fingerprint=str(t_raw.get("fingerprint", "")),
                    census=dict(t_raw.get("census") or {}),
                    probe_tokens_used=int(t_raw.get("probe_tokens_used", 0)),
                    errors=tuple(t_raw.get("errors") or []),
                )
                if isinstance(t_raw, dict)
                else None
            )
            rec = SpawnedHarnessRecord(
                spawn_id=str(item["spawn_id"]),
                name=str(item["name"]),
                domain=str(item["domain"]),
                task=str(item.get("task", "spawned_harness")),
                state=SpawnLifecycleState(str(item["state"])),
                depth=int(item.get("depth", 1)),
                max_spawn_depth=int(item.get("max_spawn_depth", DEFAULT_MAX_SPAWN_DEPTH)),
                parent_spawn_id=item.get("parent_spawn_id"),
                parent_session_id=item.get("parent_session_id"),
                session_id=str(item["session_id"]),
                node_id=str(item["node_id"]),
                fingerprint=str(item.get("fingerprint", "")),
                save_dir=str(item.get("save_dir", "")),
                tokens_used=int(item.get("tokens_used", 0)),
                rollouts_used=int(item.get("rollouts_used", 0)),
                sessions_used=int(item.get("sessions_used", 1)),
                budget=budget,
                lifetime=str(item.get("lifetime", "persistent")),
                trial=trial,
                error=str(item.get("error", "")),
            )
            self._records[rec.spawn_id] = rec

        for p_item in raw.get("proposals") or []:
            prop = SpawnMergeProposal(
                proposal_id=str(p_item["proposal_id"]),
                spawn_id=str(p_item["spawn_id"]),
                domain=str(p_item["domain"]),
                task_id=str(p_item["task_id"]),
                tree=dict(p_item.get("tree") or {}),
                cue=str(p_item["cue"]),
                lesson=str(p_item["lesson"]),
                evidence=str(p_item["evidence"]),
                why=str(p_item.get("why", "")),
                ki_id=str(p_item.get("ki_id", "")),
                status=str(p_item.get("status", "pending")),
            )
            self._proposals[prop.proposal_id] = prop


__all__ = ["_SpawnerPersistenceMixin"]
