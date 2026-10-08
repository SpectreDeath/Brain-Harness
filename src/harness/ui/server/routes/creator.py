"""Plugin creator, scaffolding, and validation endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
import structlog

from harness.ui.server.models import (
    CreatorScaffoldRequest,
    CreatorValidateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/api/creator/scaffold")
async def scaffold_plugin_api(req: CreatorScaffoldRequest, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    projection_engine = request.app.state.projection_engine
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

        if adapter.event_bus is not None and projection_engine is not None:
            await projection_engine.broadcast(
                channel="system",
                message={
                    "type": "plugin_scaffolded",
                    "data": plugin_data,
                },
            )

        return {"status": "ok", "plugin": plugin_data}
    except Exception as e:
        logger.error("Failed to scaffold plugin from UI", name=req.name, error=str(e))
        return {"status": "error", "error": str(e)}


@router.post("/api/creator/validate")
async def validate_plugin_api(req: CreatorValidateRequest, request: Request) -> dict[str, Any]:
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


@router.get("/api/creator/archetypes")
async def get_creator_archetypes_api(request: Request) -> dict[str, Any]:
    from harness.creator.creator import PluginCreator

    archetypes = PluginCreator.list_archetypes()
    return {"archetypes": archetypes, "total": len(archetypes)}


__all__ = ["router"]
