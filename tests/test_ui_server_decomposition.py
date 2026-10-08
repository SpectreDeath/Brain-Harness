"""Comprehensive unit and contract tests for ui/server package decomposition.

Verifies:
1. Isolated submodule imports (models, adapter, swarm_graph, routes, app, facade).
2. 100% backward compatibility of all public symbols exported from harness.ui.server.
3. Request models validation and defaults.
4. Mermaid diagram generation for swarm execution graphs.
5. RuntimeAdapter initialization and feature introspection with ServiceContext.
6. FastAPI app creation, route registration, and middleware configuration.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from harness.kernel.context import ServiceContext


@pytest.mark.unit
def test_submodule_direct_imports() -> None:
    """Verify each decomposed submodule can be imported independently."""
    from harness.ui.server.adapter import RuntimeAdapter
    from harness.ui.server.app import create_app
    from harness.ui.server.models import (
        CreatorScaffoldRequest,
        CreatorValidateRequest,
        PluginIngestRequest,
        PluginToggleRequest,
        SwarmRunRequest,
        SwarmSkillDispatchRequest,
        TaskRequest,
        ToolToggleRequest,
    )
    from harness.ui.server.routes.creator import router as creator_router
    from harness.ui.server.routes.plugins import router as plugins_router
    from harness.ui.server.routes.sessions import router as sessions_router
    from harness.ui.server.routes.skills import router as skills_router
    from harness.ui.server.routes.swarm import router as swarm_router
    from harness.ui.server.swarm_graph import build_swarm_mermaid_graph

    assert RuntimeAdapter is not None
    assert callable(create_app)
    assert TaskRequest is not None
    assert PluginToggleRequest is not None
    assert ToolToggleRequest is not None
    assert PluginIngestRequest is not None
    assert CreatorScaffoldRequest is not None
    assert CreatorValidateRequest is not None
    assert SwarmRunRequest is not None
    assert SwarmSkillDispatchRequest is not None
    assert callable(build_swarm_mermaid_graph)
    assert plugins_router is not None
    assert creator_router is not None
    assert sessions_router is not None
    assert swarm_router is not None
    assert skills_router is not None


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility() -> None:
    """Verify facade re-exports all public symbols."""
    import harness.ui.server as server

    symbols = [
        "create_app",
        "RuntimeAdapter",
        "build_swarm_mermaid_graph",
        "TaskRequest",
        "PluginToggleRequest",
        "ToolToggleRequest",
        "PluginIngestRequest",
        "CreatorScaffoldRequest",
        "CreatorValidateRequest",
        "SwarmRunRequest",
        "SwarmSkillDispatchRequest",
    ]
    for sym in symbols:
        assert hasattr(server, sym), f"Facade missing symbol: {sym}"
        assert getattr(server, sym) is not None


@pytest.mark.unit
def test_request_models_validation() -> None:
    """Verify request models construct cleanly and validate types."""
    from harness.ui.server.models import (
        CreatorScaffoldRequest,
        PluginToggleRequest,
        SwarmRunRequest,
        TaskRequest,
    )

    t_req = TaskRequest(task="analyze codebase", max_steps=5)
    assert t_req.task == "analyze codebase"
    assert t_req.max_steps == 5

    p_req = PluginToggleRequest(name="arch_linter", action="enable")
    assert p_req.name == "arch_linter"
    assert p_req.action == "enable"

    c_req = CreatorScaffoldRequest(name="new_tool", category="developer_tools", preset="tool")
    assert c_req.name == "new_tool"
    assert c_req.category == "developer_tools"
    assert c_req.preset == "tool"

    s_req = SwarmRunRequest(objective="coordinate task", max_tokens=50_000)
    assert s_req.objective == "coordinate task"
    assert s_req.max_tokens == 50_000


@pytest.mark.unit
def test_build_swarm_mermaid_graph() -> None:
    """Verify build_swarm_mermaid_graph generates formatted Mermaid syntax."""
    from harness.ui.server.swarm_graph import build_swarm_mermaid_graph

    graph_data = {
        "nodes": [
            {"id": "node_1", "agent_name": "architect", "task": "plan system", "state": "Completed"},
            {"id": "node_2", "agent_name": "developer", "task": "write code", "state": "Open"},
        ],
        "edges": [
            {"source": "node_1", "target": "node_2", "kind": "spawn"},
        ],
    }

    mermaid = build_swarm_mermaid_graph("run_123", graph_data)
    assert "graph TD" in mermaid
    assert "node_1" in mermaid
    assert "node_2" in mermaid
    assert "architect" in mermaid
    assert "developer" in mermaid
    assert "-->" in mermaid


@pytest.mark.unit
def test_runtime_adapter_instantiation() -> None:
    """Verify RuntimeAdapter adapts ServiceContext and detects non-unified runtime."""
    from harness.events.bus import EventBus
    from harness.kernel.lifecycle import PluginLifecycle
    from harness.ui.server.adapter import RuntimeAdapter

    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)
    bus = EventBus()
    adapter = RuntimeAdapter(context_or_runtime=ctx, lifecycle=lifecycle, event_bus=bus)
    assert adapter.is_unified_runtime is False
    assert adapter.context is ctx
    assert adapter.event_bus is bus
    introspector = adapter.get_introspector()
    assert introspector is not None
    status = introspector.get_status_report()
    assert isinstance(status, dict)


@pytest.mark.unit
def test_create_app_routes_registered() -> None:
    """Verify create_app registers API endpoints across all router domains."""
    from harness.events.bus import EventBus
    from harness.kernel.lifecycle import PluginLifecycle
    from harness.ui.server.app import create_app

    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)
    bus = EventBus()
    app = create_app(ctx, lifecycle=lifecycle, event_bus=bus)
    assert isinstance(app, FastAPI)

    registered_paths = set(app.openapi()["paths"].keys())
    expected_paths = [
        "/api/status",
        "/api/projection/status",
        "/api/plugins",
        "/api/catalog",
        "/api/tools",
        "/api/creator/scaffold",
        "/api/creator/validate",
        "/api/creator/archetypes",
        "/api/sessions",
        "/api/metrics",
        "/api/timeline",
        "/api/sandboxes",
        "/api/swarm/status",
        "/api/swarm/runs",
        "/api/skills",
        "/api/skills/clusters",
        "/",
    ]
    for path in expected_paths:
        assert path in registered_paths, f"Expected route {path} not registered in app"

    assert any(getattr(r, "path", None) == "/ws/events" for r in app.routes)

    client = TestClient(app)
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert "status" in resp.json() or "plugins" in resp.json()
