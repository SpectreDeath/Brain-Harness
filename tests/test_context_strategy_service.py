"""Comprehensive tests for ContextOptimizerService, composable pruning strategies, and slotted domain models."""

from __future__ import annotations

import asyncio
from typing import Any
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
from harness.services.llm import LLMMessage
from harness.services.repomap import REPO_MAP_SERVICE_KEY, RepoMapResult, RepoMapService
from plugins.developer_tooling.context_optimizer.main import (
    ContextOptimizerPlugin,
    context_compact_observation,
    context_optimize_messages,
    plugin,
)


# =============================================================================
# Slotted & Frozen Dataclass Immutability Tests (Rule 12 & Rule 43)
# =============================================================================

class TestSlottedDataclassContracts:
    """Verify slots=True, frozen=True, and __post_init__ validation on domain models."""

    def test_context_optimization_config_immutability(self) -> None:
        cfg = ContextOptimizationConfig(max_observation_chars=2000, max_total_messages=20)
        assert hasattr(cfg, "__slots__")
        assert not hasattr(cfg, "__dict__")

        # Rule 43: direct attribute assignment raises AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            cfg.max_observation_chars = 5000  # type: ignore[misc]

        with pytest.raises((AttributeError, TypeError)):
            cfg.compact_json = False  # type: ignore[misc]

        assert cfg.to_dict()["max_observation_chars"] == 2000

    def test_context_optimization_config_post_init_validation(self) -> None:
        with pytest.raises(AssertionError):
            ContextOptimizationConfig(max_observation_chars=0)

        with pytest.raises(AssertionError):
            ContextOptimizationConfig(max_total_messages=1)

        with pytest.raises(AssertionError):
            ContextOptimizationConfig(recent_messages_preserve=0)

        with pytest.raises(AssertionError):
            ContextOptimizationConfig(token_budget=-10)

    def test_pruning_metric_immutability(self) -> None:
        metric = PruningMetric(
            strategy_name="test_strat",
            initial_count=10,
            pruned_count=6,
            estimated_tokens_before=1000,
            estimated_tokens_after=600,
            duration_ms=1.5,
        )
        assert hasattr(metric, "__slots__")
        assert not hasattr(metric, "__dict__")

        with pytest.raises((AttributeError, TypeError)):
            metric.pruned_count = 2  # type: ignore[misc]

        d = metric.to_dict()
        assert d["strategy"] == "test_strat"
        assert d["initial_messages"] == 10
        assert d["pruned_messages"] == 6

    def test_context_optimization_result_immutability(self) -> None:
        msgs = (
            LLMMessage(role="system", content="System"),
            LLMMessage(role="user", content="Task"),
        )
        res = ContextOptimizationResult(
            status="ok",
            messages=msgs,
            original_count=2,
            optimized_count=2,
            estimated_tokens=10,
        )
        assert hasattr(res, "__slots__")
        assert not hasattr(res, "__dict__")

        with pytest.raises((AttributeError, TypeError)):
            res.status = "error"  # type: ignore[misc]

        assert res.to_dict()["status"] == "ok"
        assert res.to_dict()["original_count"] == 2


# =============================================================================
# Observation Compactor Tests
# =============================================================================

class TestMiddleOutObservationCompactor:
    """Verify progressive middle-out tool observation compaction."""

    def test_compact_none_and_short_string(self) -> None:
        compactor = MiddleOutObservationCompactor()
        assert compactor.compact("tool", None, max_chars=100) == "Observation: None"
        assert compactor.compact("tool", "short output", max_chars=100) == "short output"

    def test_compact_long_string_truncation(self) -> None:
        compactor = MiddleOutObservationCompactor()
        long_str = "H" * 100 + "M" * 300 + "T" * 100
        compacted = compactor.compact("read_file", long_str, max_chars=100)
        assert "[TRUNCATED 400 CHARS]" in compacted
        assert compacted.startswith("H" * 50)
        assert compacted.endswith("T" * 50)

    def test_compact_json_data(self) -> None:
        compactor = MiddleOutObservationCompactor()
        data = {"key": "val", "nums": [1, 2, 3]}
        res = compactor.compact("query", data, max_chars=100, compact_json=True)
        assert res == '{"key":"val","nums":[1,2,3]}'

    def test_compact_huge_json_truncation(self) -> None:
        compactor = MiddleOutObservationCompactor()
        huge_data = {"payload": "X" * 500}
        res = compactor.compact("query", huge_data, max_chars=80)
        assert "[TRUNCATED JSON" in res


# =============================================================================
# Sliding Window Pruner Tests
# =============================================================================

