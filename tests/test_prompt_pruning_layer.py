"""Contract verification tests for Deterministic 3-Pass Prompt Pruner (Phase 2 Vector 2)."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.llm import LLMMessage
from harness.services.context_optimizer import (
    CONTEXT_OPTIMIZER_SERVICE_KEY,
    CompositeContextStrategy,
    ContextOptimizationConfig,
    DefaultContextOptimizerService,
    DeterministicPromptPruner,
    PrunableMessage,
    PruningAuditReport,
)
from plugins.memory_and_epistemics.prompt_pruning_layer.main import (
    PROMPT_PRUNING_SERVICE_KEY,
    PromptPruningPlugin,
    plugin,
)


@pytest.mark.unit
class TestPromptPruningDataStructures:
    """Verifies slotted frozen dataclass immutability and post-init assertions (Rule 12, Rule 43)."""

    def test_prunable_message_slotted_immutability(self) -> None:
        msg = PrunableMessage(
            role="tool",
            content="DEF test DEFINE:schema_v1",
            turn_index=1,
            resource_key="res_1",
        )
        assert msg.role == "tool"
        assert "schema_v1" in msg.defines_keys

        # Rule 43: direct assignment must raise AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            msg.content = "mutated content"  # type: ignore[misc]

        with pytest.raises((AttributeError, TypeError)):
            msg.turn_index = 2  # type: ignore[misc]

    def test_prunable_message_post_init_validation(self) -> None:
        with pytest.raises(ValueError, match="role must be non-empty"):
            PrunableMessage(role="", content="sample", turn_index=0)

        with pytest.raises(ValueError, match="turn_index must be non-negative"):
            PrunableMessage(role="user", content="sample", turn_index=-1)

    def test_pruning_audit_report_immutability(self) -> None:
        rep = PruningAuditReport(
            original_message_count=10,
            pruned_message_count=6,
            dropped_turns=(1, 2, 3, 4),
            restored_turns=(),
            pass1_dropped=2,
            pass2_dropped=2,
            pass3_restored=0,
            elapsed_ms=1.5,
        )
        assert rep.original_message_count == 10
        assert rep.pruned_message_count == 6

        with pytest.raises((AttributeError, TypeError)):
            rep.original_message_count = 20  # type: ignore[misc]


@pytest.mark.unit
class TestDeterministic3PassPruner:
    """Verifies algorithmic Pass 1, 2, 3 and fixed-point idempotence."""

    def test_pass1_superseded_tool_elimination(self) -> None:
        pruner = DeterministicPromptPruner()
        msgs = [
            PrunableMessage(role="tool", content="File content v1", turn_index=0, resource_key="file://main.py"),
            PrunableMessage(role="user", content="Please update", turn_index=1),
            PrunableMessage(role="tool", content="File content v2", turn_index=2, resource_key="file://main.py"),
        ]
        pruned, report = pruner.prune_prunable_messages(msgs)
        assert report.original_message_count == 3
        assert report.pruned_message_count == 2
        assert report.pass1_dropped == 1
        assert [m.content for m in pruned] == ["Please update", "File content v2"]

    def test_pass2_duplicate_passage_elimination(self) -> None:
        pruner = DeterministicPromptPruner()
        msgs = [
            PrunableMessage(role="tool", content="Standard query result table", turn_index=0),
            PrunableMessage(role="user", content="Next step", turn_index=1),
            PrunableMessage(role="tool", content="standard QUERY  result table", turn_index=2),
        ]
        pruned, report = pruner.prune_prunable_messages(msgs)
        assert report.pass2_dropped == 1
        assert len(pruned) == 2
        assert [m.turn_index for m in pruned] == [0, 1]

    def test_pass3_dependency_restoration(self) -> None:
        pruner = DeterministicPromptPruner()
        msgs = [
            PrunableMessage(
                role="tool",
                content="Legacy tool DEFINE:auth_spec",
                turn_index=0,
                resource_key="doc://auth",
            ),
            PrunableMessage(
                role="tool",
                content="New tool doc supersedes auth",
                turn_index=1,
                resource_key="doc://auth",
            ),
            PrunableMessage(
                role="user",
                content="Verify authentication using REF:auth_spec",
                turn_index=2,
            ),
        ]
        pruned, report = pruner.prune_prunable_messages(msgs)
        # Turn 0 was dropped in Pass 1, but restored in Pass 3 because Turn 2 references auth_spec!
        assert report.pass1_dropped == 1
        assert report.pass3_restored == 1
        assert len(pruned) == 3
        assert [m.turn_index for m in pruned] == [0, 1, 2]

    def test_fixed_point_idempotence(self) -> None:
        pruner = DeterministicPromptPruner()
        msgs = [
            PrunableMessage(role="tool", content="Old data", turn_index=0, resource_key="k1"),
            PrunableMessage(role="tool", content="New data", turn_index=1, resource_key="k1"),
            PrunableMessage(role="tool", content="Doc duplicate", turn_index=2),
            PrunableMessage(role="tool", content="doc DUPLICATE", turn_index=3),
            PrunableMessage(role="user", content="Final question", turn_index=4),
        ]
        once, report1 = pruner.prune_prunable_messages(msgs)
        twice, report2 = pruner.prune_prunable_messages(once)

        assert [m.turn_index for m in once] == [m.turn_index for m in twice]
        assert [m.content for m in once] == [m.content for m in twice]
        assert report2.original_message_count == len(once)
        assert report2.pruned_message_count == len(once)
        assert report2.pass1_dropped == 0
        assert report2.pass2_dropped == 0
        assert report2.pass3_restored == 0

    def test_context_optimizer_strategy_pipeline_integration(self) -> None:
        pruner = DeterministicPromptPruner()
        cfg = ContextOptimizationConfig(enable_pruning=True, max_total_messages=2)

        llm_messages = [
            LLMMessage(role="user", content="Start prompt"),
            LLMMessage(role="tool", content="KEY:table_1 Result batch 1"),
            LLMMessage(role="tool", content="KEY:table_1 Result batch 2"),
            LLMMessage(role="user", content="Show latest result"),
        ]

        pruned, metric = pruner.prune(llm_messages, config=cfg)
        assert metric is not None
        assert metric.strategy_name == "deterministic_prompt_pruner"
        assert metric.pruned_count == 3
        # Expired batch 1 was pruned, batch 2 was retained
        assert "Result batch 1" not in [m.content for m in pruned]
        assert any("Result batch 2" in m.content for m in pruned)


@pytest.mark.asyncio
class TestPromptPruningPluginLifecycle:
    """Verifies IoC container integration and non-invasive strategy registration."""

    async def test_plugin_registers_into_context_optimizer(self) -> None:
        ctx = ServiceContext()
        optimizer = DefaultContextOptimizerService(context=ctx)
        ctx.provide(CONTEXT_OPTIMIZER_SERVICE_KEY, optimizer)

        p = PromptPruningPlugin()
        assert PROMPT_PRUNING_SERVICE_KEY in p.provides

        await p.on_load(ctx)
        assert ctx.has(PROMPT_PRUNING_SERVICE_KEY)

        # Check strategy was registered into optimizer pipeline (Rule 19)
        registered_names = [s.name for s in optimizer.composite_pipeline._strategies]
        assert "deterministic_prompt_pruner" in registered_names

        # Verify module-level singleton export (Rule 45)
        assert plugin is not None
        assert plugin.name == "domain.prompt_pruning_layer"
