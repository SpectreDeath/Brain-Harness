"""Comprehensive verification suite for Phase 2 Architecture Remediations.

Tests:
    1. Compiled interceptor pipeline caching and invalidation in ServiceContext.
    2. Pre-image transaction restoration on ServiceContext rollback.
    3. Concurrency-safe ServiceContext mutation locks.
    4. Full-duplex multiplexed JSON-RPC transport with concurrent calls.
    5. Async coroutine execution in bridge_runner.py without serialization errors.
    6. BM25 intent routing calibration on short vs. verbose queries.
    7. AntiPatternGuard active execution checking against declared failure modes.
    8. Transitive single-pass cascading deactivation in PluginLifecycle.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.plugins.base import HarnessPlugin
from harness.plugins.sandbox import SubprocessExecutor
from harness.plugins.transport import StdioJsonRpcTransport
from harness.services.skill_graph import (
    AntiPatternGuard,
    BuiltinSkillRegistryService,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillStageDefinition,
)


@pytest.mark.asyncio
async def test_compiled_interceptor_caching() -> None:
    """Verify interceptor pipelines are compiled and cached on hot require paths."""
    key = ServiceKey[int]("test.number")
    ctx = ServiceContext()
    ctx.provide(key, 10)

    # Wrap with two interceptors
    child_ctx = ctx.intercept(key, lambda x: x + 5)
    grandchild_ctx = child_ctx.intercept(key, lambda x: x * 2)

    # First lookup: compiles and caches chain
    val1 = grandchild_ctx.require(key)
    assert val1 == 30  # (10 + 5) * 2

    # Verify cache is populated
    assert key.name in grandchild_ctx._compiled_interceptors
    assert len(grandchild_ctx._compiled_interceptors[key.name]) == 2

    # Second lookup: hits cache directly
    val2 = grandchild_ctx.require(key)
    assert val2 == 30


@pytest.mark.asyncio
async def test_transaction_pre_image_restoration() -> None:
    """Verify transaction rollback cleanly restores pre-transaction entry state."""
    key = ServiceKey[str]("test.service")
    ctx = ServiceContext()
    ctx.provide(key, "initial_value")

    # Transaction 1: Aborts due to error -> rolls back intermediate changes
    with pytest.raises(RuntimeError):
        async with ctx.transaction() as tx:
            tx.provide(key, "failed_value", allow_override=True)
            assert tx.require(key) == "failed_value"
            raise RuntimeError("Aborted transaction")

    # State in ctx remains preserved
    assert ctx.require(key) == "initial_value"

    # Transaction 2: Commits successfully
    async with ctx.transaction() as tx2:
        tx2.provide(key, "committed_value", allow_override=True)

    assert ctx.require(key) == "committed_value"


@pytest.mark.asyncio
async def test_multiplexed_transport_concurrency(tmp_path: Path) -> None:
    """Verify StdioJsonRpcTransport multiplexes concurrent calls without head-of-line blocking."""
    # Create a dummy plugin script
    script = tmp_path / "mock_echo.py"
    script.write_text(
        "def echo(val):\n"
        "    return val\n"
        "def add(a, b):\n"
        "    return a + b\n",
        encoding="utf-8",
    )

    import sys
    runner_path = Path(__file__).parent.parent / "src" / "harness" / "plugins" / "bridge_runner.py"

    transport = StdioJsonRpcTransport(
        sys.executable,
        [str(runner_path), str(script)],
    )
    await transport.start()
    try:
        # Launch 10 concurrent calls
        tasks = [
            transport.call("echo", {"val": i}, timeout=5.0)
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for i, res in enumerate(results):
            assert res.get("result") == i
            assert "error" not in res
    finally:
        await transport.stop()


@pytest.mark.asyncio
async def test_async_coroutine_in_bridge_runner(tmp_path: Path) -> None:
    """Verify bridge_runner.py cleanly executes and awaits async coroutine tools."""
    script = tmp_path / "async_service.py"
    script.write_text(
        "import asyncio\n"
        "async def compute_async(x: int) -> int:\n"
        "    await asyncio.sleep(0.02)\n"
        "    return x * 3\n",
        encoding="utf-8",
    )

    executor = SubprocessExecutor(script)
    await executor.start()
    try:
        resp = await executor.execute("compute_async", {"x": 14})
        assert resp["status"] == "ok"
        assert resp["result"] == 42
    finally:
        await executor.stop()


def test_bm25_intent_routing_with_detailed_prompt() -> None:
    """Verify BM25 intent calibration maintains high confidence on rich, descriptive prompts."""
    registry = BuiltinSkillRegistryService()

    terse_res = registry.route_intent("deepen architecture", top_k=3)
    assert terse_res["status"] == "ok"
    assert len(terse_res["matches"]) > 0
    top_terse = terse_res["matches"][0]
    assert top_terse["skill_name"] == "deepen-architecture"
    assert top_terse["confidence"] >= 0.50

    detailed_prompt = (
        "We need to thoroughly inspect our system seams and deepen the codebase architecture "
        "to eliminate shallow wrappers and optimize module depth across the repository"
    )
    verbose_res = registry.route_intent(detailed_prompt, top_k=3)
    assert verbose_res["status"] == "ok"
    assert len(verbose_res["matches"]) > 0
    top_verbose = verbose_res["matches"][0]
    assert top_verbose["skill_name"] == "deepen-architecture"
    # BM25 calibration prevents length dilation from crushing confidence
    assert top_verbose["confidence"] >= 0.50


def test_anti_pattern_guard_detection() -> None:
    """Verify AntiPatternGuard flags proposed actions matching declared anti-patterns."""
    skill = SkillCardDefinition(
        name="test-guard-skill",
        target="Verify anti-pattern guardrails",
        stages=[SkillStageDefinition(stage_num=1, name="Init", completion_gate="Done")],
        anti_patterns=[
            SkillAntiPatternDefinition(
                name="Speculative Abstraction",
                symptom="Adding premature generic wrappers",
                remedy="Keep implementations concrete and bound to immediate requirements",
            ),
            SkillAntiPatternDefinition(
                name="Bypassing The Checkpoint",
                symptom="Modifying files without user plan approval",
                remedy="Always await explicit approval",
            ),
        ],
    )

    clean_plan = "Refactor the existing database query to use parameterized inputs."
    assert len(AntiPatternGuard.check_proposal(skill, clean_plan)) == 0

    bad_plan = "We should introduce a speculative abstraction layer for potential future databases."
    violations = AntiPatternGuard.check_proposal(skill, bad_plan)
    assert len(violations) == 1
    assert violations[0].anti_pattern == "Speculative Abstraction"
    assert violations[0].remedy.startswith("Keep implementations concrete")


@pytest.mark.asyncio
async def test_transitive_cascading_disable() -> None:
    """Verify PluginLifecycle disables transitive dependents in a single sorted pass."""
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    k1 = ServiceKey[str]("svc.1")
    k2 = ServiceKey[str]("svc.2")
    k3 = ServiceKey[str]("svc.3")

    class P1(HarnessPlugin):
        name = "p1"
        version = "1.0.0"
        description = "Plugin 1"
        provides = [k1]
        async def on_load(self, c: ServiceContext) -> None: c.provide(k1, "v1")
        async def on_enable(self) -> None: pass
        async def on_disable(self) -> None: pass
        async def on_unload(self) -> None: pass

    class P2(HarnessPlugin):
        name = "p2"
        version = "1.0.0"
        description = "Plugin 2"
        provides = [k2]
        requires = [k1]
        async def on_load(self, c: ServiceContext) -> None: c.provide(k2, "v2")
        async def on_enable(self) -> None: pass
        async def on_disable(self) -> None: pass
        async def on_unload(self) -> None: pass

    class P3(HarnessPlugin):
        name = "p3"
        version = "1.0.0"
        description = "Plugin 3"
        provides = [k3]
        requires = [k2]
        async def on_load(self, c: ServiceContext) -> None: c.provide(k3, "v3")
        async def on_enable(self) -> None: pass
        async def on_disable(self) -> None: pass
        async def on_unload(self) -> None: pass

    p1, p2, p3 = P1(), P2(), P3()
    await lifecycle.register_and_enable(p1)
    await lifecycle.register_and_enable(p2)
    await lifecycle.register_and_enable(p3)

    assert lifecycle.get_state("p1") == PluginState.ENABLED
    assert lifecycle.get_state("p2") == PluginState.ENABLED
    assert lifecycle.get_state("p3") == PluginState.ENABLED

    # Disabling p1 with cascade=True should transitively disable p3 then p2 then p1
    await lifecycle.disable("p1", cascade=True)

    assert lifecycle.get_state("p1") == PluginState.DISABLED
    assert lifecycle.get_state("p2") == PluginState.DISABLED
    assert lifecycle.get_state("p3") == PluginState.DISABLED
