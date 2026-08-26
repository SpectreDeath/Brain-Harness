"""Tests for Sandbox Executors (InProcess, Subprocess, Venv) and SandboxedPlugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)
from harness.plugins.sandbox import (
    InProcessExecutor,
    SandboxError,
    SubprocessExecutor,
)
from harness.plugins.sandboxed import SandboxedPlugin
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry


class DummyModule:
    def add(self, a: int, b: int) -> int:
        return a + b

    async def async_echo(self, text: str) -> str:
        return f"Echo: {text}"

    def fail(self) -> None:
        raise ValueError("Intentional crash")


@pytest.mark.unit
@pytest.mark.asyncio
class TestInProcessExecutor:
    async def test_in_process_execution(self) -> None:
        executor = InProcessExecutor(DummyModule())
        assert not executor.is_running

        await executor.start()
        assert executor.is_running

        # Synchronous function
        res = await executor.execute("add", {"a": 2, "b": 3})
        assert res == {"status": "ok", "result": 5}

        # Async function
        res_async = await executor.execute("async_echo", {"text": "hello"})
        assert res_async == {"status": "ok", "result": "Echo: hello"}

        # Error handling
        res_err = await executor.execute("fail")
        assert res_err["status"] == "error"
        assert "Intentional crash" in res_err["error"]

        # Missing method
        res_missing = await executor.execute("not_found")
        assert res_missing["status"] == "error"

        await executor.stop()
        assert not executor.is_running


@pytest.mark.integration
@pytest.mark.asyncio
class TestSubprocessExecutor:
    async def test_subprocess_execution(self, tmp_path: Path) -> None:
        script = tmp_path / "worker.py"
        script.write_text(
            """
def compute(x: int, y: int) -> int:
    return x * y

def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
        )

        executor = SubprocessExecutor(script)
        await executor.start()
        assert executor.is_running

        res = await executor.execute("compute", {"x": 6, "y": 7})
        assert res == {"status": "ok", "result": 42}

        res_greet = await executor.execute("greet", {"name": "Harness"})
        assert res_greet == {"status": "ok", "result": "Hello, Harness!"}

        # Missing method in subprocess
        res_missing = await executor.execute("unknown_fn")
        assert res_missing["status"] == "error"

        await executor.stop()
        assert not executor.is_running


