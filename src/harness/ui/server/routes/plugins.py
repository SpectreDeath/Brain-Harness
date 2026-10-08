"""Plugins and tools lifecycle management endpoints."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
from typing import Any

from fastapi import APIRouter, File, Request, UploadFile
import structlog

from harness.services.tools import TOOL_REGISTRY_KEY
from harness.ui.server.models import (
    PluginIngestRequest,
    PluginToggleRequest,
    ToolToggleRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/api/plugins")
async def get_plugins(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    return {"plugins": adapter.lifecycle.summary()}


@router.get("/api/catalog")
async def get_catalog_api(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    catalog = adapter.get_catalog()
    return {"catalog": catalog, "total": len(catalog)}


@router.get("/api/plugins/{name}/guide")
async def get_plugin_guide_api(name: str, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    return adapter.get_plugin_guide(name)


@router.post("/api/plugins/enable-all")
async def enable_all_plugins(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    try:
        results = await adapter.enable_all()
        return {"status": "ok", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/api/plugins/disable-all")
async def disable_all_plugins(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    try:
        disabled = await adapter.disable_all(keep_core=True)
        return {"status": "ok", "disabled": disabled}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/api/tools")
async def get_tools(request: Request, provider: str | None = None, enabled_only: bool = False) -> dict[str, Any]:
    adapter = request.app.state.adapter
    tools_registry = adapter.context.optional(TOOL_REGISTRY_KEY)
    if not tools_registry:
        return {"tools": []}
    return {"tools": tools_registry.to_catalog(enabled_only=enabled_only, provider=provider)}


@router.post("/api/tools/toggle")
async def toggle_tool(req: ToolToggleRequest, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    tools_registry = adapter.context.optional(TOOL_REGISTRY_KEY)
    if not tools_registry:
        return {"status": "error", "error": "No tools registry found"}
    success = tools_registry.toggle_tool(req.name, enabled=req.enabled)
    if success:
        is_enabled = tools_registry.is_tool_enabled(req.name)
        return {"status": "ok", "name": req.name, "enabled": is_enabled}
    return {"status": "error", "error": f"Tool '{req.name}' not found"}


@router.post("/api/plugins/toggle")
async def toggle_plugin(req: PluginToggleRequest, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
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


@router.post("/api/plugins/ingest")
async def ingest_plugin(req: PluginIngestRequest, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    projection_engine = request.app.state.projection_engine
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

        if adapter.event_bus is not None and projection_engine is not None:
            await projection_engine.broadcast(
                channel="system",
                message={
                    "type": "plugin_ingested",
                    "data": plugin_data,
                },
            )

        return {"status": "ok", "plugin": plugin_data}
    except Exception as e:
        logger.error("Failed to ingest plugin from UI", source=req.source, error=str(e))
        return {"status": "error", "error": str(e)}


@router.post("/api/plugins/upload")
async def upload_plugin(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
    adapter = request.app.state.adapter
    projection_engine = request.app.state.projection_engine

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

        if adapter.event_bus is not None and projection_engine is not None:
            await projection_engine.broadcast(
                channel="system",
                message={
                    "type": "plugin_ingested",
                    "data": plugin_data,
                },
            )

        return {"status": "ok", "plugin": plugin_data}
    except Exception as e:
        logger.error("Failed to upload plugin from UI", filename=file.filename, error=str(e))
        return {"status": "error", "error": str(e)}


__all__ = ["router"]
