"""Contract verification test suite for MCP Server & Router Decomposition (Cycle 43).

Verifies:
1. Subpackage structure and strict line count bounds (Rule 11: all submodules <= 200 lines).
2. Slotted dataclass contracts on request context (Rule 12).
3. 100% backward-compatible facade re-exports across harness.mcp.server.
4. Typed service key MCP_REGISTRY_KEY (Rule 2).
5. Middleware onion interceptor pipeline execution and access control policies.
6. Custom resource and prompt registration in MCPRegistry.
7. End-to-end tool and batch dispatching through HarnessMCPServer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
import pytest

from harness.kernel.context import ServiceKey
from harness.mcp.server import (
    AsyncStdioServerTransport,
    HarnessMCPServer,
    MCPAccessControlInterceptor,
    MCPHandler,
    MCPInterceptor,
    MCPInterceptorPipeline,
    MCPMethodRouter,
    MCPRegistry,
    MCPRequestContext,
    MCPTelemetryInterceptor,
    MCP_REGISTRY_KEY,
)
from harness.services.tools import ToolRegistry

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TestMCPServerDecompositionArchitecture:
    """Architectural and structural invariants for mcp/server subpackage."""

    def test_submodule_structure_and_line_limits(self) -> None:
        """Rule 11: All decomposed submodules must strictly remain <= 200 lines."""
        pkg_dir = Path(__file__).parent.parent / "src" / "harness" / "mcp" / "server"
        assert pkg_dir.is_dir(), f"Expected directory at {pkg_dir}"

        expected_modules = {
            "__init__.py",
            "context.py",
            "interceptors.py",
            "registry.py",
            "router.py",
            "server.py",
            "transport.py",
        }

        found_modules = {p.name for p in pkg_dir.glob("*.py")}
        assert expected_modules.issubset(found_modules)

        for mod_name in expected_modules:
            mod_path = pkg_dir / mod_name
            lines = len(mod_path.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"Module {mod_name} has {lines} lines, exceeding Rule 11 limit (200)"

    def test_slotted_request_context_and_service_key(self) -> None:
        """Rule 12 & Rule 2: MCPRequestContext must be slotted, and MCP_REGISTRY_KEY typed."""
        ctx = MCPRequestContext(request_id=1, method="test", params={"x": 1})
        assert hasattr(ctx, "__slots__")
        assert not hasattr(ctx, "__dict__")

        assert isinstance(MCP_REGISTRY_KEY, ServiceKey)
        assert MCP_REGISTRY_KEY.name == "mcp.registry"

    @pytest.mark.asyncio
    async def test_interceptor_pipeline_onion_execution(self) -> None:
        """Verify middleware onion chain wraps execution in expected order."""
        order: list[str] = []

        class FirstInterceptor(MCPInterceptor):
            async def intercept(self, ctx, next_handler):
                order.append("first_in")
                res = await next_handler(ctx)
                order.append("first_out")
                return res

        class SecondInterceptor(MCPInterceptor):
            async def intercept(self, ctx, next_handler):
                order.append("second_in")
                res = await next_handler(ctx)
                order.append("second_out")
                return res

        pipeline = MCPInterceptorPipeline([FirstInterceptor(), SecondInterceptor()])
        ctx = MCPRequestContext(request_id=1, method="dummy", params={})

        async def terminal(c):
            order.append("terminal")
            return {"status": "ok"}

        res = await pipeline.execute(ctx, terminal)
        assert res == {"status": "ok"}
        assert order == ["first_in", "second_in", "terminal", "second_out", "first_out"]

    @pytest.mark.asyncio
    async def test_access_control_interceptor(self) -> None:
        """Verify access control interceptor rejects unauthorized methods."""
        guard = MCPAccessControlInterceptor(allowed_methods={"ping", "tools/list"})
        pipeline = MCPInterceptorPipeline([guard])

        async def ok_term(c: MCPRequestContext) -> dict[str, Any]:
            return {"result": "pong"}

        async def denied_term(c: MCPRequestContext) -> dict[str, Any]:
            return {"result": "should_not_run"}

        # Allowed
        ctx_ok = MCPRequestContext(request_id=1, method="ping", params={})
        res_ok = await pipeline.execute(ctx_ok, ok_term)
        assert res_ok == {"result": "pong"}

        # Denied
        ctx_denied = MCPRequestContext(request_id=2, method="dangerous_call", params={})
        res_denied = await pipeline.execute(ctx_denied, denied_term)
        assert "error" in res_denied
        assert res_denied["error"]["code"] == -32001
        assert "Access denied" in res_denied["error"]["message"]

    @pytest.mark.asyncio
    async def test_registry_resource_and_prompt_catalog(self) -> None:
        """Verify dynamic resource and prompt catalog listing and resolution."""
        tools = ToolRegistry()
        registry = MCPRegistry(tools)

        resources = registry.list_resources()
        assert any(r["uri"] == "harness://system/status" for r in resources)
        assert any(r["uri"] == "harness://plugins/catalog" for r in resources)

        # Read status resource
        res_data = await registry.read_resource("harness://system/status")
        assert res_data is not None
        status_dict, mime = res_data
        assert "tools_count" in status_dict
        assert mime == "application/json"

        # List prompts
        prompts = registry.list_prompts()
        assert any(p["name"] == "agent_task" for p in prompts)
        desc, msgs = await registry.get_prompt("agent_task", {"task": "test goal"})
        assert len(msgs) == 1
        assert "test goal" in msgs[0]["content"]["text"]

    @pytest.mark.asyncio
    async def test_harness_mcp_server_full_dispatch_and_batch(self) -> None:
        """Verify HarnessMCPServer handles initialize, tools/list, and batch requests."""
        tools = ToolRegistry()

        async def echo(text: str = "") -> str:
            return f"echo:{text}"

        tools.register(
            name="echo",
            description="Echoes input",
            executor=echo,
            parameters_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
            },
        )

        server = HarnessMCPServer(tools)

        # 1. Initialize
        init_res = await server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        assert init_res["result"]["serverInfo"]["name"] == "harness-mcp"

        # 2. Tool invocation
        call_res = await server.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"text": "hello"}},
        })
        assert "result" in call_res
        assert call_res["result"]["content"][0]["text"] == "echo:hello"

        # 3. Batch handling via raw transport
        batch_line = json.dumps([
            {"jsonrpc": "2.0", "id": 10, "method": "ping", "params": {}},
            {"jsonrpc": "2.0", "id": 11, "method": "tools/list", "params": {}},
        ])
        raw_resp = await server.dispatch_raw(batch_line)
        assert raw_resp is not None
        batch_data = json.loads(raw_resp)
        assert len(batch_data) == 2
        assert batch_data[0]["id"] == 10
        assert batch_data[1]["id"] == 11
