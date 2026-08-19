"""FastAPI web server with real-time WebSocket event streaming and REST API.

Provides:
    - Real-time event log broadcast over WebSocket (/ws/events)
    - Plugin management REST endpoints (/api/plugins)
    - Autonomous agent task invocation endpoint (/api/agent/run)
    - Live Mermaid dependency graph (/api/graph)
    - Embedded Single-Page Control Dashboard (/)
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from harness.agent.base import AGENT_LOOP_KEY
from harness.creator.dynamic import RuntimeIntrospector
from harness.events.bus import EventBus
from harness.events.types import HarnessEvent
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.base import HarnessPlugin
from harness.services.tools import TOOL_REGISTRY_KEY

logger = structlog.get_logger()


class TaskRequest(BaseModel):
    task: str
    max_steps: int = 10


class PluginToggleRequest(BaseModel):
    name: str
    action: str  # "enable" or "disable"


class ToolToggleRequest(BaseModel):
    name: str
    enabled: bool | None = None


class PluginIngestRequest(BaseModel):
    source: str
    ref: str = "main"
    force: bool = False


class CreatorScaffoldRequest(BaseModel):
    name: str
    description: str = ""
    language: str = "python"
    tools: list[str] = ["execute"]
    dependencies: list[str] = []
    author: str = "Harness Developer"
    category: str = "general"
    preset: str = "general"
    isolation: str = "subprocess"
    target_dir: str | None = None
    auto_enable: bool = True


class CreatorValidateRequest(BaseModel):
    path: str
    dry_run: bool = False
    timeout: float = 15.0


class ConnectionManager:
    """Manages active WebSocket connections for event broadcasting."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        text = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(text)
            except Exception:
                self.disconnect(connection)