class TestSlidingWindowPruner:
    """Verify sliding-window preservation and middle omission summary."""

    def test_no_pruning_under_budget(self) -> None:
        pruner = SlidingWindowPruner()
        cfg = ContextOptimizationConfig(max_total_messages=10)
        msgs = [
            LLMMessage(role="system", content="sys"),
            LLMMessage(role="user", content="usr"),
            LLMMessage(role="assistant", content="asst"),
        ]
        pruned, metric = pruner.prune(msgs, config=cfg)
        assert len(pruned) == 3
        assert metric is None

    def test_pruning_over_budget(self) -> None:
        pruner = SlidingWindowPruner()
        cfg = ContextOptimizationConfig(
            max_total_messages=6,
            recent_messages_preserve=2,
            enable_pruning=True,
        )
        msgs = [
            LLMMessage(role="system", content="System Header"),
            LLMMessage(role="user", content="Task Prompt"),
            LLMMessage(role="assistant", content="Step 1"),
            LLMMessage(role="user", content="Obs 1"),
            LLMMessage(role="assistant", content="Step 2"),
            LLMMessage(role="user", content="Obs 2"),
            LLMMessage(role="assistant", content="Step 3"),
            LLMMessage(role="user", content="Obs 3"),
            LLMMessage(role="assistant", content="Step 4"),
            LLMMessage(role="user", content="Obs 4"),
        ]
        pruned, metric = pruner.prune(msgs, config=cfg)
        # Expected: Header(2) + Summary(1) + Tail(2) = 5 messages
        assert len(pruned) == 5
        assert pruned[0].content == "System Header"
        assert pruned[1].content == "Task Prompt"
        assert "[CONTEXT PRUNING: 6 intermediate reasoning steps and observations omitted for brevity]" in pruned[2].content
        assert pruned[3].content == "Step 4"
        assert pruned[4].content == "Obs 4"

        assert metric is not None
        assert metric.initial_count == 10
        assert metric.pruned_count == 5
        assert metric.strategy_name == "sliding_window_pruner"


# =============================================================================
# RepoMap Injection Strategy Tests
# =============================================================================

class MockRepoMapService(RepoMapService):
    def get_repo_map(self, root: str, query_context: str | None = None, max_tokens: int = 1024) -> RepoMapResult:
        return RepoMapResult(
            status="ok",
            root_path=root,
            total_files=5,
            formatted_map="src/main.py: app\nsrc/service.py: run",
            token_count=15,
        )


class TestRepoMapInjectionStrategy:
    """Verify AST RepoMap injection into system prompt (Rule 9)."""

    def test_injects_repo_map_into_system_message(self) -> None:
        ctx = ServiceContext()
        ctx.provide(REPO_MAP_SERVICE_KEY, MockRepoMapService())

        strat = RepoMapInjectionStrategy(context=ctx)
        cfg = ContextOptimizationConfig(repo_map_root="src")
        msgs = [
            LLMMessage(role="system", content="Base system instructions"),
            LLMMessage(role="user", content="Build the feature"),
        ]

        enhanced, injected = strat.inject(msgs, config=cfg)
        assert injected is True
        assert "### Repository Map:" in enhanced[0].content
        assert "src/main.py: app" in enhanced[0].content
        assert enhanced[1].content == "Build the feature"

    def test_skips_when_no_repo_map_root(self) -> None:
        strat = RepoMapInjectionStrategy()
        cfg = ContextOptimizationConfig(repo_map_root=None)
        msgs = [LLMMessage(role="system", content="Base sys")]
        enhanced, injected = strat.inject(msgs, config=cfg)
        assert injected is False
        assert enhanced[0].content == "Base sys"


# =============================================================================
# Composite Context Strategy Tests
# =============================================================================

class CustomTaggingPruner:
    """Test custom strategy appending a diagnostic marker."""

    @property
    def name(self) -> str:
        return "custom_tagger"

    def prune(
        self, messages: list[LLMMessage], *, config: ContextOptimizationConfig
    ) -> tuple[list[LLMMessage], PruningMetric | None]:
        tagged = [LLMMessage(role=m.role, content=f"{m.content} [TAGGED]") for m in messages]
        metric = PruningMetric(
            strategy_name=self.name,
            initial_count=len(messages),
            pruned_count=len(tagged),
            estimated_tokens_before=10,
            estimated_tokens_after=12,
            duration_ms=0.5,
        )
        return tagged, metric


