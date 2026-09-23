"""Tests for architecture hardening across IoC kernel, sandbox transport, and skill graph."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.plugins.base import HarnessPlugin
from harness.plugins.sandbox import SubprocessExecutor
from harness.plugins.transport import StdioJsonRpcTransport, TransportError
from harness.services.skill_graph import (
    BuiltinSkillRegistryService,
)


class DummyService:
    def __init__(self, val: str) -> None:
        self.val = val


KEY_A = ServiceKey[DummyService]("dummy.service.a")
KEY_B = ServiceKey[DummyService]("dummy.service.b")
KEY_C = ServiceKey[DummyService]("dummy.service.c")


class FlakyPlugin(HarnessPlugin):
    def __init__(self, name: str = "flaky-plugin") -> None:
        self._name = name
        self.should_fail = True
        self.load_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    async def on_load(self, context: ServiceContext) -> None:
        self.load_count += 1
        if self.should_fail:
            raise RuntimeError("Simulated transient initialization error")
        context.provide(KEY_A, DummyService("recovered"), provider=self.name)


class SimplePlugin(HarnessPlugin):
    def __init__(self, name: str, provides: list[Any] | None = None, requires: list[Any] | None = None) -> None:
        self._name = name
        self._provides = provides or []
        self._requires = requires or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[Any]:
        return self._provides

    @property
    def requires(self) -> list[Any]:
        return self._requires


@pytest.mark.unit
class TestIoCKernelHardening:
    """Verify dispose stack purging and lifecycle state recovery."""

    def test_context_dispose_stack_purging(self) -> None:
        ctx = ServiceContext()
        ctx.provide(KEY_A, DummyService("a"), provider="plugin-alpha")
        ctx.provide(KEY_B, DummyService("b"), provider="plugin-alpha")
        ctx.provide(KEY_C, DummyService("c"), provider="plugin-beta")

        assert len(ctx._dispose_stack) == 3

        # Revoking single service purges its closure
        revoked = ctx.revoke(KEY_A)
        assert revoked is True
        assert len(ctx._dispose_stack) == 2
        assert not any(getattr(inv, "_realm_key", None) == KEY_A.name for inv in ctx._dispose_stack)

        # Revoking all from plugin purges all matching closures
        revoked_all = ctx.revoke_all_from("plugin-alpha")
        assert revoked_all == [KEY_B.name]
        assert len(ctx._dispose_stack) == 1
        assert getattr(ctx._dispose_stack[0], "_provider", None) == "plugin-beta"

    @pytest.mark.asyncio
    async def test_lifecycle_error_recovery(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        plugin = FlakyPlugin()

        lifecycle.discover(plugin)
        # ensure_enabled will fail on load and enter ERROR state
        ok = await lifecycle.ensure_enabled(plugin.name)
        assert ok is False
        assert lifecycle.plugins[plugin.name].state == PluginState.ERROR

        # Now fix plugin and re-drive ensure_enabled
        plugin.should_fail = False
        recovered = await lifecycle.ensure_enabled(plugin.name)
        assert recovered is True
        assert lifecycle.plugins[plugin.name].state == PluginState.ENABLED
        assert ctx.require(KEY_A).val == "recovered"

    def test_lifecycle_dependency_graph_epoch_cache(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        p1 = SimplePlugin("p1", provides=[KEY_A])
        p2 = SimplePlugin("p2", requires=[KEY_A])

        lifecycle.discover(p1)
        lifecycle.discover(p2)

        g1 = lifecycle.build_dependency_graph(["p1", "p2"])
        g2 = lifecycle.build_dependency_graph(["p1", "p2"])
        assert g1 is g2  # Cached hit within same epoch

        # Mutate lifecycle with new discovery
        p3 = SimplePlugin("p3")
        lifecycle.discover(p3)

        g3 = lifecycle.build_dependency_graph(["p1", "p2", "p3"])
        assert g3 is not g1  # Recomputed because epoch incremented


@pytest.mark.unit
@pytest.mark.asyncio
class TestSandboxAndTransportHardening:
    """Verify staged runner execution without -c strings and stderr drain."""

    async def test_subprocess_staged_runner(self, tmp_path: Path) -> None:
        worker_script = tmp_path / "calc_worker.py"
        worker_script.write_text(
            """def multiply(a: int, b: int) -> int:
    return a * b
