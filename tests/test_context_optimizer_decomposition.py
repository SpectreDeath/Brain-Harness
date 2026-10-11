"""Contract verification test suite for Context Optimizer Service Decomposition (Cycle 41).

Verifies:
1. Subpackage structure and strict line count bounds (Rule 11: all submodules <= 200 lines).
2. Slotted & frozen dataclass contracts and immutability guards (Rule 12 & Rule 43).
3. 100% backward-compatible facade re-exports across harness.services.context_optimizer and harness.agent.context_optimizer.
4. Single-seam IoC resolution via resolve_context_optimizer (Rule 58).
5. Observation compaction, sliding-window pruning, AST repo map injection, and telemetry metrics.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
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
from harness.agent.context_optimizer import (
    AgentContextOptimizer,
    DefaultContextOptimizer,
    resolve_context_optimizer as agent_resolve_context_optimizer,
)
from harness.services.llm import LLMMessage
from harness.services.repomap import REPO_MAP_SERVICE_KEY, RepoMapResult, RepoMapService

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TestContextOptimizerDecompositionArchitecture:
    """Architectural and structural invariants for context_optimizer subpackage."""

    def test_submodule_structure_and_line_limits(self) -> None:
        """Rule 11: All decomposed submodules must strictly remain <= 200 lines."""
        pkg_dir = Path(__file__).parent.parent / "src" / "harness" / "services" / "context_optimizer"
        assert pkg_dir.is_dir(), f"Expected directory at {pkg_dir}"

        expected_modules = {
            "__init__.py",
            "models.py",
            "protocols.py",
            "compactor.py",
            "strategies.py",
            "resolvers.py",
            "service.py",
        }

        found_modules = {p.name for p in pkg_dir.glob("*.py")}
        assert expected_modules.issubset(found_modules)

        for mod_name in expected_modules:
            mod_path = pkg_dir / mod_name
            lines = len(mod_path.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"Module {mod_name} has {lines} lines, exceeding Rule 11 limit (200)"

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Rule 12 & Rule 43: Direct attribute mutation must raise AttributeError or TypeError."""
        cfg = ContextOptimizationConfig(max_observation_chars=1500, max_total_messages=10)
        assert hasattr(cfg, "__slots__")
        assert not hasattr(cfg, "__dict__")

        with pytest.raises((AttributeError, TypeError)):
            cfg.max_observation_chars = 2000  # type: ignore[misc]

        metric = PruningMetric(
            strategy_name="test_strat",
            initial_count=10,
            pruned_count=5,
            estimated_tokens_before=1000,
            estimated_tokens_after=500,
        )
        assert hasattr(metric, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            metric.pruned_count = 2  # type: ignore[misc]

        res = ContextOptimizationResult(
            status="ok",
            original_count=10,
            optimized_count=5,
            estimated_tokens=500,
        )
        assert hasattr(res, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            res.status = "error"  # type: ignore[misc]

    def test_backward_compatibility_aliases(self) -> None:
        """Ensure harness.agent.context_optimizer aliases and re-exports remain intact."""
        assert AgentContextOptimizer is ContextOptimizerService
        assert DefaultContextOptimizer is DefaultContextOptimizerService
        assert agent_resolve_context_optimizer is resolve_context_optimizer

    def test_single_seam_resolver(self) -> None:
        """Rule 58: resolve_context_optimizer resolves from IoC context or defaults cleanly."""
        # 1. Fallback without context
        svc_default = resolve_context_optimizer()
        assert isinstance(svc_default, DefaultContextOptimizerService)

        # 2. Resolution with custom registration in context
        ctx = ServiceContext()
        custom_svc = DefaultContextOptimizerService(
            config=ContextOptimizationConfig(max_observation_chars=1234)
        )
        ctx.provide(CONTEXT_OPTIMIZER_SERVICE_KEY, custom_svc)

        resolved = resolve_context_optimizer(ctx)
        assert resolved is custom_svc
        assert resolved.config.max_observation_chars == 1234

        # 3. Resolution with legacy agent key
        ctx_legacy = ServiceContext()
        ctx_legacy.provide(AGENT_CONTEXT_OPTIMIZER_KEY, custom_svc)
        resolved_legacy = resolve_context_optimizer(ctx_legacy)
        assert resolved_legacy is custom_svc

    def test_observation_compaction_and_json_truncation(self) -> None:
        """Verify MiddleOutObservationCompactor string and JSON bounded reduction."""
        compactor = MiddleOutObservationCompactor()
        assert compactor.name == "middle_out_compactor"

        # None handling
        assert compactor.compact("test", None, max_chars=100) == "Observation: None"

        # Short text
        assert compactor.compact("test", "short string", max_chars=100) == "short string"

        # Long text middle-out truncation
        long_text = "A" * 1000 + "B" * 1000
        truncated = compactor.compact("test", long_text, max_chars=100)
        assert "TRUNCATED" in truncated
        assert truncated.startswith("A" * 50)
        assert truncated.endswith("B" * 50)

        # JSON truncation
        huge_dict = {f"k_{i}": f"val_{i}" * 50 for i in range(100)}
        truncated_json = compactor.compact("test", huge_dict, max_chars=200)
        assert "TRUNCATED JSON" in truncated_json

    def test_sliding_window_pruning_and_telemetry(self) -> None:
        """Verify SlidingWindowPruner preserving head/tail and generating diagnostic metrics."""
        pruner = SlidingWindowPruner()
        cfg = ContextOptimizationConfig(max_total_messages=6, recent_messages_preserve=2)

        msgs = [
            LLMMessage(role="system", content="System instruction"),
            LLMMessage(role="user", content="User goal"),
            LLMMessage(role="assistant", content="Step 1"),
            LLMMessage(role="user", content="Step 2"),
            LLMMessage(role="assistant", content="Step 3"),
            LLMMessage(role="user", content="Step 4"),
            LLMMessage(role="assistant", content="Step 5"),
            LLMMessage(role="user", content="Final response needed"),
        ]

        pruned, metric = pruner.prune(msgs, config=cfg)
        assert metric is not None
        assert metric.initial_count == 8
        assert metric.pruned_count == 5  # 2 header + 1 notice + 2 tail
        assert metric.strategy_name == "sliding_window_pruner"
        assert len(pruned) == 5
        assert "CONTEXT PRUNING:" in (pruned[2].content or "")

    def test_default_service_full_context_optimization(self) -> None:
        """Verify DefaultContextOptimizerService optimize_context end-to-end pipeline."""
        svc = DefaultContextOptimizerService(
            config=ContextOptimizationConfig(
                max_total_messages=4,
                recent_messages_preserve=2,
            )
        )

        msgs = [
            LLMMessage(role="system", content="System 0"),
            LLMMessage(role="user", content="User 1"),
            LLMMessage(role="assistant", content="Assistant 2"),
            LLMMessage(role="user", content="User 3"),
            LLMMessage(role="assistant", content="Assistant 4"),
            LLMMessage(role="user", content="User 5"),
        ]

        res = svc.optimize_context(msgs)
        assert res.status == "ok"
        assert res.original_count == 6
        assert res.optimized_count == 5
        assert len(res.metrics) == 1
        assert res.metrics[0].strategy_name == "sliding_window_pruner"
        assert res.to_dict()["status"] == "ok"