class TestCompositeStrategy:
    """Verify sequential chaining of multiple pruning strategies."""

    def test_composite_pipeline_execution(self) -> None:
        pipeline = CompositeContextStrategy([SlidingWindowPruner(), CustomTaggingPruner()])
        cfg = ContextOptimizationConfig(max_total_messages=4, recent_messages_preserve=1)
        msgs = [
            LLMMessage(role="system", content="Sys"),
            LLMMessage(role="user", content="Task"),
            LLMMessage(role="assistant", content="Step 1"),
            LLMMessage(role="assistant", content="Step 2"),
            LLMMessage(role="assistant", content="Step 3"),
        ]
        result_msgs, metrics = pipeline.prune_pipeline(msgs, config=cfg)
        assert len(metrics) == 2
        assert metrics[0].strategy_name == "sliding_window_pruner"
        assert metrics[1].strategy_name == "custom_tagger"
        assert all("[TAGGED]" in m.content for m in result_msgs)


# =============================================================================
# Service & IoC Resolution Tests (Rule 1, Rule 2, Rule 58)
# =============================================================================

class TestContextOptimizerServiceIoC:
    """Verify IoC provider, resolution factory, and plugin integration."""

    def test_resolve_without_context_returns_default(self) -> None:
        svc = resolve_context_optimizer()
        assert isinstance(svc, DefaultContextOptimizerService)
        assert svc.config.max_total_messages == 30

    def test_resolve_from_ioc_context(self) -> None:
        ctx = ServiceContext()
        custom_svc = DefaultContextOptimizerService(ContextOptimizationConfig(max_total_messages=50))
        ctx.provide(CONTEXT_OPTIMIZER_SERVICE_KEY, custom_svc)

        resolved = resolve_context_optimizer(ctx)
        assert resolved is custom_svc
        assert resolved.config.max_total_messages == 50

    def test_resolve_from_legacy_agent_key(self) -> None:
        ctx = ServiceContext()
        custom_svc = DefaultContextOptimizerService(ContextOptimizationConfig(max_total_messages=42))
        ctx.provide(AGENT_CONTEXT_OPTIMIZER_KEY, custom_svc)

        resolved = resolve_context_optimizer(ctx)
        assert resolved is custom_svc
        assert resolved.config.max_total_messages == 42

    @pytest.mark.asyncio
    async def test_plugin_on_load_provides_service_keys(self) -> None:
        ctx = ServiceContext()
        p = ContextOptimizerPlugin()
        await p.on_load(ctx)

        assert ctx.has(CONTEXT_OPTIMIZER_SERVICE_KEY)
        assert ctx.has(AGENT_CONTEXT_OPTIMIZER_KEY)

        svc = ctx.require(CONTEXT_OPTIMIZER_SERVICE_KEY)
        assert isinstance(svc, ContextOptimizerService)

    def test_plugin_tool_entrypoints(self) -> None:
        # Test compact observation tool
        obs_res = context_compact_observation("test", "A" * 200, max_chars=50)
        assert obs_res["status"] == "ok"
        assert "[TRUNCATED" in obs_res["compacted_observation"]

        # Test optimize messages tool
        raw_msgs = [
            {"role": "system", "content": "Sys"},
            {"role": "user", "content": "Task"},
            {"role": "assistant", "content": "Step 1"},
            {"role": "assistant", "content": "Step 2"},
            {"role": "assistant", "content": "Step 3"},
            {"role": "assistant", "content": "Step 4"},
            {"role": "assistant", "content": "Step 5"},
            {"role": "assistant", "content": "Step 6"},
        ]
        opt_res = context_optimize_messages(raw_msgs, max_total_messages=4, recent_messages_preserve=2)
        assert opt_res["status"] == "ok"
        assert opt_res["optimized_count"] == 5

    def test_optimize_context_telemetry(self) -> None:
        svc = DefaultContextOptimizerService(
            ContextOptimizationConfig(max_total_messages=4, recent_messages_preserve=2)
        )
        msgs = [
            LLMMessage(role="system", content="Sys"),
            LLMMessage(role="user", content="Task"),
            LLMMessage(role="assistant", content="Step 1"),
            LLMMessage(role="assistant", content="Step 2"),
            LLMMessage(role="assistant", content="Step 3"),
            LLMMessage(role="assistant", content="Step 4"),
            LLMMessage(role="assistant", content="Step 5"),
        ]
        result = svc.optimize_context(msgs)
        assert isinstance(result, ContextOptimizationResult)
        assert result.status == "ok"
        assert result.original_count == 7
        assert result.optimized_count == 5
        assert len(result.metrics) >= 1
        assert result.estimated_tokens > 0
