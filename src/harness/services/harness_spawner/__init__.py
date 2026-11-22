"""Micro-kernel Child Harness Spawning, Recursion Depth Governance, and Memory Merge-Back."""

from __future__ import annotations

from .blueprints import (
    DEFAULT_MAX_BLUEPRINT_SKILLS,
    HARD_MAX_BLUEPRINT_SKILLS,
    HarnessBlueprint,
    SeededKI,
    build_blueprint_tree,
    recommend_harness_blueprints,
)
from .cold_walk import (
    ColdWalkPoint,
    ColdWalkReport,
    format_cold_walk_markdown,
    run_cold_walk,
)
from .diff_review import (
    TreeDiffReview,
    build_tree_diff_review,
    compute_tree_sha256,
    verify_diff_approval,
)
from .doc_bundle import (
    TRACKED_DOC_PATHS,
    HarnessDocContext,
    build_harness_docs,
    compute_docs_sha256,
    validate_harness_docs,
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
    "DEFAULT_MAX_BLUEPRINT_SKILLS",
    "DEFAULT_MAX_ROLLOUTS",
    "DEFAULT_MAX_SESSIONS",
    "DEFAULT_MAX_SPAWN_DEPTH",
    "DEFAULT_MAX_TOKENS",
    "EXPERIENCE_LIBRARY_KEY",
    "HARD_MAX_BLUEPRINT_SKILLS",
    "HARD_MAX_SPAWN_DEPTH",
    "HARNESS_SPAWNER_SERVICE_KEY",
    "SPAWN_DEPTH_KEY",
    "SPAWN_MAX_DEPTH_KEY",
    "TRACKED_DOC_PATHS",
    "ColdWalkPoint",
    "ColdWalkReport",
    "HarnessBlueprint",
    "HarnessDocContext",
    "HarnessSpawnerEngine",
    "HarnessSpawnerProtocol",
    "SeededKI",
    "SpawnBudgetSpec",
    "SpawnLifecycleState",
    "SpawnMergeProposal",
    "SpawnSpec",
    "SpawnTrialResult",
    "SpawnedHarnessRecord",
    "TreeDiffReview",
    "build_blueprint_tree",
    "build_harness_docs",
    "build_tree_diff_review",
    "check_materialized_drift",
    "compute_docs_sha256",
    "compute_tree_sha256",
    "format_cold_walk_markdown",
    "materialize_spawn_as_dock",
    "recommend_harness_blueprints",
    "run_cold_walk",
    "validate_harness_docs",
    "verify_diff_approval",
]