@pytest.mark.unit
@pytest.mark.asyncio
class TestSandboxedPluginAdapter:
    async def test_sandboxed_plugin_full_lifecycle(self, tmp_path: Path) -> None:
        script = tmp_path / "main.py"
        script.write_text("def run(msg: str) -> str:\n    return f'Ran: {msg}'\n")

        manifest = PluginManifest(
            name="sandboxed_tool",
            version="1.0.0",
            description="Sandboxed test tool",
            entrypoint="main.py",
            provides=["tool.sandboxed_tool"],
            requires=[TOOL_REGISTRY_KEY.name],
            isolation=IsolationMode.IN_PROCESS,
            entrypoints=[
                EntrypointSpec(
                    name="run",
                    description="Run tool action",
                    parameters=[ParameterSpec(name="msg", type="string", required=True)],
                )
            ],
        )

        class ToolImpl:
            def run(self, msg: str) -> str:
                return f"Ran: {msg}"

        plugin = SandboxedPlugin(manifest, tmp_path, executor=InProcessExecutor(ToolImpl()))
        assert plugin.name == "sandboxed_tool"
        assert plugin.version == "1.0.0"
        assert plugin.description == "Sandboxed test tool"
        assert len(plugin.provides) == 1
        assert len(plugin.requires) == 1
        assert plugin.root == tmp_path
        ctx = ServiceContext()
        tools = ToolRegistry()
        ctx.provide(TOOL_REGISTRY_KEY, tools)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        # Check tool was registered
        assert "sandboxed_tool.run" in tools
        res = await tools.invoke("sandboxed_tool.run", {"msg": "hello sandbox"})
        assert res == {"status": "ok", "result": "Ran: hello sandbox"}

        # Disable and verify tool unregistration
        await plugin.on_disable()
        assert "sandboxed_tool.run" not in tools

        # Unload
        await plugin.on_unload()

    async def test_sandboxed_plugin_auto_provisioning(self, tmp_path: Path) -> None:
        """Test that SandboxedPlugin automatically provisions its executor without explicit injection."""
        script = tmp_path / "main.py"
        script.write_text("def ping(text: str) -> str:\n    return f'PONG: {text}'\n")

        manifest = PluginManifest(
            name="auto_ping_tool",
            version="1.0.0",
            entrypoint="main.py",
            provides=["tool.auto_ping"],
            requires=[TOOL_REGISTRY_KEY.name],
            isolation=IsolationMode.IN_PROCESS,
            trusted=True,
            entrypoints=[
                EntrypointSpec(
                    name="ping",
                    parameters=[ParameterSpec(name="text", type="string", required=True)],
                )
            ],
        )

        plugin = SandboxedPlugin(manifest, tmp_path)  # No explicit executor!
        ctx = ServiceContext()
        tools = ToolRegistry()
        ctx.provide(TOOL_REGISTRY_KEY, tools)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        assert "auto_ping_tool.ping" in tools
        res = await tools.invoke("auto_ping_tool.ping", {"text": "hello auto"})
        assert res == {"status": "ok", "result": "PONG: hello auto"}

        await plugin.on_disable()
        await plugin.on_unload()

    async def test_domain_plugin_runtime_invocation(self) -> None:
        """Verify workspace domain plugins invoke successfully through HarnessRuntime."""
        from harness.kernel.runtime import HarnessRuntime

        async with HarnessRuntime.create(
            plugin_dirs=[Path("plugins/security_and_forensics/network_forensics")]
        ) as rt:
            assert rt.tools is not None
            assert "domain.network_forensics.audit_port_configuration" in rt.tools

            res = await rt.tools.invoke(
                "domain.network_forensics.audit_port_configuration",
                {"open_ports": [22, 23, 80, 443, 6379]},
            )
            assert res["status"] == "ok"
            assert res["result"]["secure"] is False
            assert res["result"]["vulnerabilities_found"] >= 3

    async def test_sandboxed_plugin_health_and_metrics(self, tmp_path: Path) -> None:
        """Test health diagnostics and metrics tracking seams on SandboxedPlugin."""
        script = tmp_path / "main.py"
        script.write_text("def calc(n: int) -> int:\n    return n * 2\n")

        manifest = PluginManifest(
            name="metric_calc_tool",
            version="2.0.0",
            entrypoint="main.py",
            provides=["tool.metric_calc"],
            requires=[TOOL_REGISTRY_KEY.name],
            isolation=IsolationMode.IN_PROCESS,
            trusted=True,
            entrypoints=[
                EntrypointSpec(
                    name="calc",
                    parameters=[ParameterSpec(name="n", type="integer", required=True)],
                )
            ],
        )

        plugin = SandboxedPlugin(manifest, tmp_path)
        ctx = ServiceContext()
        tools = ToolRegistry()
        ctx.provide(TOOL_REGISTRY_KEY, tools)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        health = plugin.get_health()
        assert health["name"] == "metric_calc_tool"
        assert health["status"] == "healthy"
        assert health["version"] == "2.0.0"
        assert health["trusted"] is True

        res = await plugin.call("calc", {"n": 21})
        assert res["status"] == "ok"
        assert res["result"] == 42

        metrics = plugin.get_metrics()
        assert metrics["invocations"] == 1
        assert metrics["errors"] == 0
        assert metrics["total_duration_ms"] > 0.0

        await plugin.on_disable()
        await plugin.on_unload()

    async def test_sandbox_error(self) -> None:
        err = SandboxError("venv", "Failed to build")
        assert "venv" in str(err)
        assert "Failed to build" in str(err)
