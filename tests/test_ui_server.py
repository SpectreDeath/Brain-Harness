"""Tests for FastAPI UI server endpoints and WebSocket broadcaster."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.services.tools import ToolRegistryPlugin
from harness.ui.server import create_app


@pytest.mark.unit
@pytest.mark.asyncio
class TestUIServer:
    async def test_ui_rest_endpoints(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        tools_plugin = ToolRegistryPlugin()
        lifecycle.discover(tools_plugin)
        await lifecycle.load(tools_plugin.name)
        await lifecycle.validate(tools_plugin.name)
        await lifecycle.enable(tools_plugin.name)

        # Emit an event
        await bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED))

        app = create_app(ctx, lifecycle, bus)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Root dashboard HTML
            root_res = await client.get("/")
            assert root_res.status_code == 200
            assert "Harness" in root_res.text

            # 2. Status API
            status_res = await client.get("/api/status")
            assert status_res.status_code == 200
            data = status_res.json()
            assert data["plugins_count"] == 1
            assert "tools.registry" in data["plugins"]

            # 3. Plugins API
            plugins_res = await client.get("/api/plugins")
            assert plugins_res.status_code == 200
            assert "tools.registry" in plugins_res.json()["plugins"]

            # 4. Events API
            events_res = await client.get("/api/events")
            assert events_res.status_code == 200
            assert len(events_res.json()) >= 1

            # 5. Graph API
            graph_res = await client.get("/api/graph")
            assert graph_res.status_code == 200
            assert "graph TD" in graph_res.json()["mermaid"]

            # 6. Catalog API
            catalog_res = await client.get("/api/catalog")
            assert catalog_res.status_code == 200
            assert "catalog" in catalog_res.json()
            assert "total" in catalog_res.json()

            # 7. Skills API
            skills_res = await client.get("/api/skills")
            assert skills_res.status_code == 200
            assert "indexed_skills" in skills_res.json()

            route_res = await client.get("/api/skills/route?intent=test+task")
            assert route_res.status_code == 200
            assert "matches" in route_res.json()

            chain_res = await client.get("/api/skills/chain?start=s1&target=s2")
            assert chain_res.status_code == 200
            assert "chain" in chain_res.json()

    async def test_ui_without_event_bus(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        app = create_app(ctx, lifecycle, event_bus=None)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            events_res = await client.get("/api/events")
            assert events_res.status_code == 200
            assert events_res.json() == []

    async def test_ui_plugin_ingest_and_upload(self, tmp_path) -> None:
        import io
        import json
        import zipfile
        from harness.kernel.runtime import HarnessRuntime

        # Create a mock zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr(
                "uploaded_plug/plugin.json",
                json.dumps({
                    "name": "uploaded_plug",
                    "version": "2.0.0",
                    "entrypoint": "main.py",
                    "entrypoints": [{"name": "action", "description": "Run action"}],
                }),
            )
            zf.writestr("uploaded_plug/main.py", "def action(): return 'success'")
        zip_bytes = zip_buffer.getvalue()

        async with HarnessRuntime.create(db_path=":memory:", plugin_dirs=[tmp_path / "plugins"]) as runtime:
            app = create_app(runtime)
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # 1. Test POST /api/plugins/upload
                upload_res = await client.post(
                    "/api/plugins/upload",
                    files={"file": ("uploaded_plug.zip", zip_bytes, "application/zip")},
                )
                assert upload_res.status_code == 200
                upload_data = upload_res.json()
                assert upload_data["status"] == "ok"
                assert upload_data["plugin"]["name"] == "uploaded_plug"

                # 2. Test status shows new plugin
                status_res = await client.get("/api/status")
                assert "uploaded_plug" in status_res.json()["plugins"]

                # 3. Test POST /api/plugins/ingest with local directory
                local_dir = tmp_path / "ingested_local"
                local_dir.mkdir()
                (local_dir / "plugin.json").write_text(
                    json.dumps({
                        "name": "ingested_local",
                        "version": "1.0.0",
                        "entrypoint": "main.py",
                        "entrypoints": [{"name": "compute", "description": "Compute math"}],
                    })
                )
                (local_dir / "main.py").write_text("def compute(): return 42")

                ingest_res = await client.post(
                    "/api/plugins/ingest",
                    json={"source": str(local_dir)},
                )
                assert ingest_res.status_code == 200
                ingest_data = ingest_res.json()
                assert ingest_data["status"] == "ok"
                assert ingest_data["plugin"]["name"] == "ingested_local"

                # 4. Test GET /api/tools
                tools_res = await client.get("/api/tools")
                assert tools_res.status_code == 200
                tools_data = tools_res.json()["tools"]
                assert len(tools_data) > 0
                sample_tool_name = tools_data[0]["name"]

                # 5. Test POST /api/tools/toggle (disable)
                toggle_res = await client.post(
                    "/api/tools/toggle",
                    json={"name": sample_tool_name, "enabled": False},
                )
                assert toggle_res.status_code == 200
                assert toggle_res.json()["enabled"] is False

                # 6. Test POST /api/plugins/disable-all
                disable_all_res = await client.post("/api/plugins/disable-all")
                assert disable_all_res.status_code == 200
                assert "disabled" in disable_all_res.json()

                # 7. Test POST /api/plugins/enable-all
                enable_all_res = await client.post("/api/plugins/enable-all")
                assert enable_all_res.status_code == 200
                assert enable_all_res.json()["status"] == "ok"

                # 8. Test GET /api/plugins/{name}/guide
                guide_res = await client.get("/api/plugins/tools.registry/guide")
                assert guide_res.status_code == 200
                guide_data = guide_res.json()
                assert guide_data["status"] == "ok"
                assert "card" in guide_data
                assert "guide" in guide_data

                # 9. Test POST /api/creator/scaffold
                scaffold_target = tmp_path / "plugins" / "ui_scaffolded"
                scaffold_res = await client.post(
                    "/api/creator/scaffold",
                    json={
                        "name": "ui_scaffolded",
                        "description": "Scaffolded via API",
                        "language": "python",
                        "tools": ["api_exec"],
                        "target_dir": str(scaffold_target),
                        "auto_enable": True,
                    },
                )
                assert scaffold_res.status_code == 200
                scaffold_data = scaffold_res.json()
                assert scaffold_data["status"] == "ok"
                assert scaffold_data["plugin"]["name"] == "ui_scaffolded"

                # 10. Test POST /api/creator/validate
                validate_res = await client.post(
                    "/api/creator/validate",
                    json={"path": str(scaffold_target), "dry_run": True},
                )
                assert validate_res.status_code == 200
                validate_data = validate_res.json()
                assert validate_data["status"] == "ok"
                assert validate_data["report"]["valid"] is True
