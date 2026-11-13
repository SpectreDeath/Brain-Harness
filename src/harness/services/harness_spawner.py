"""Child harness spawning engine, isolation realms, probe gate, and merge-back workflow.

Implements Step 1 (Option A) of harness spawning:
  - Spawns isolated child ``ServiceContext`` scopes inheriting parent registrations.
  - Enforces bounded recursion depth (default 1, hard-capped at 3).
  - Validates editable component trees (``SurfaceSpec`` + clean-tree guards) and runs a
    deterministic ``k=1`` probe trial gate before transitioning ``VALIDATED -> RUNNING``.
  - Tracks live child nodes in ``AgentExecutionGraphService`` (Rule 17) and fails closed
    on dual token/rollout/session budget exhaustion.
  - Registers a non-invasive ``parent_context.effect`` hook (Rule 19) so parent disposal
    cascades to all active child harnesses.
  - Stages learnings in child-partitioned ``ExperienceLibrary`` + draft dual-file KIs
    (Rule 40) for explicit reviewed adoption via ``adopt_merge_proposal``.
"""

from __future__ import annotations

import asyncio
import dataclasses
import inspect
import json
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.context.models import ServiceNotFoundError
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    DefaultAgentExecutionGraphService,
    ExecutionGraphExport,
    ThreadSpawnStatus,
)
from harness.services.recursive_harnessing import guards, identity
from harness.services.recursive_harnessing import surface as surface_ops
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import BRAIN_SURFACE, SurfaceSpec, Tree

logger = structlog.get_logger(__name__)

HARD_MAX_SPAWN_DEPTH: int = 3
DEFAULT_MAX_SPAWN_DEPTH: int = 1
DEFAULT_MAX_TOKENS: int = 16_000
DEFAULT_K: int = 1
DEFAULT_MAX_ROLLOUTS: int = 4
DEFAULT_MAX_SESSIONS: int = 3


class SpawnLifecycleState(str, Enum):
    """Lifecycle states of a spawned child harness."""

    SPAWNED = "SPAWNED"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETIRED = "RETIRED"


EXPERIENCE_LIBRARY_KEY: ServiceKey[ExperienceLibrary] = ServiceKey("service.experience_library")
SPAWN_DEPTH_KEY: ServiceKey[int] = ServiceKey("service.spawn_depth")
SPAWN_MAX_DEPTH_KEY: ServiceKey[int] = ServiceKey("service.spawn_max_depth")


@dataclass(slots=True, frozen=True)
class SpawnBudgetSpec:
    """Dual resource budget bounding tokens and rollout/session counts (Rules 12, 43)."""

    max_tokens: int = DEFAULT_MAX_TOKENS
    k: int = DEFAULT_K
    max_rollouts: int = DEFAULT_MAX_ROLLOUTS
    max_sessions: int = DEFAULT_MAX_SESSIONS

    def __post_init__(self) -> None:
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")
        if self.k < 1:
            raise ValueError(f"k must be >= 1, got {self.k}")
        if self.max_rollouts < 1:
            raise ValueError(f"max_rollouts must be >= 1, got {self.max_rollouts}")
        if self.max_sessions < 1:
            raise ValueError(f"max_sessions must be >= 1, got {self.max_sessions}")


