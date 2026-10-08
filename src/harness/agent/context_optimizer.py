"""Agent context optimization, message budgeting, and compaction facade (Rule 57).

Re-exports slotted domain models, composable pruning strategies, and the
DefaultContextOptimizerService from the authoritative micro-kernel service
harness.services.context_optimizer (Rule 49 & Rule 58).
"""

from __future__ import annotations

import sys

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    CONTEXT_OPTIMIZER_SERVICE_KEY,
    CompositeContextStrategy,
    ContextOptimizationConfig,
    ContextOptimizationResult,
    ContextOptimizerService,
    ContextPruningStrategy,
    DefaultContextOptimizerService,
    MiddleOutObservationCompactor,
    ObservationCompactorStrategy,
    PruningMetric,
    RepoMapInjectionStrategy,
    SlidingWindowPruner,
    estimate_tokens,
    resolve_context_optimizer,
)

# Backward-compatibility aliases for legacy agent loops
AgentContextOptimizer = ContextOptimizerService
DefaultContextOptimizer = DefaultContextOptimizerService

__all__ = [
    "AGENT_CONTEXT_OPTIMIZER_KEY",
    "AgentContextOptimizer",
    "CONTEXT_OPTIMIZER_SERVICE_KEY",
    "CompositeContextStrategy",
    "ContextOptimizationConfig",
    "ContextOptimizationResult",
    "ContextOptimizerService",
    "ContextPruningStrategy",
    "DefaultContextOptimizer",
    "DefaultContextOptimizerService",
    "MiddleOutObservationCompactor",
    "ObservationCompactorStrategy",
    "PruningMetric",
    "RepoMapInjectionStrategy",
    "SlidingWindowPruner",
    "estimate_tokens",
    "resolve_context_optimizer",
]
