"""Context Optimizer Service, Composable Pruning Strategies, and Slotted Domain Models.

Provides an authoritative micro-kernel service for:
1. Composable pre-LLM message pruning strategies (sliding window, middle-out compaction, AST RepoMap).
2. Slotted, frozen configuration and diagnostic telemetry results (Rule 12 & Rule 43).
3. Pluggable observation compaction with character and JSON boundary controls.
4. Seamless fallback and IoC container integration (Rule 1, Rule 2, Rule 49, Rule 58).
5. 100% backward-compatible support for StepExecutionEngine and SwarmCoordinator.
"""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.context_optimizer.compactor import MiddleOutObservationCompactor
from harness.services.context_optimizer.models import (
    ContextOptimizationConfig,
    ContextOptimizationResult,
    PruningMetric,
    estimate_tokens,
)
from harness.services.context_optimizer.protocols import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    CONTEXT_OPTIMIZER_SERVICE_KEY,
    ContextOptimizerService,
    ContextPruningStrategy,
    ObservationCompactorStrategy,
)
from harness.services.context_optimizer.resolvers import resolve_context_optimizer
from harness.services.context_optimizer.service import DefaultContextOptimizerService
from harness.services.context_optimizer.strategies import (
    CompositeContextStrategy,
    RepoMapInjectionStrategy,
    SlidingWindowPruner,
)

__all__ = [
    "AGENT_CONTEXT_OPTIMIZER_KEY",
    "CONTEXT_OPTIMIZER_SERVICE_KEY",
    "CompositeContextStrategy",
    "ContextOptimizationConfig",
    "ContextOptimizationResult",
    "ContextOptimizerService",
    "ContextPruningStrategy",
    "DefaultContextOptimizerService",
    "MiddleOutObservationCompactor",
    "ObservationCompactorStrategy",
    "PruningMetric",
    "RepoMapInjectionStrategy",
    "SlidingWindowPruner",
    "estimate_tokens",
    "resolve_context_optimizer",
]