class RuntimeAdapter:
    """Authoritative adapter normalizing access between unified HarnessRuntime and standalone kernel components."""

    def __init__(
        self,
        context_or_runtime: ServiceContext | HarnessRuntime,
        lifecycle: PluginLifecycle | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        if isinstance(context_or_runtime, HarnessRuntime):
            self._runtime: HarnessRuntime | None = context_or_runtime
            self.context: ServiceContext = context_or_runtime.context
            self.lifecycle: PluginLifecycle = context_or_runtime.lifecycle
            self.event_bus: EventBus | None = context_or_runtime.event_bus
        else:
            self._runtime = None
            self.context = context_or_runtime
            if lifecycle is None:
                raise ValueError("lifecycle is required when context is passed")
            self.lifecycle = lifecycle
            self.event_bus = event_bus

    @property
    def is_unified_runtime(self) -> bool:
        return self._runtime is not None

    async def enable_all(self) -> dict[str, bool]:
        """Enable all discovered plugins."""
        if self._runtime is not None:
            return await self._runtime.enable_all_plugins()

        for name, entry in list(self.lifecycle.plugins.items()):
            if entry.state == PluginState.DISCOVERED:
                try:
                    await self.lifecycle.load(name)
                    await self.lifecycle.validate(name)
                except Exception as e:
                    logger.warning("Failed loading plugin before enable_all", plugin=name, error=str(e))
        return await self.lifecycle.enable_all()

    async def disable_all(self, *, keep_core: bool = True) -> list[str]:
        """Disable all active plugins with optional core service retention."""
        if self._runtime is not None:
            return await self._runtime.disable_all_plugins(keep_core=keep_core)

        core_plugins = {"tools.registry", "storage.sqlite", "llm.provider"} if keep_core else set()
        disabled: list[str] = []
        for name, entry in list(self.lifecycle.plugins.items()):
            if entry.state == PluginState.ENABLED and name not in core_plugins:
                await self.lifecycle.disable(name)
                disabled.append(name)
        return disabled

    async def add_plugin_from_source(
        self,
        source: str | Path,
        *,
        ref: str = "main",
        force: bool = False,
        auto_enable: bool = True,
    ) -> HarnessPlugin:
        """Ingest and register a plugin from source."""
        if self._runtime is not None:
            return await self._runtime.add_plugin_from_source(
                source, ref=ref, force=force, auto_enable=auto_enable
            )

        pipeline = PluginIngestionPipeline()
        plugin = await pipeline.ingest(str(source), ref=ref, force=force)
        if auto_enable:
            await self.lifecycle.register_and_enable(plugin)
        else:
            self.lifecycle.discover(plugin)
        return plugin

    async def run_agent(self, task: str, max_steps: int = 10) -> Any:
        """Execute an autonomous agent task."""
        if self._runtime is not None:
            return await self._runtime.run_task(task, max_steps=max_steps)

        agent_loop = self.context.optional(AGENT_LOOP_KEY)
        if not agent_loop:
            raise RuntimeError("No active agent.loop service found")
        return await agent_loop.run_task(task, max_steps=max_steps)

    def get_introspector(self) -> RuntimeIntrospector:
        """Return an authoritative RuntimeIntrospector instance."""
        tools = self.context.optional(TOOL_REGISTRY_KEY)
        return RuntimeIntrospector(self.context, self.lifecycle, tools)

    def get_catalog(self) -> list[dict[str, Any]]:
        """Return enriched catalog report."""
        loader = getattr(self._runtime, "loader", None) if self._runtime else None
        return self.get_introspector().get_catalog_report(loader=loader)

    def get_plugin_guide(self, name: str) -> dict[str, Any]:
        """Return structured guide and manifest card for a plugin."""
        loader = getattr(self._runtime, "loader", None) if self._runtime else None
        return self.get_introspector().get_plugin_guide_report(name, loader=loader)

    def get_sandboxes(self) -> list[dict[str, Any]]:
        """Return runtime sandbox states across all registered plugins."""
        return self.get_introspector().get_sandboxes_report()


def create_app(
    context_or_runtime: ServiceContext | HarnessRuntime,
    lifecycle: PluginLifecycle | None = None,
    event_bus: EventBus | None = None,
) -> FastAPI:
    """Create and configure the FastAPI web application.

    Supports either a unified HarnessRuntime or individual kernel instances.
    """
    adapter = RuntimeAdapter(
        context_or_runtime=context_or_runtime,
        lifecycle=lifecycle,
        event_bus=event_bus,
    )

    app = FastAPI(title="Harness Control Dashboard", version="0.1.0")
    manager = ConnectionManager()

    # Hook event bus to broadcast to WebSocket clients
    if adapter.event_bus is not None:
        async def ws_event_handler(event: HarnessEvent) -> None:
            await manager.broadcast({
                "type": "event",
                "data": event.to_dict(),
            })

        adapter.event_bus.on_all(ws_event_handler)

    @app.get("/api/status")
    async def get_status() -> dict[str, Any]:
        return adapter.get_introspector().get_status_report()

    @app.get("/api/plugins")
    async def get_plugins() -> dict[str, Any]:
        return {"plugins": adapter.lifecycle.summary()}

    @app.get("/api/catalog")
    async def get_catalog_api() -> dict[str, Any]:
        catalog = adapter.get_catalog()
        return {"catalog": catalog, "total": len(catalog)}

    @app.get("/api/plugins/{name}/guide")
    async def get_plugin_guide_api(name: str) -> dict[str, Any]:
        return adapter.get_plugin_guide(name)


    @app.post("/api/plugins/enable-all")
    async def enable_all_plugins() -> dict[str, Any]:
        try:
            results = await adapter.enable_all()
            return {"status": "ok", "results": results}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.post("/api/plugins/disable-all")
    async def disable_all_plugins() -> dict[str, Any]:
        try:
            disabled = await adapter.disable_all(keep_core=True)
            return {"status": "ok", "disabled": disabled}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.get("/api/tools")
    async def get_tools(provider: str | None = None, enabled_only: bool = False) -> dict[str, Any]:
        tools_registry = adapter.context.optional(TOOL_REGISTRY_KEY)
        if not tools_registry:
            return {"tools": []}
        return {"tools": tools_registry.to_catalog(enabled_only=enabled_only, provider=provider)}

    @app.post("/api/tools/toggle")
    async def toggle_tool(req: ToolToggleRequest) -> dict[str, Any]:
        tools_registry = adapter.context.optional(TOOL_REGISTRY_KEY)
        if not tools_registry:
            return {"status": "error", "error": "No tools registry found"}
        success = tools_registry.toggle_tool(req.name, enabled=req.enabled)
        if success:
            is_enabled = tools_registry.is_tool_enabled(req.name)
            return {"status": "ok", "name": req.name, "enabled": is_enabled}
        return {"status": "error", "error": f"Tool '{req.name}' not found"}

    @app.post("/api/plugins/toggle")
    async def toggle_plugin(req: PluginToggleRequest) -> dict[str, Any]:
        try:
            if req.action == "enable":
                await adapter.lifecycle.enable(req.name)
            elif req.action == "disable":
                await adapter.lifecycle.disable(req.name)
            else:
                return {"status": "error", "error": f"Invalid action: {req.action}"}
            return {"status": "ok", "state": adapter.lifecycle.get_state(req.name).value}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.post("/api/plugins/ingest")
    async def ingest_plugin(req: PluginIngestRequest) -> dict[str, Any]:
        try:
            plugin = await adapter.add_plugin_from_source(
                req.source, ref=req.ref, force=req.force, auto_enable=True
            )

            manifest = getattr(plugin, "manifest", None)
            plugin_data = {
                "name": plugin.name,
                "version": getattr(plugin, "version", "0.1.0"),
                "state": adapter.lifecycle.get_state(plugin.name).value,
                "entrypoints": len(manifest.entrypoints) if manifest else 0,
            }

            if adapter.event_bus is not None:
                await manager.broadcast({
                    "type": "plugin_ingested",
                    "data": plugin_data,
                })

            return {"status": "ok", "plugin": plugin_data}
        except Exception as e:
            logger.error("Failed to ingest plugin from UI", source=req.source, error=str(e))
            return {"status": "error", "error": str(e)}

    @app.post("/api/plugins/upload")
    async def upload_plugin(file: UploadFile = File(...)) -> dict[str, Any]:
        if not file.filename or not file.filename.lower().endswith(".zip"):
            return {"status": "error", "error": "Only .zip archive uploads are supported"}

        try:
            temp_dir = Path(tempfile.gettempdir()) / "harness_uploads"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / file.filename

            with open(temp_file, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            plugin = await adapter.add_plugin_from_source(temp_file, auto_enable=True)

            manifest = getattr(plugin, "manifest", None)
            plugin_data = {
                "name": plugin.name,
                "version": getattr(plugin, "version", "0.1.0"),
                "state": adapter.lifecycle.get_state(plugin.name).value,
                "entrypoints": len(manifest.entrypoints) if manifest else 0,
            }

            if adapter.event_bus is not None:
                await manager.broadcast({
                    "type": "plugin_ingested",
                    "data": plugin_data,
                })

            return {"status": "ok", "plugin": plugin_data}
        except Exception as e:
            logger.error("Failed to upload plugin from UI", filename=file.filename, error=str(e))
            return {"status": "error", "error": str(e)}

    @app.post("/api/creator/scaffold")
    async def scaffold_plugin_api(req: CreatorScaffoldRequest) -> dict[str, Any]:
        try:
            from harness.creator.creator import PluginCreator
            from harness.creator.scaffold import ScaffoldOptions
            from harness.plugins.manifest import IsolationMode

            out_dir = Path(req.target_dir) if req.target_dir else Path("plugins") / req.name
            options = ScaffoldOptions(
                name=req.name,
                description=req.description,
                language=req.language.lower(),
                tools=req.tools,
                dependencies=req.dependencies,
                author=req.author,
                category=req.category,
                preset=req.preset.lower(),
                isolation=IsolationMode(req.isolation.lower()),
            )

            if req.auto_enable:
                scaffold_res, plugin = await PluginCreator.scaffold_and_mount(
                    adapter, out_dir, options=options, auto_enable=True
                )
                plugin_state = adapter.lifecycle.get_state(plugin.name).value
            else:
                scaffold_res = await PluginCreator.scaffold_async(out_dir, options=options)
                plugin_state = "unloaded"

            plugin_data = {
                "name": req.name,
                "path": str(scaffold_res.path),
                "language": req.language,
                "preset": req.preset,
                "tools": req.tools,
                "state": plugin_state,
            }

            if adapter.event_bus is not None:
                await manager.broadcast({
                    "type": "plugin_scaffolded",
                    "data": plugin_data,
                })

            return {"status": "ok", "plugin": plugin_data}
        except Exception as e:
            logger.error("Failed to scaffold plugin from UI", name=req.name, error=str(e))
            return {"status": "error", "error": str(e)}

    @app.post("/api/creator/validate")
    async def validate_plugin_api(req: CreatorValidateRequest) -> dict[str, Any]:
        try:
            from harness.creator.creator import PluginCreator

            report = await PluginCreator.validate(req.path, dry_run=req.dry_run, timeout=req.timeout)
            return {
                "status": "ok" if report.valid else "error",
                "report": report.to_dict(),
            }
        except Exception as e:
            logger.error("Failed to validate plugin from UI", path=req.path, error=str(e))
            return {"status": "error", "error": str(e)}

    @app.get("/api/creator/archetypes")
    async def get_creator_archetypes_api() -> dict[str, Any]:
        from harness.creator.creator import PluginCreator

        archetypes = PluginCreator.list_archetypes()
        return {"archetypes": archetypes, "total": len(archetypes)}

    @app.post("/api/agent/run")
    async def run_agent(req: TaskRequest) -> dict[str, Any]:
        try:
            result = await adapter.run_agent(req.task, max_steps=req.max_steps)
            return {
                "status": "ok",
                "task": result.task,
                "task_status": result.status,
                "final_answer": result.final_answer,
                "steps_count": len(result.steps),
                "session_id": getattr(result, "session_id", None),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.get("/api/sessions")
    async def get_sessions(status: str | None = None, limit: int = 50) -> dict[str, Any]:
        from harness.agent.session import AGENT_SESSION_MANAGER_KEY

        sess_mgr = adapter.context.optional(AGENT_SESSION_MANAGER_KEY)
        if sess_mgr is None:
            return {"sessions": [], "total": 0}
        sessions = await sess_mgr.list_sessions(status=status, limit=limit)
        return {
            "sessions": [s.to_dict() for s in sessions],
            "total": len(sessions),
        }

    @app.get("/api/sessions/{session_id}")
    async def get_session_details(session_id: str) -> dict[str, Any]:
        from harness.agent.session import AGENT_SESSION_MANAGER_KEY

        sess_mgr = adapter.context.optional(AGENT_SESSION_MANAGER_KEY)
        if sess_mgr is None:
            return {"status": "error", "error": "No session manager available"}
        session = await sess_mgr.get_session(session_id)
        if session is None:
            return {"status": "error", "error": f"Session '{session_id}' not found"}
        return {"status": "ok", "session": session.to_dict()}

    @app.get("/api/sessions/{session_id}/export")
    async def export_session_endpoint(session_id: str, format: str = "json") -> dict[str, Any]:
        from harness.agent.session import AGENT_SESSION_MANAGER_KEY

        sess_mgr = adapter.context.optional(AGENT_SESSION_MANAGER_KEY)
        if sess_mgr is None:
            return {"status": "error", "error": "No session manager available"}
        try:
            content = await sess_mgr.export_session(session_id, format=format)
            return {"status": "ok", "session_id": session_id, "format": format, "content": content}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.get("/api/graph")
    async def get_graph() -> dict[str, str]:
        return {"mermaid": adapter.get_introspector().generate_mermaid_graph()}

    @app.get("/api/events")
    async def get_events(limit: int = 50) -> list[dict[str, Any]]:
        if adapter.event_bus is None:
            return []
        return [e.to_dict() for e in adapter.event_bus.log[-limit:]]

    @app.get("/api/metrics")
    async def get_metrics() -> dict[str, Any]:
        if adapter.event_bus is None:
            return {
                "total_events": 0,
                "event_counts_by_type": {},
                "tool_invocations": {},
                "tool_results": {},
                "tool_errors": {},
                "total_tokens": 0,
                "llm_calls": 0,
            }
        from harness.events.bus import MetricsProjection

        projection = MetricsProjection()
        for event in adapter.event_bus.log:
            projection.handle(event)
        return projection.get_state()

    @app.get("/api/timeline")
    async def get_timeline(
        from_time: str | None = None,
        to_time: str | None = None,
        event_type: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        if adapter.event_bus is None:
            return {"events": [], "total": 0, "summary": {}}

        events: list[dict[str, Any]] = []
        counts_by_type: dict[str, int] = {}
        error_count = 0

        for event in adapter.event_bus.log:
            ts_str = event.timestamp.isoformat() if hasattr(event.timestamp, "isoformat") else str(event.timestamp)
            if from_time and ts_str < from_time:
                continue
            if to_time and ts_str > to_time:
                continue
            etype = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
            if event_type and etype != event_type and event_type != "*":
                continue
            if source and event.source != source:
                continue

            counts_by_type[etype] = counts_by_type.get(etype, 0) + 1
            if "error" in etype.lower() or "error" in event.source.lower():
                error_count += 1

            events.append(event.to_dict())

        if limit > 0 and len(events) > limit:
            events = events[-limit:]

        return {
            "events": events,
            "total": len(events),
            "summary": {
                "counts_by_type": counts_by_type,
                "error_count": error_count,
                "first_timestamp": events[0]["timestamp"] if events else None,
                "last_timestamp": events[-1]["timestamp"] if events else None,
            },
        }

    @app.get("/api/sandboxes")
    async def get_sandboxes() -> dict[str, Any]:
        sandboxes = adapter.get_sandboxes()
        return {"sandboxes": sandboxes, "total": len(sandboxes)}


    @app.get("/api/swarm/status")
    async def get_swarm_status() -> dict[str, Any]:
        from harness.kernel.context import ServiceKey

        swarm_key: ServiceKey[Any] = ServiceKey("agent.swarm")
        swarm_coord = adapter.context.optional(swarm_key)
        if swarm_coord is not None and hasattr(swarm_coord, "get_status"):
            return await swarm_coord.get_status()

        return {
            "status": "ready",
            "active_swarms": 0,
            "coordinator_available": swarm_coord is not None,
        }

    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        try:
            while True:
                data_text = await websocket.receive_text()
                try:
                    msg = json.loads(data_text)
                    if msg.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "time": str(datetime.now(timezone.utc))}))
                except Exception:
                    pass
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    # Static HTML frontend
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"

    @app.get("/", response_class=HTMLResponse)
    async def root() -> str:
        if index_file.exists():
            return index_file.read_text(encoding="utf-8")
        return "<h1>Harness Dashboard</h1><p>Static index.html not found.</p>"

    return app
