"""FastAPI application factory for the Harness Control Dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.kernel.runtime import HarnessRuntime
from harness.ui.server.adapter import RuntimeAdapter
from harness.ui.server.routes.creator import router as creator_router
from harness.ui.server.routes.plugins import router as plugins_router
from harness.ui.server.routes.sessions import router as sessions_router
from harness.ui.server.routes.skills import router as skills_router
from harness.ui.server.routes.swarm import router as swarm_router


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

    from harness.ui.projection import UIProjectionEngine

    projection_engine = UIProjectionEngine(adapter=adapter, event_bus=adapter.event_bus)
    app.state.adapter = adapter
    app.state.projection_engine = projection_engine

    # Include domain routers
    app.include_router(plugins_router)
    app.include_router(creator_router)
    app.include_router(sessions_router)
    app.include_router(swarm_router)
    app.include_router(skills_router)

    # Real-time WebSocket event streaming
    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket) -> None:
        await projection_engine.connect_client(websocket)
        try:
            while True:
                data_text = await websocket.receive_text()
                await projection_engine.handle_client_message(websocket, data_text)
        except WebSocketDisconnect:
            projection_engine.disconnect_client(websocket)

    # Static frontend (Dual-mode: React dist bundle with fallback to embedded zero-build index.html)
    repo_root = Path(__file__).resolve().parents[4]
    frontend_dist = repo_root / "frontend" / "dist"
    static_dir = Path(__file__).resolve().parents[1] / "static"
    index_file = static_dir / "index.html"

    if frontend_dist.exists() and (frontend_dist / "assets").exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def root() -> str:
        if frontend_dist.exists() and (frontend_dist / "index.html").exists():
            return (frontend_dist / "index.html").read_text(encoding="utf-8")
        if index_file.exists():
            return index_file.read_text(encoding="utf-8")
        return "<h1>Harness Dashboard</h1><p>Static index.html not found.</p>"

    @app.get("/metrics")
    async def metrics_endpoint():
        from fastapi.responses import PlainTextResponse
        from harness.services.prometheus import resolve_prometheus_exporter

        ctx = adapter.context if hasattr(adapter, "context") else None
        exporter = resolve_prometheus_exporter(ctx)
        return PlainTextResponse(
            exporter.generate_text_export(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


__all__ = ["create_app"]