@dataclass(slots=True, frozen=True)
class SpawnSpec:
    """Typed declaration of a child harness to validate, probe, and run (Rules 12, 43)."""

    name: str
    domain: str
    task: str = "spawned_harness"
    surface: SurfaceSpec = field(default_factory=lambda: BRAIN_SURFACE)
    tree: dict[str, str] = field(default_factory=dict)
    isolated_keys: tuple[str, ...] = ("service.experience_library",)
    budget: SpawnBudgetSpec = field(default_factory=SpawnBudgetSpec)
    save_dir: Path = field(default_factory=lambda: Path(".harness/spawns"))
    parent_session_id: str | None = None
    parent_spawn_id: str | None = None
    current_depth: int = 0
    max_spawn_depth: int = DEFAULT_MAX_SPAWN_DEPTH
    lifetime: str = "persistent"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("SpawnSpec.name must be non-empty")
        if not self.domain or not self.domain.strip():
            raise ValueError("SpawnSpec.domain must be non-empty")
        if self.current_depth < 0:
            raise ValueError(f"SpawnSpec.current_depth must be >= 0, got {self.current_depth}")
        if self.max_spawn_depth < 1 or self.max_spawn_depth > HARD_MAX_SPAWN_DEPTH:
            raise ValueError(
                f"SpawnSpec.max_spawn_depth={self.max_spawn_depth} must be in [1, {HARD_MAX_SPAWN_DEPTH}]"
            )
        if self.lifetime not in ("task", "persistent"):
            raise ValueError(
                f"SpawnSpec.lifetime must be 'task' or 'persistent', got {self.lifetime!r}"
            )
        if not isinstance(self.save_dir, Path):
            object.__setattr__(self, "save_dir", Path(self.save_dir))


@dataclass(slots=True, frozen=True)
class SpawnTrialResult:
    """Outcome of the admission validation + k=1 deterministic probe gate."""

    passed: bool
    fingerprint: str
    census: dict[str, int]
    probe_tokens_used: int = 0
    errors: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class SpawnMergeProposal:
    """Staged child learning awaiting explicit parent review and adoption."""

    proposal_id: str
    spawn_id: str
    domain: str
    task_id: str
    tree: dict[str, str]
    cue: str
    lesson: str
    evidence: str
    why: str = ""
    ki_id: str = ""
    status: str = "pending"

    def __post_init__(self) -> None:
        if not self.proposal_id.strip():
            raise ValueError("SpawnMergeProposal.proposal_id must be non-empty")
        if not self.spawn_id.strip():
            raise ValueError("SpawnMergeProposal.spawn_id must be non-empty")
        if not self.domain.strip():
            raise ValueError("SpawnMergeProposal.domain must be non-empty")
        if not self.task_id.strip():
            raise ValueError("SpawnMergeProposal.task_id must be non-empty")
        for field_name in ("cue", "lesson", "evidence"):
            val = getattr(self, field_name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"SpawnMergeProposal.{field_name} must be non-empty")
        if self.status not in ("pending", "adopted", "rejected"):
            raise ValueError(f"Invalid proposal status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "spawn_id": self.spawn_id,
            "domain": self.domain,
            "task_id": self.task_id,
            "tree": dict(self.tree),
            "cue": self.cue,
            "lesson": self.lesson,
            "evidence": self.evidence,
            "why": self.why,
            "ki_id": self.ki_id,
            "status": self.status,
        }


@dataclass(slots=True, frozen=True)
class SpawnedHarnessRecord:
    """Immutable snapshot of a spawned child harness and its resource consumption."""

    spawn_id: str
    name: str
    domain: str
    task: str
    state: SpawnLifecycleState
    depth: int
    max_spawn_depth: int
    parent_spawn_id: str | None
    parent_session_id: str | None
    session_id: str
    node_id: str
    fingerprint: str
    save_dir: str
    tokens_used: int
    rollouts_used: int
    sessions_used: int
    budget: SpawnBudgetSpec
    lifetime: str
    trial: SpawnTrialResult | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        trial_dict: dict[str, Any] | None = None
        if self.trial is not None:
            trial_dict = {
                "passed": self.trial.passed,
                "fingerprint": self.trial.fingerprint,
                "census": dict(self.trial.census),
                "probe_tokens_used": self.trial.probe_tokens_used,
                "errors": list(self.trial.errors),
            }
        return {
            "spawn_id": self.spawn_id,
            "name": self.name,
            "domain": self.domain,
            "task": self.task,
            "state": self.state.value,
            "depth": self.depth,
            "max_spawn_depth": self.max_spawn_depth,
            "parent_spawn_id": self.parent_spawn_id,
            "parent_session_id": self.parent_session_id,
            "session_id": self.session_id,
            "node_id": self.node_id,
            "fingerprint": self.fingerprint,
            "save_dir": self.save_dir,
            "tokens_used": self.tokens_used,
            "rollouts_used": self.rollouts_used,
            "sessions_used": self.sessions_used,
            "budget": {
                "max_tokens": self.budget.max_tokens,
                "k": self.budget.k,
                "max_rollouts": self.budget.max_rollouts,
                "max_sessions": self.budget.max_sessions,
            },
            "lifetime": self.lifetime,
            "trial": trial_dict,
            "error": self.error,
        }