""",
            encoding="utf-8",
        )

        executor = SubprocessExecutor(worker_script)
        await executor.start()

        assert executor.is_running
        assert executor._transport is not None
        # Verify no inline "-c" commands
        assert "-c" not in executor._transport.args
        assert any("bridge_runner.py" in str(arg) for arg in executor._transport.args)

        res = await executor.execute("multiply", {"a": 7, "b": 6})
        assert res["status"] == "ok"
        assert res["result"] == 42

        await executor.stop()
        assert not executor.is_running

    async def test_transport_stderr_drain_and_diagnostics(self, tmp_path: Path) -> None:
        server_script = tmp_path / "noisy_server.py"
        server_script.write_text(
            """import sys, json
sys.stderr.write("Diagnostic alert line 1\\n")
sys.stderr.flush()
for line in sys.stdin:
    req = json.loads(line.strip())
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": "acknowledged"}) + "\\n")
    sys.stdout.flush()
""",
            encoding="utf-8",
        )

        transport = StdioJsonRpcTransport(
            "python",
            [str(server_script)],
        )
        await transport.start()

        res = await transport.call("ping")
        assert res.get("result") == "acknowledged"

        # Give proactor loop a tick to process stderr stream
        await asyncio.sleep(0.05)
        assert any("Diagnostic alert line 1" in line for line in transport.stderr_lines)

        await transport.stop()

    async def test_transport_crash_surfaces_stderr(self, tmp_path: Path) -> None:
        crash_script = tmp_path / "crashing_server.py"
        crash_script.write_text(
            """import sys
sys.stderr.write("Fatal startup assertion failed: ModuleMissing\\n")
sys.stderr.flush()
sys.exit(1)
""",
            encoding="utf-8",
        )

        transport = StdioJsonRpcTransport(
            "python",
            [str(crash_script)],
        )
        await transport.start()
        await asyncio.sleep(0.05)

        with pytest.raises(TransportError) as exc_info:
            await transport.call("check")
        assert "ModuleMissing" in str(exc_info.value)

        await transport.stop()


@pytest.mark.unit
class TestSkillGraphHardening:
    """Verify no_path semantics, frontmatter dependencies, and confidence filtering."""

    def test_skill_registry_no_path_semantics(self) -> None:
        registry = BuiltinSkillRegistryService()
        # Nonexistent skills with fallback_direct=False should return status: no_path
        res_strict = registry.get_chain("unrelated-alpha", "unrelated-beta", fallback_direct=False)
        assert res_strict.status == "no_path"
        assert res_strict.chain == []
        assert res_strict.length == 0

        # With fallback_direct=True, returns synthetic 2-hop chain for backwards compatibility
        res_compat = registry.get_chain("unrelated-alpha", "unrelated-beta", fallback_direct=True)
        assert res_compat.status == "ok"
        assert res_compat.chain == ["unrelated-alpha", "unrelated-beta"]
        assert res_compat.length == 2

    def test_skill_registry_explicit_yaml_dependencies(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "sample-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: sample-skill
description: "A sample skill for testing explicit frontmatter dependencies"
dependencies:
  - dep-alpha
  - dep-beta
---

# Sample Skill
Implementation details here.
""",
            encoding="utf-8",
        )

        registry = BuiltinSkillRegistryService(default_root=str(tmp_path))
        card = registry._parse_skill_directory(skill_dir)
        assert card is not None
        assert card.name == "sample-skill"
        assert "dep-alpha" in card.dependencies
        assert "dep-beta" in card.dependencies

    def test_skill_registry_confidence_threshold_filtering(self) -> None:
        registry = BuiltinSkillRegistryService()
        # Intent with low confidence threshold returns matches
        res_low = registry.route_intent("architect system", min_confidence=0.10)
        assert res_low["status"] == "ok"

        # Very high confidence threshold filters out weak matches
        res_high = registry.route_intent("architect system", min_confidence=0.99)
        assert res_high["status"] == "ok"
        assert len(res_high["matches"]) <= len(res_low["matches"])
        for m in res_high["matches"]:
            assert m["confidence"] >= 0.99
