"""Contract verification suite for Architectural Modernization.

Validates:
1. Wave-parallel execution in lifecycle.enable_all and failure isolation.
2. Async coroutine execution in bridge_runner._execute_func without nested loop crash.
3. Subprocess memory watchdog RSS enforcement.
4. Negation-aware anti-pattern detection in AntiPatternGuard.
5. Strict graph reachability (zero synthetic routing edges by default) in BuiltinSkillRegistryService.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from harness.agent.react import StepExecutionEngine
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.plugins.base import HarnessPlugin
from harness.plugins.bridge_runner import _execute_func
from harness.plugins.sandbox import SandboxError, SubprocessExecutor
from harness.services.skill_graph import (
    AntiPatternGuard,
    BuiltinSkillRegistryService,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
)

# Test service keys
KEY_A: ServiceKey[str] = ServiceKey("test.service.a")
KEY_B: ServiceKey[str] = ServiceKey("test.service.b")
KEY_C: ServiceKey[str] = ServiceKey("test.service.c")
KEY_D: ServiceKey[str] = ServiceKey("test.service.d")


class DelayPlugin(HarnessPlugin):
    """Plugin with controlled on_enable delay for concurrency verification."""

    def __init__(
        self,
        name: str,
        delay: float = 0.1,
        provides: list[ServiceKey[Any]] | None = None,
        requires: list[ServiceKey[Any]] | None = None,
        should_fail: bool = False,
    ) -> None:
        self._name = name
        self._delay = delay
        self._provides = provides or []
        self._requires = requires or []
        self._should_fail = should_fail
        self.enabled_at: float = 0.0

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return f"Delay plugin {self._name}"

    @property
    def trusted(self) -> bool:
        return True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return self._provides

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return self._requires

    async def on_load(self, ctx: ServiceContext) -> None:
        for k in self._provides:
            ctx.provide(k, f"val_{self._name}")

    async def on_enable(self) -> None:
        await asyncio.sleep(self._delay)
        if self._should_fail:
            raise RuntimeError(f"Simulated failure in {self._name}")
        self.enabled_at = time.perf_counter()


@pytest.mark.unit
class TestArchitecturalModernization:
    """Rigorous contract tests for architectural modernization upgrades."""

    @pytest.mark.asyncio
    async def test_enable_all_wave_parallel(self) -> None:
        """Verify that independent plugins in the same wave execute concurrently."""
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)

        # 3 independent plugins in wave 1 (each takes 0.15s)
        # Serial would take >= 0.45s, parallel wave takes ~0.15s-0.25s
        p1 = DelayPlugin("p1", delay=0.15, provides=[KEY_A])
        p2 = DelayPlugin("p2", delay=0.15, provides=[KEY_B])
        p3 = DelayPlugin("p3", delay=0.15, provides=[KEY_C])

        # p4 in wave 2 depends on p1, p2
        p4 = DelayPlugin("p4", delay=0.05, requires=[KEY_A, KEY_B], provides=[KEY_D])

        lc.discover(p1)
        lc.discover(p2)
        lc.discover(p3)
        lc.discover(p4)

        t_start = time.perf_counter()
        results = await lc.enable_all()
        elapsed = time.perf_counter() - t_start

        assert all(results.values()), f"Expected all plugins to succeed: {results}"
        assert lc.get_state("p1") == PluginState.ENABLED
        assert lc.get_state("p2") == PluginState.ENABLED
        assert lc.get_state("p3") == PluginState.ENABLED
        assert lc.get_state("p4") == PluginState.ENABLED

        # If executed serially, time would be at least 0.15 * 3 + 0.05 = 0.50s
        # With wave parallelism, wave 1 is max(0.15) + wave 2 is 0.05 = ~0.20s
        assert elapsed < 0.40, (
            f"Wave execution took too long ({elapsed:.3f}s), should be < 0.40s"
        )

    @pytest.mark.asyncio
    async def test_enable_all_wave_failure_isolation(self) -> None:
        """Verify that a failure in wave 1 skips its dependent in wave 2, but leaves independent plugins unaffected."""
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)

        p1_fail = DelayPlugin("p1_fail", delay=0.05, provides=[KEY_A], should_fail=True)
        p2_ok = DelayPlugin("p2_ok", delay=0.05, provides=[KEY_B])
        p3_dependent = DelayPlugin("p3_dep", delay=0.05, requires=[KEY_A])

        lc.discover(p1_fail)
        lc.discover(p2_ok)
        lc.discover(p3_dependent)

        results = await lc.enable_all()

        assert results["p1_fail"] is False
        assert results["p2_ok"] is True
        assert results["p3_dep"] is False
        assert lc.get_state("p1_fail") == PluginState.ERROR
        assert lc.get_state("p2_ok") == PluginState.ENABLED
        assert lc.get_state("p3_dep") == PluginState.ERROR

    @pytest.mark.asyncio
    async def test_bridge_runner_no_nested_asyncio_run(self) -> None:
        """Verify _execute_func handles async coroutines inside an active event loop without raising RuntimeError."""

        async def sample_coroutine(msg: str) -> str:
            await asyncio.sleep(0.01)
            return f"Processed: {msg}"

        def sample_sync(val: int) -> int:
            return val * 10

        # Must execute cleanly inside this already running async test loop
        res_async = await _execute_func(sample_coroutine, {"msg": "hello"})
        assert res_async == "Processed: hello"

        res_sync = await _execute_func(sample_sync, {"val": 42})
        assert res_sync == 420

    @pytest.mark.asyncio
    async def test_subprocess_memory_watchdog(self, tmp_path: Path) -> None:
        """Verify that SubprocessExecutor watchdog enforces RSS memory limit."""
        script = tmp_path / "mem_worker.py"
        script.write_text(
            """
