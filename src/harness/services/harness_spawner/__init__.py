"""Micro-kernel Child Harness Spawning, Recursion Depth Governance, and Memory Merge-Back."""

from __future__ import annotations

from .diff_review import (
    TreeDiffReview,
    build_tree_diff_review,
    compute_tree_sha256,
    verify_diff_approval,
)
from .engine import HarnessSpawnerEngine
from .materialize import (
    check_materialized_drift,
    materialize_spawn_as_dock,
)
from .helpers import (
    _dispose_contexts_async,
    _dispose_contexts_sync,
    _slugify,
    _write_ki_dual_file,
    logger,
)
from .models import (
    DEFAULT_K,
    DEFAULT_MAX_ROLLOUTS,
    DEFAULT_MAX_SESSIONS,
    DEFAULT_MAX_SPAWN_DEPTH,
    DEFAULT_MAX_TOKENS,
    EXPERIENCE_LIBRARY_KEY,
    HARD_MAX_SPAWN_DEPTH,
    SPAWN_DEPTH_KEY,
    SPAWN_MAX_DEPTH_KEY,
    SpawnBudgetSpec,
    SpawnedHarnessRecord,
    SpawnLifecycleState,
    SpawnMergeProposal,
    SpawnSpec,
    SpawnTrialResult,
    _RuntimeHandle,
)
from .protocols import HARNESS_SPAWNER_SERVICE_KEY, HarnessSpawnerProtocol

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
    "TreeDiffReview",
    "build_tree_diff_review",
    "check_materialized_drift",
    "compute_tree_sha256",
    "materialize_spawn_as_dock",
    "verify_diff_approval",
]
