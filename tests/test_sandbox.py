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


@pytest.mark.unit
def test_posix_cgroup_lifecycle(tmp_path: Path) -> None:
    """Verify privilege-aware Linux cgroup v2 detection, limit application, and cleanup."""
    fake_sys_cgroup = tmp_path / "sys" / "fs" / "cgroup"
    fake_slice = fake_sys_cgroup / "user.slice" / "user-1000.slice"
    fake_slice.mkdir(parents=True)
    (fake_sys_cgroup / "cgroup.controllers").write_text("memory pids\n", encoding="utf-8")

    fake_proc_cgroup = tmp_path / "proc_self_cgroup"
    fake_proc_cgroup.write_text("0::/user.slice/user-1000.slice\n", encoding="utf-8")

    dummy_script = tmp_path / "dummy.py"
    dummy_script.write_text("def ping(): return 'pong'\n", encoding="utf-8")

    executor = SubprocessExecutor(dummy_script, memory_limit_mb=256.0)

    # 1. Apply limits in mock Linux cgroup v2 hierarchy
    success = executor._apply_cgroup_limits(
        pid=4242,
        limit_mb=256.0,
        cgroup_root=fake_sys_cgroup,
        proc_cgroup=fake_proc_cgroup,
    )
    assert success is True
    assert executor._cgroup_path is not None
    assert executor._cgroup_path.exists()
    assert (executor._cgroup_path / "memory.max").read_text(encoding="utf-8") == str(256 * 1024 * 1024)
    assert (executor._cgroup_path / "cgroup.procs").read_text(encoding="utf-8") == "4242"

    # 2. Cleanup
    cgroup_dir = executor._cgroup_path
    (cgroup_dir / "cgroup.procs").unlink()
    (cgroup_dir / "memory.max").unlink()
    executor._cleanup_cgroup()
    assert not cgroup_dir.exists()
    assert executor._cgroup_path is None

    # 3. PermissionError / non-writable slice fallback without raising
    non_writable = tmp_path / "read_only"
    non_writable.mkdir()
    res = executor._apply_cgroup_limits(
        pid=9999,
        limit_mb=128.0,
        cgroup_root=non_writable,
        proc_cgroup=fake_proc_cgroup,
    )
    assert res is False
    assert executor._cgroup_path is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transport_capability_negotiation(tmp_path: Path) -> None:
    """Verify StdioJsonRpcTransport negotiates capabilities with the bridge runner."""
    script = tmp_path / "mock_plugin.py"
    script.write_text("def ping(): return 'pong'\n", encoding="utf-8")

    executor = SubprocessExecutor(script)
    await executor.start()
    try:
        assert executor.transport is not None
        assert "shm" in executor.transport.peer_capabilities
    finally:
        await executor.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transport_shm_round_trip(tmp_path: Path) -> None:
    """Send a >64KB payload through StdioJsonRpcTransport and verify byte-for-byte recovery via SHM."""
    import hashlib

    script = tmp_path / "echo_large.py"
    script.write_text(
        "import hashlib\n"
        "def echo_blob(data: str) -> dict:\n"
        "    digest = hashlib.sha256(data.encode('utf-8')).hexdigest()\n"
        "    return {'length': len(data), 'sha256': digest}\n",
        encoding="utf-8",
    )

    executor = SubprocessExecutor(script)
    await executor.start()
    try:
        # 256 KB string payload
        large_str = "A" * (256 * 1024)
        expected_sha256 = hashlib.sha256(large_str.encode("utf-8")).hexdigest()
        res = await executor.execute("echo_blob", {"data": large_str}, timeout=15.0)
        assert res["status"] == "ok"
        assert res["result"]["length"] == len(large_str)
        assert res["result"]["sha256"] == expected_sha256
        # Confirm that SHM transport was actually negotiated and used
        assert executor.transport is not None
        assert "shm" in executor.transport.peer_capabilities
    finally:
        await executor.stop()