import time

def allocate() -> str:
    data = "X" * (25 * 1024 * 1024)
    time.sleep(1.0)
    return f"Allocated {len(data)}"
"""
        )

        # Baseline Python process is ~18MB, so limit of 5MB will be exceeded immediately
        executor = SubprocessExecutor(
            script,
            memory_limit_mb=5.0,
            watchdog_interval=0.05,
        )
        await executor.start()
        assert executor.is_running

        # Allow the watchdog to sample RSS
        await asyncio.sleep(0.2)

        with pytest.raises(SandboxError) as exc_info:
            await executor.execute("allocate", timeout=5.0)

        assert "memory limit" in str(exc_info.value).lower()
        await executor.stop()
        assert not executor.is_running

    def test_anti_pattern_negation_exclusion(self) -> None:
        """Verify that AntiPatternGuard excludes matches preceded by negation words."""
        skill = SkillCardDefinition(
            name="boundary-guard",
            anti_patterns=[
                SkillAntiPatternDefinition(
                    name="Loose Boundaries",
                    symptom="Failing to enforce isolation",
                    remedy="Enforce sandbox",
                ),
                SkillAntiPatternDefinition(
                    name="Premature Optimization",
                    symptom="Optimizing before profiling",
                    remedy="Profile first",
                ),
            ],
        )

        # 1. Un-negated proposal -> violation flagged
        v1 = AntiPatternGuard.check_proposal(
            skill, "We will adopt loose boundaries for quick iteration."
        )
        assert len(v1) == 1
        assert v1[0].anti_pattern == "Loose Boundaries"

        # 2. Negated proposal using 'avoid' -> zero violations
        v2 = AntiPatternGuard.check_proposal(
            skill, "We must avoid loose boundaries when designing the module."
        )
        assert len(v2) == 0

        # 3. Negated proposal using 'do not' -> zero violations
        v3 = AntiPatternGuard.check_proposal(
            skill, "Please do not use loose boundaries in production."
        )
        assert len(v3) == 0

        # 4. Negated proposal using 'without' -> zero violations
        v4 = AntiPatternGuard.check_proposal(
            skill, "Proceed without premature optimization until metrics exist."
        )
        assert len(v4) == 0

    def test_route_intent_no_synthetic_chain(self) -> None:
        """Verify strict reachability (Rule 55): route_intent and get_chain do not synthesize fake paths."""
        registry = BuiltinSkillRegistryService()

        # Manually register two disconnected skills in cache
        skill_a = SkillCardDefinition(
            name="skill-alpha", triggers=["alpha task"], target="Alpha work"
        )
        skill_b = SkillCardDefinition(
            name="skill-beta", triggers=["beta task"], target="Beta work"
        )

        registry._skills_cache["skill-alpha"] = skill_a
        registry._skills_cache["skill-beta"] = skill_b
        registry._last_scan_time = time.time() + 1000.0  # Prevent scan override

        # Default get_chain with disconnected skills must return no_path
        chain_res = registry.get_chain(
            "skill-alpha", "skill-beta", fallback_direct=False
        )
        assert chain_res.status == "no_path"
        assert chain_res.chain == []

        # When explicitly opting into fallback_direct=True, it returns direct 2-node chain
        chain_fallback = registry.get_chain(
            "skill-alpha", "skill-beta", fallback_direct=True
        )
        assert chain_fallback.status == "ok"
        assert chain_fallback.chain == ["skill-alpha", "skill-beta"]

        # route_intent with a query matching both skills must have recommended_chain == []
        route_res = registry.route_intent("perform alpha task and beta task", top_k=2)
        assert len(route_res["matches"]) >= 2
        assert route_res["recommended_chain"] == []

    def test_extract_action_xml_tool_call(self) -> None:
        """Verify Rule 21: extract_action parses XML <tool_call> tags."""
        engine = StepExecutionEngine(llm=MagicMock(), tools=MagicMock())
        thought = (
            "I need to read the file first.\n"
            '<tool_call>{"action": "read_file", "input": {"path": "src/main.py"}}</tool_call>\n'
            "Waiting for result."
        )
        action, action_input = engine.extract_action(thought)
        assert action == "read_file"
        assert action_input == {"path": "src/main.py"}

    def test_extract_action_json_auto_repair(self) -> None:
        """Verify Rule 21: extract_action auto-repairs trailing commas and unclosed braces."""
        engine = StepExecutionEngine(llm=MagicMock(), tools=MagicMock())
        # Trailing comma in JSON object
        thought_comma = '{"action": "write_file", "input": {"data": "hello",}}'
        action, action_input = engine.extract_action(thought_comma)
        assert action == "write_file"
        assert action_input == {"data": "hello"}

        # Unclosed brace
        thought_unclosed = '{"action": "exec_cmd", "input": {"cmd": "ls"'
        action2, action_input2 = engine.extract_action(thought_unclosed)
        assert action2 == "exec_cmd"
        assert action_input2 == {"cmd": "ls"}

    def test_hot_swap_dispose_stack_no_accumulation(self) -> None:
        """Verify Rule 54: hot_swap purges stale inverse closures from _dispose_stack."""
        ctx = ServiceContext()
        ctx.provide(KEY_A, "v1", provider="plugin1")

        # Initial provide creates 1 inverse for KEY_A
        inverses_a = [
            inv
            for inv in ctx._dispose_stack
            if getattr(inv, "_realm_key", None) == KEY_A.name
        ]
        assert len(inverses_a) == 1

        # Hot-swap 5 times consecutively
        for i in range(5):
            ctx.hot_swap(KEY_A, f"v_swap_{i}", provider=f"plugin_swap_{i}")

        # Rule 54 Invariant: Dispose stack must not leak/accumulate orphaned inverses
        inverses_a_after = [
            inv
            for inv in ctx._dispose_stack
            if getattr(inv, "_realm_key", None) == KEY_A.name
        ]
        assert len(inverses_a_after) == 1
        assert ctx.require(KEY_A) == "v_swap_4"

    @pytest.mark.asyncio
    async def test_enable_all_wave_timeout_propagates(self) -> None:
        """Verify per-wave timeout bounds hanging plugin on_enable without blocking startup."""
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)

        # Hanging plugin that sleeps for 10 seconds
        hanging = DelayPlugin("hanging_plugin", delay=10.0, provides=[KEY_A])
        # Fast plugin in the same wave
        fast = DelayPlugin("fast_plugin", delay=0.01, provides=[KEY_B])

        lc.discover(hanging)
        lc.discover(fast)

        start = time.perf_counter()
        # Enable with 0.1s timeout
        results = await lc.enable_all(enable_timeout=0.1)
        elapsed = time.perf_counter() - start

        # Must finish well under the 10s hang time (e.g. < 1.0s)
        assert elapsed < 1.0
        assert results["hanging_plugin"] is False
        assert results["fast_plugin"] is True

        hanging_entry = lc._entries["hanging_plugin"]
        assert hanging_entry.state == PluginState.ERROR
        assert "Timed out" in (hanging_entry.error or "") or "Timeout" in (
            hanging_entry.error or ""
        )

        fast_entry = lc._entries["fast_plugin"]
        assert fast_entry.state == PluginState.ENABLED
