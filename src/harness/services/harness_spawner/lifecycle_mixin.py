"""HarnessSpawnerEngine mixin module: lifecycle_mixin."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from harness.kernel.context import (
    ServiceContext,
    ServiceKey,
)
from harness.kernel.context.models import ServiceNotFoundError
from harness.services.agent_graph import ThreadSpawnStatus
from harness.services.recursive_harnessing import (
    guards,
    identity,
    surface as surface_ops,
)
from harness.services.recursive_harnessing.library import ExperienceLibrary

from .models import (
    EXPERIENCE_LIBRARY_KEY,
    HARD_MAX_SPAWN_DEPTH,
    SPAWN_DEPTH_KEY,
    SPAWN_MAX_DEPTH_KEY,
    SpawnLifecycleState,
    SpawnSpec,
    SpawnTrialResult,
    SpawnedHarnessRecord,
)
from .helpers import (
    _build_spawn_record_and_handle,
    _dispose_contexts_sync,
    _slugify,
)


class _SpawnerLifecycleMixin:
    """Mixin supplying lifecycle mixin operations."""

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
                min(spec.max_spawn_depth, inherited_max) if inherited_max is not None else spec.max_spawn_depth
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
            rec, handle = _build_spawn_record_and_handle(
                spawn_id=spawn_id,
                spec=spec,
                state=SpawnLifecycleState.FAILED,
                child_depth=child_depth,
                effective_max_depth=effective_max_depth,
                session_id=session_id,
                node_id=node_id,
                fingerprint=fp,
                child_save_dir=child_save_dir,
                probe_tokens=probe_tokens,
                has_probe=probe_fn is not None,
                trial=trial,
                error=err_msg,
                child_scopes=tuple(child_scopes),
                child_library=child_library,
                disposed=True,
            )
            self._records[spawn_id] = rec
            self._handles[spawn_id] = handle
            _dispose_contexts_sync(tuple(child_scopes))
            self._graph_store.update_thread_status(node_id, "failed", tokens_used=probe_tokens, completed=False)
            self._graph_store.close_spawn_edge(parent_node_id, node_id, ThreadSpawnStatus.FAILED)
            self._save_state()
            return rec

        # Transition SPAWNED -> VALIDATED -> RUNNING and materialize validated tree
        surface_ops.write_tree(spec.surface, spec.tree, child_save_dir / "harness")
        rec, handle = _build_spawn_record_and_handle(
            spawn_id=spawn_id,
            spec=spec,
            state=SpawnLifecycleState.RUNNING,
            child_depth=child_depth,
            effective_max_depth=effective_max_depth,
            session_id=session_id,
            node_id=node_id,
            fingerprint=fp,
            child_save_dir=child_save_dir,
            probe_tokens=probe_tokens,
            has_probe=probe_fn is not None,
            trial=trial,
            error="",
            child_scopes=tuple(child_scopes),
            child_library=child_library,
            disposed=False,
        )
        self._records[spawn_id] = rec
        self._handles[spawn_id] = handle
        if probe_tokens:
            self._graph_store.update_thread_status(node_id, "open", tokens_used=probe_tokens)
        self._save_state()
        return rec


__all__ = ["_SpawnerLifecycleMixin"]
