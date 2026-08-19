"""Tests for all exercise solutions to ensure curriculum correctness."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginState
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistryPlugin

ROOT = Path(__file__).parent.parent


def _import_solution(rel_path: str) -> Any:
    file_path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.unit
class TestExerciseSolutions:
    def test_ex_01_01_service_keys(self) -> None:
        mod = _import_solution("exercises/01-micro-kernel-and-ioc/01.01-service-keys-and-context/solution/main.py")
        ctx = mod.setup_kernel()
        cfg = ctx.require(mod.CONFIG_KEY)
        cfg.set("mode", "prod")
        assert cfg.get("mode") == "prod"
        assert cfg.get("missing", "def") == "def"

    @pytest.mark.asyncio
    async def test_ex_01_02_topological_lifecycle(self) -> None:
        mod = _import_solution("exercises/01-micro-kernel-and-ioc/01.02-topological-plugin-lifecycle/solution/main.py")
        lifecycle = await mod.run_lifecycle()
        assert lifecycle.plugins["plugin.a"].state == PluginState.ENABLED
        assert lifecycle.plugins["plugin.b"].state == PluginState.ENABLED

    @pytest.mark.asyncio
    async def test_ex_01_03_event_bus(self) -> None:
        mod = _import_solution("exercises/01-micro-kernel-and-ioc/01.03-immutable-event-bus/solution/main.py")
        bus, captured = await mod.run_event_pipeline()
        assert bus is not None
        assert len(captured) >= 1
        assert captured[0].payload == {"plugin": "custom"}

    @pytest.mark.asyncio
    async def test_ex_02_01_authoring_custom_plugins(self) -> None:
        mod = _import_solution("exercises/02-plugin-architecture-and-sandboxing/02.01-authoring-custom-plugins/solution/main.py")
        ctx = ServiceContext()
        tools_plugin = ToolRegistryPlugin()
        await tools_plugin.on_load(ctx)

        text_plugin = mod.TextTransformPlugin()
        await text_plugin.on_load(ctx)
        await text_plugin.on_enable()

        registry = ctx.require(TOOL_REGISTRY_KEY)
        res = await registry.invoke("text.reverse", {"text": "BrainHarness"})
        assert res["status"] == "ok"
        assert res["result"] == "ssenraHniarB"

    @pytest.mark.asyncio
    async def test_ex_02_02_stdio_sandboxing(self) -> None:
        mod = _import_solution("exercises/02-plugin-architecture-and-sandboxing/02.02-stdio-jsonrpc-sandboxing/solution/main.py")
        res = await mod.run_rpc_echo({"hello": "world"})
        assert res["echo"] == {"hello": "world"}

    @pytest.mark.asyncio
    async def test_ex_02_03_ingestion(self, tmp_path: Path) -> None:
        mod = _import_solution("exercises/02-plugin-architecture-and-sandboxing/02.03-github-ingestion-pipeline/solution/main.py")
        (tmp_path / "calc.py").write_text(
            "def multiply(a: int, b: int) -> int:\n"
            "    \"\"\"Multiply two numbers.\"\"\"\n"
            "    return a * b\n"
        )
        plugin = await mod.ingest_local_repo(tmp_path)
        assert len(plugin.manifest.entrypoints) >= 1

    @pytest.mark.asyncio
    async def test_ex_03_01_tool_registry(self) -> None:
        mod = _import_solution("exercises/03-agent-loops-and-planning/03.01-tool-registry-and-validation/solution/main.py")
        res = await mod.run_tool_registration_demo()
        assert res["status"] == "ok"
        assert res["result"] == "Hello Harness"

    @pytest.mark.asyncio
    async def test_ex_03_02_react_agent(self) -> None:
        mod = _import_solution("exercises/03-agent-loops-and-planning/03.02-react-reasoning-and-acting/solution/main.py")
        res = await mod.run_agent_task()
        assert res.status == "completed"
        assert "12" in res.final_answer

    def test_ex_03_03_dag_planning(self) -> None:
        mod = _import_solution("exercises/03-agent-loops-and-planning/03.03-hierarchical-dag-planning/solution/main.py")
        res = mod.run_dag_milestones()
        assert res["initial_unblocked"] == 2
        assert res["second_unblocked"] == 1
        assert res["all_completed"] is True

    @pytest.mark.asyncio
    async def test_ex_04_01_memtext(self) -> None:
        mod = _import_solution("exercises/04-ecosystem-bridges-and-mcp/04.01-memtext-persistent-memory/solution/main.py")
        recalled = await mod.run_memory_workflow()
        assert len(recalled) == 2

    @pytest.mark.asyncio
    async def test_ex_04_02_em_cubed(self) -> None:
        mod = _import_solution("exercises/04-ecosystem-bridges-and-mcp/04.02-em-cubed-symbolic-reasoning/solution/main.py")
        res = await mod.run_logic_reasoning()
        assert res.get("status") in ("ok", "success") or "result" in res

    @pytest.mark.asyncio
    async def test_ex_04_03_mcp_server(self) -> None:
        mod = _import_solution("exercises/04-ecosystem-bridges-and-mcp/04.03-mcp-protocol-integration/solution/main.py")
        res = await mod.handle_mcp_discovery()
        assert "result" in res
        assert "tools" in res["result"]
        tools = [t["name"] for t in res["result"]["tools"]]
        assert "system.ping" in tools
