"""Contract verification tests for Ebbinghaus Memory Decay Engine (Phase 2 Vector 1)."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.memory_decay import (
    MEMORY_DECAY_SERVICE_KEY,
    DecayConfig,
    DefaultMemoryDecayService,
    EvictionDecision,
    MemoryDecayService,
    MemoryNode,
    resolve_memory_decay,
)
from plugins.memory_and_epistemics.memory_decay_engine.main import (
    MemoryDecayPlugin,
    plugin,
)


@pytest.mark.unit
class TestMemoryDecayDataStructures:
    """Verifies slotted frozen dataclass immutability and post-init assertions (Rule 12, Rule 43)."""

    def test_memory_node_slotted_immutability(self) -> None:
        node = MemoryNode(
            node_id="n1",
            content="Observation A",
            category="tool_output",
            stability=10.0,
            recall_count=1,
            created_turn=0,
            last_accessed_turn=0,
        )
        assert node.node_id == "n1"
        assert node.stability == 10.0

        # Rule 43: direct attribute assignment must raise AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            node.content = "Mutated content"  # type: ignore[misc]

        with pytest.raises((AttributeError, TypeError)):
            node.stability = 20.0  # type: ignore[misc]

    def test_memory_node_post_init_validation(self) -> None:
        with pytest.raises(ValueError, match="node_id must be non-empty"):
            MemoryNode(
                node_id="",
                content="test",
                category="test",
                stability=1.0,
                recall_count=1,
                created_turn=0,
                last_accessed_turn=0,
            )

        with pytest.raises(ValueError, match="stability must be positive"):
            MemoryNode(
                node_id="n1",
                content="test",
                category="test",
                stability=-1.0,
                recall_count=1,
                created_turn=0,
                last_accessed_turn=0,
            )

        with pytest.raises(ValueError, match="last_accessed_turn cannot be prior"):
            MemoryNode(
                node_id="n1",
                content="test",
                category="test",
                stability=1.0,
                recall_count=1,
                created_turn=5,
                last_accessed_turn=2,
            )

    def test_decay_config_validation(self) -> None:
        cfg = DecayConfig(half_life_turns=15, retention_threshold=0.25)
        assert cfg.half_life_turns == 15
        assert cfg.retention_threshold == 0.25

        with pytest.raises(ValueError, match="half_life_turns must be positive"):
            DecayConfig(half_life_turns=0)

        with pytest.raises(ValueError, match=r"retention_threshold must be in \(0, 1\)"):
            DecayConfig(retention_threshold=1.5)


@pytest.mark.unit
class TestEbbinghausMemoryDecayService:
    """Verifies decay retention math, monotonicity, and eviction policies."""

    def test_monotonic_stability_reinforcement(self) -> None:
        svc = DefaultMemoryDecayService(DecayConfig(half_life_turns=10, stability_boost_alpha=0.5))
        node = svc.register_observation("obs_1", "Result from search", current_turn=0)
        s0 = node.stability

        r1 = svc.reinforce_recall("obs_1", current_turn=1)
        assert r1 is not None
        s1 = r1.stability
        assert s1 > s0

        r2 = svc.reinforce_recall("obs_1", current_turn=2)
        assert r2 is not None
        s2 = r2.stability
        assert s2 > s1
        assert r2.recall_count == 3

    def test_exponential_decay_and_eviction(self) -> None:
        cfg = DecayConfig(half_life_turns=5, retention_threshold=0.30)
        svc = DefaultMemoryDecayService(cfg)
        svc.register_observation("fast_decay", "Scratch note", current_turn=0, initial_stability=2.0)
        svc.register_observation("slow_decay", "Critical law", current_turn=0, initial_stability=50.0)

        # At turn 0: retention is 1.0 for both
        assert svc.calculate_retention("fast_decay", current_turn=0) == 1.0
        assert svc.calculate_retention("slow_decay", current_turn=0) == 1.0

        # At turn 10:
        # fast_decay: exp(-10/2) = exp(-5) = 0.0067 < 0.30 -> evicted
        # slow_decay: exp(-10/50) = exp(-0.2) = 0.8187 > 0.30 -> retained
        decision = svc.evaluate_decay(current_turn=10, auto_evict=True)
        assert "fast_decay" in decision.evicted_ids
        assert "slow_decay" in decision.retained_ids
        assert not svc.is_present("fast_decay")
        assert svc.is_present("slow_decay")
        assert svc.working_set_size() == 1

    def test_max_nodes_bounding_eviction(self) -> None:
        cfg = DecayConfig(half_life_turns=10, retention_threshold=0.01, max_nodes=2)
        svc = DefaultMemoryDecayService(cfg)
        svc.register_observation("n1", "First item", current_turn=0, initial_stability=5.0)
        svc.register_observation("n2", "Second item", current_turn=0, initial_stability=10.0)
        svc.register_observation("n3", "Third item", current_turn=0, initial_stability=15.0)

        assert svc.working_set_size() == 3
        # Evaluate decay with auto_evict: capacity is 2, so lowest retention item (n1) must be evicted
        decision = svc.evaluate_decay(current_turn=2, auto_evict=True)
        assert "n1" in decision.evicted_ids
        assert svc.working_set_size() == 2
        assert not svc.is_present("n1")
        assert svc.is_present("n2")
        assert svc.is_present("n3")

    def test_single_seam_resolver(self) -> None:
        ctx = ServiceContext()
        custom_svc = DefaultMemoryDecayService(DecayConfig(half_life_turns=40))
        ctx.provide(MEMORY_DECAY_SERVICE_KEY, custom_svc)

        resolved = resolve_memory_decay(ctx)
        assert resolved.config.half_life_turns == 40

        # Fallback when no context provided
        fallback = resolve_memory_decay(None)
        assert fallback.config.half_life_turns == 20


@pytest.mark.asyncio
class TestMemoryDecayPluginLifecycle:
    """Verifies IoC container integration and plugin lifecycle."""

    async def test_plugin_on_load_provides_service_key(self) -> None:
        ctx = ServiceContext()
        p = MemoryDecayPlugin()
        assert MEMORY_DECAY_SERVICE_KEY in p.provides

        await p.on_load(ctx)
        assert ctx.has(MEMORY_DECAY_SERVICE_KEY)
        svc = ctx.require(MEMORY_DECAY_SERVICE_KEY)
        assert isinstance(svc, MemoryDecayService)

        # Test module singleton export (Rule 45)
        assert plugin is not None
        assert plugin.name == "domain.memory_decay_engine"