@dataclass(slots=True)
class _RuntimeHandle:
    """Mutable runtime handle for live child contexts and libraries."""

    contexts: tuple[ServiceContext, ...]
    library: ExperienceLibrary
    surface: SurfaceSpec
    tree: dict[str, str]
    disposed: bool = False


@runtime_checkable
class HarnessSpawnerProtocol(Protocol):
    """Protocol for micro-kernel child harness spawning and lifecycle governance."""

    def spawn(
        self,
        spec: SpawnSpec,
        *,
        probe_fn: Callable[[SpawnSpec, ServiceContext], bool] | None = None,
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
    ) -> SpawnMergeProposal: ...

    def adopt_merge_proposal(
        self,
        proposal_id: str,
        *,
        parent_library_root: Path | str | None = None,
        parent_knowledge_root: Path | str | None = None,
    ) -> dict[str, Any]: ...

    def list_proposals(self, *, status: str | None = None) -> list[SpawnMergeProposal]: ...


HARNESS_SPAWNER_SERVICE_KEY: ServiceKey[HarnessSpawnerProtocol] = ServiceKey(
    "service.harness_spawner"
)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower()).strip("-")
    return cleaned or "spawn"


def _write_ki_dual_file(
    ki_dir: Path,
    *,
    ki_id: str,
    title: str,
    domain: str,
    spawn_id: str,
    task_id: str,
    proposal_id: str,
    cue: str,
    lesson: str,
    evidence: str,
    why: str,
    status: str,
) -> None:
    """Write a canonical dual-file Knowledge Item directory (Rule 40)."""
    ki_dir.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()
    metadata = {
        "id": ki_id,
        "title": title,
        "summary": f"{cue} -> {lesson}",
        "domain": domain,
        "status": status,
        "tags": ["spawn", _slugify(domain)],
        "created_at": now_iso,
        "updated_at": now_iso,
        "source_spawn_id": spawn_id,
        "source_proposal_id": proposal_id,
        "task_id": task_id,
        "isnad_claim": {
            "cue": cue,
            "lesson": lesson,
            "evidence": evidence,
        },
    }
    (ki_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    md_lines = [
        f"# {title}",
        "",
        f"- **KI ID**: `{ki_id}`",
        f"- **Domain**: `{domain}`",
        f"- **Status**: `{status}`",
        f"- **Source Spawn**: `{spawn_id}` (`{task_id}`)",
        f"- **Proposal ID**: `{proposal_id}`",
        "",
        "## Transferable Claim",
        f"- **Cue**: {cue}",
        f"- **Lesson**: {lesson}",
        f"- **Evidence**: {evidence}",
    ]
    if why.strip():
        md_lines.extend(["", "## Rationale", why.strip()])
    (ki_dir / "summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


async def _dispose_contexts_async(contexts: tuple[ServiceContext, ...]) -> None:
    for ctx in reversed(contexts):
        try:
            await ctx.dispose()
        except Exception as exc:
            logger.warning("child_context_dispose_error", error=str(exc))


def _dispose_contexts_sync(contexts: tuple[ServiceContext, ...]) -> None:
    """Dispose a child context stack cleanly from sync or async call sites."""
    if not contexts:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_dispose_contexts_async(contexts))
        return

    if loop.is_running():
        # Clear local registrations & run sync inverses immediately, and schedule full async dispose.
        for ctx in reversed(contexts):
            with ctx._mutation_lock:
                stack = list(ctx._dispose_stack)
                ctx._dispose_stack.clear()
                async_inverses = []
                for inv in reversed(stack):
                    try:
                        if inspect.iscoroutinefunction(inv):
                            async_inverses.append(inv)
                        else:
                            res = inv()
                            if inspect.isawaitable(res):
                                async_inverses.append(lambda r=res: r)
                    except Exception as exc:
                        logger.warning("sync_context_inverse_error", error=str(exc))
            if async_inverses:
                async def _drain(items: list[Any] = async_inverses) -> None:
                    for item in items:
                        try:
                            res = item()
                            if inspect.isawaitable(res):
                                await res
                        except Exception:
                            pass

                loop.create_task(_drain())


class HarnessSpawnerEngine(HarnessSpawnerProtocol):
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

    def spawn(
        self,
        spec: SpawnSpec,
        *,
        probe_fn: Callable[[SpawnSpec, ServiceContext], bool] | None = None,
    ) -> SpawnedHarnessRecord:
        """Validate, isolate, k=1 probe-gate, and admit a child harness."""
        parent_rec: SpawnedHarnessRecord | None = None
        if spec.parent_spawn_id is not None:
            parent_rec = self._records.get(spec.parent_spawn_id)
            if parent_rec is None:
                raise KeyError(f"Unknown parent_spawn_id: {spec.parent_spawn_id!r}")

        base_ctx: ServiceContext
        if spec.parent_spawn_id is not None and spec.parent_spawn_id in self._handles:
            base_ctx = self._handles[spec.parent_spawn_id].contexts[-1]
        elif self._parent_context is not None:
            base_ctx = self._parent_context
        else:
            base_ctx = ServiceContext()

        inherited_depth = base_ctx.optional(SPAWN_DEPTH_KEY)
        if parent_rec is not None:
            child_depth = parent_rec.depth + 1
            effective_max_depth = min(spec.max_spawn_depth, parent_rec.max_spawn_depth)
        elif inherited_depth is not None:
            child_depth = inherited_depth + 1
            inherited_max = base_ctx.optional(SPAWN_MAX_DEPTH_KEY)
            effective_max_depth = (
                min(spec.max_spawn_depth, inherited_max)
                if inherited_max is not None
                else spec.max_spawn_depth
            )
        else:
            child_depth = spec.current_depth + 1
            effective_max_depth = spec.max_spawn_depth

        if child_depth > effective_max_depth or child_depth > HARD_MAX_SPAWN_DEPTH:
            raise ValueError(
                f"Spawn recursion depth {child_depth} exceeds max_spawn_depth={effective_max_depth} "
                f"(hard cap {HARD_MAX_SPAWN_DEPTH})"
            )

        spawn_id = f"spawn_{_slugify(spec.name)}_{uuid.uuid4().hex[:8]}"
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        node_id = f"harness:{spawn_id}"
        parent_node_id: str | None = None
        if parent_rec is not None:
            parent_node_id = parent_rec.node_id
        elif spec.parent_session_id:
            parent_node_id = spec.parent_session_id
        else:
            parent_node_id = "prime"

        self._ensure_parent_graph_node(parent_node_id)

        child_save_dir = spec.save_dir / spawn_id
        child_library = ExperienceLibrary(
            root=child_save_dir / "library",
            domain=spec.domain,
            surface=spec.surface,
        )

        # Build isolated child context chain inheriting non-isolated parent services
        child_scopes: list[ServiceContext] = [base_ctx.child()]
        cur_ctx = child_scopes[0]
        isolated_meta: list[tuple[ServiceKey[Any], str]] = []
        for key_name in spec.isolated_keys:
            key_obj: ServiceKey[Any] = ServiceKey(key_name)
            key_realm = f"{key_name}:spawn:{spawn_id}"
            cur_ctx = cur_ctx.isolate(key_obj, realm=key_realm)
            child_scopes.append(cur_ctx)
            if key_name != EXPERIENCE_LIBRARY_KEY.name:
                isolated_meta.append((key_obj, key_realm))

        for iso_key, iso_realm in isolated_meta:
            def _make_isolation_guard(
                _key: ServiceKey[Any] = iso_key,
                _realm: str = iso_realm,
            ) -> Callable[[Any], Any]:
                def _guard(val: Any) -> Any:
                    if not any(_realm in sc._entries for sc in child_scopes):
                        raise ServiceNotFoundError(_key)
                    return val

                return _guard

            cur_ctx = cur_ctx.intercept(iso_key, _make_isolation_guard())
            child_scopes.append(cur_ctx)

        cur_ctx.provide(EXPERIENCE_LIBRARY_KEY, child_library, provider=spawn_id, allow_override=True)
        cur_ctx.provide(SPAWN_DEPTH_KEY, child_depth, provider=spawn_id, allow_override=True)
        cur_ctx.provide(SPAWN_MAX_DEPTH_KEY, effective_max_depth, provider=spawn_id, allow_override=True)

        self._graph_store.register_thread(
            node_id=node_id,
            role=f"harness:{spec.domain}",
            task=spec.task,
            parent_id=parent_node_id,
            metadata={
                "spawn_id": spawn_id,
                "depth": child_depth,
                "max_spawn_depth": effective_max_depth,
                "state": SpawnLifecycleState.SPAWNED.value,
                "lifetime": spec.lifetime,
            },
        )

        # Admission gate: SurfaceSpec validation + leak-free clean tree + k=1 probe check
        errors: list[str] = []
        census: dict[str, int] = {}
        try:
            guards.assert_tree_clean(spec.tree)
            census = surface_ops.validate(spec.surface, spec.tree)
        except Exception as exc:
            errors.append(str(exc))

        fp = identity.fingerprint_tree(spec.tree)
        probe_tokens = 0
        if not errors and probe_fn is not None:
            try:
                ok = bool(probe_fn(spec, cur_ctx))
                probe_tokens = min(100, spec.budget.max_tokens)
                if not ok:
                    errors.append("k=1 deterministic probe trial returned False")
            except Exception as exc:
                errors.append(f"k=1 deterministic probe raised {type(exc).__name__}: {exc}")

        trial = SpawnTrialResult(
            passed=len(errors) == 0,
            fingerprint=fp,
            census=census,
            probe_tokens_used=probe_tokens,
            errors=tuple(errors),
        )

        if not trial.passed:
            err_msg = "; ".join(errors)
            rec = SpawnedHarnessRecord(
                spawn_id=spawn_id,
                name=spec.name,
                domain=spec.domain,
                task=spec.task,
                state=SpawnLifecycleState.FAILED,
                depth=child_depth,
                max_spawn_depth=effective_max_depth,
                parent_spawn_id=spec.parent_spawn_id,
                parent_session_id=spec.parent_session_id,
                session_id=session_id,
                node_id=node_id,
                fingerprint=fp,
                save_dir=str(child_save_dir),
                tokens_used=probe_tokens,
                rollouts_used=1 if probe_fn is not None else 0,
                sessions_used=1,
                budget=spec.budget,
                lifetime=spec.lifetime,
                trial=trial,
                error=err_msg,
            )
            self._records[spawn_id] = rec
            self._handles[spawn_id] = _RuntimeHandle(
                contexts=tuple(child_scopes),
                library=child_library,
                surface=spec.surface,
                tree=dict(spec.tree),
                disposed=True,
            )
            _dispose_contexts_sync(tuple(child_scopes))
            self._graph_store.update_thread_status(
                node_id, "failed", tokens_used=probe_tokens, completed=False
            )
            self._graph_store.close_spawn_edge(
                parent_node_id, node_id, ThreadSpawnStatus.FAILED
            )
            self._save_state()
            return rec

        # Transition SPAWNED -> VALIDATED -> RUNNING and materialize validated tree
        surface_ops.write_tree(spec.surface, spec.tree, child_save_dir / "harness")
        rec = SpawnedHarnessRecord(
            spawn_id=spawn_id,
            name=spec.name,
            domain=spec.domain,
            task=spec.task,
            state=SpawnLifecycleState.RUNNING,
            depth=child_depth,
            max_spawn_depth=effective_max_depth,
            parent_spawn_id=spec.parent_spawn_id,
            parent_session_id=spec.parent_session_id,
            session_id=session_id,
            node_id=node_id,
            fingerprint=fp,
            save_dir=str(child_save_dir),
            tokens_used=probe_tokens,
            rollouts_used=1 if probe_fn is not None else 0,
            sessions_used=1,
            budget=spec.budget,
            lifetime=spec.lifetime,
            trial=trial,
            error="",
        )
        self._records[spawn_id] = rec
        self._handles[spawn_id] = _RuntimeHandle(
            contexts=tuple(child_scopes),
            library=child_library,
            surface=spec.surface,
            tree=dict(spec.tree),
            disposed=False,
        )
        if probe_tokens:
            self._graph_store.update_thread_status(node_id, "open", tokens_used=probe_tokens)
        self._save_state()
        return rec

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

        final_state = (
            SpawnLifecycleState.RETIRED if rec.lifetime == "task" else SpawnLifecycleState.COMPLETED
        )
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
            SpawnLifecycleState.FAILED
            if rec.state == SpawnLifecycleState.FAILED
            else SpawnLifecycleState.RETIRED
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
        """Stage a validated learning in the child's ExperienceLibrary & draft_kis partition."""
        rec = self._require_record(spawn_id)
        if rec.state == SpawnLifecycleState.FAILED:
            raise RuntimeError(f"Cannot propose merge-back from FAILED spawn '{spawn_id}'")

        handle = self._handles.get(spawn_id)
        surface = handle.surface if handle is not None else BRAIN_SURFACE
        candidate_tree: dict[str, str]
        if tree is not None:
            candidate_tree = dict(tree)
        elif handle is not None:
            candidate_tree = dict(handle.tree)
        else:
            candidate_tree = surface_ops.read_tree(surface, Path(rec.save_dir) / "harness")

        guards.assert_tree_clean(candidate_tree)
        surface_ops.validate(surface, candidate_tree)

        lib = self.get_child_library(spawn_id)
        assert lib is not None
        staged_path = lib.add(
            task_id,
            candidate_tree,
            why=why,
            label=rec.name,
            run_id=spawn_id,
            experience={"cue": cue, "lesson": lesson, "evidence": evidence},
        )
        if staged_path is None:
            raise ValueError("Failed to stage child ExperienceLibrary entry: unsupported lesson")

        resolved_ki_id = ki_id.strip() or f"ki-spawn-{_slugify(rec.domain)}-{_slugify(task_id)}"
        proposal_id = f"prop_{_slugify(task_id)}_{uuid.uuid4().hex[:8]}"
        proposal = SpawnMergeProposal(
            proposal_id=proposal_id,
            spawn_id=spawn_id,
            domain=rec.domain,
            task_id=task_id,
            tree=candidate_tree,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            ki_id=resolved_ki_id,
            status="pending",
        )

        draft_dir = Path(rec.save_dir) / "draft_kis" / resolved_ki_id
        _write_ki_dual_file(
            draft_dir,
            ki_id=resolved_ki_id,
            title=f"Spawn Learning: {rec.domain} ({task_id})",
            domain=rec.domain,
            spawn_id=spawn_id,
            task_id=task_id,
            proposal_id=proposal_id,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            why=why,
            status="draft",
        )

        self._proposals[proposal_id] = proposal
        self._save_state()
        return proposal

    def adopt_merge_proposal(
        self,
        proposal_id: str,
        *,
        parent_library_root: Path | str | None = None,
        parent_knowledge_root: Path | str | None = None,
    ) -> dict[str, Any]:
        """Explicitly adopt a pending child proposal into parent ExperienceLibrary & Knowledge Vault."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise KeyError(f"Unknown merge proposal: {proposal_id!r}")
        if proposal.status != "pending":
            raise ValueError(
                f"Proposal '{proposal_id}' is already {proposal.status!r} and cannot be re-adopted"
            )

        rec = self._require_record(proposal.spawn_id)
        handle = self._handles.get(proposal.spawn_id)
        surface = handle.surface if handle is not None else BRAIN_SURFACE

        guards.assert_tree_clean(proposal.tree)
        surface_ops.validate(surface, proposal.tree)

        lib_root = Path(parent_library_root) if parent_library_root is not None else Path(".harness/experience")
        parent_lib = ExperienceLibrary(root=lib_root, domain=proposal.domain, surface=surface)
        lib_entry = parent_lib.add(
            proposal.task_id,
            dict(proposal.tree),
            why=proposal.why,
            label=rec.name,
            run_id=proposal.spawn_id,
            experience={
                "cue": proposal.cue,
                "lesson": proposal.lesson,
                "evidence": proposal.evidence,
            },
        )
        if lib_entry is None:
            raise ValueError(f"Parent library rejected proposal '{proposal_id}'")

        kn_root = (
            Path(parent_knowledge_root)
            if parent_knowledge_root is not None
            else Path(".harness/knowledge")
        )
        ki_dir = kn_root / proposal.ki_id
        _write_ki_dual_file(
            ki_dir,
            ki_id=proposal.ki_id,
            title=f"Spawn Learning: {proposal.domain} ({proposal.task_id})",
            domain=proposal.domain,
            spawn_id=proposal.spawn_id,
            task_id=proposal.task_id,
            proposal_id=proposal.proposal_id,
            cue=proposal.cue,
            lesson=proposal.lesson,
            evidence=proposal.evidence,
            why=proposal.why,
            status="adopted",
        )

        adopted = dataclasses.replace(proposal, status="adopted")
        self._proposals[proposal_id] = adopted
        self._save_state()
        return {
            "proposal_id": proposal_id,
            "status": "adopted",
            "domain": proposal.domain,
            "library_entry": str(lib_entry),
            "knowledge_dir": str(ki_dir),
            "ki_id": proposal.ki_id,
        }

    def list_proposals(self, *, status: str | None = None) -> list[SpawnMergeProposal]:
        items = list(self._proposals.values())
        if status is not None:
            items = [p for p in items if p.status == status]
        return items

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


__all__ = [
    "DEFAULT_K",
    "DEFAULT_MAX_ROLLOUTS",
    "DEFAULT_MAX_SESSIONS",
    "DEFAULT_MAX_SPAWN_DEPTH",
    "DEFAULT_MAX_TOKENS",
    "EXPERIENCE_LIBRARY_KEY",
    "HARD_MAX_SPAWN_DEPTH",
    "HARNESS_SPAWNER_SERVICE_KEY",
    "SPAWN_DEPTH_KEY",
    "SPAWN_MAX_DEPTH_KEY",
    "HarnessSpawnerEngine",
    "HarnessSpawnerProtocol",
    "SpawnBudgetSpec",
    "SpawnLifecycleState",
    "SpawnMergeProposal",
    "SpawnSpec",
    "SpawnTrialResult",
    "SpawnedHarnessRecord",
]
