"""Tests for UI Skill Clustering REST and Mermaid endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.services.skill_graph import SkillRegistryPlugin
from harness.ui.server import create_app


@pytest.mark.unit
@pytest.mark.asyncio
class TestUISkillClusteringSeam:
    async def test_get_skill_clusters_endpoint(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        skill_plugin = SkillRegistryPlugin()
        lifecycle.discover(skill_plugin)
        await lifecycle.load(skill_plugin.name)
        await lifecycle.validate(skill_plugin.name)
        await lifecycle.enable(skill_plugin.name)

        app = create_app(ctx, lifecycle, bus)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/skills/clusters")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ok"
            assert "clusters" in data
            assert isinstance(data["clusters"], list)
            assert data["total"] == len(data["clusters"])

            if data["clusters"]:
                first = data["clusters"][0]
                assert "cluster_id" in first
                assert "name" in first
                assert "skills" in first
                assert "cohesion_score" in first
                assert "central_hub_skill" in first

    async def test_get_skill_clusters_mermaid_endpoint(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        skill_plugin = SkillRegistryPlugin()
        lifecycle.discover(skill_plugin)
        await lifecycle.load(skill_plugin.name)
        await lifecycle.validate(skill_plugin.name)
        await lifecycle.enable(skill_plugin.name)

        app = create_app(ctx, lifecycle, bus)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/skills/clusters/mermaid")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ok"
            assert "mermaid" in data
            assert "graph TD" in data["mermaid"]
            assert "subgraph" in data["mermaid"]
