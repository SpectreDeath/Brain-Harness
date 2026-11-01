"""REA Reverse-Engineering Toolkit endpoints for Control Dashboard."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import structlog

from harness.services.rea_toolkit import (
    ARTIFACT_KIND_TOOLS,
    StandardReaToolkitService,
    resolve_rea_toolkit,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


class InspectRequest(BaseModel):
    target_path: str
    artifact_type: str | None = None


@router.get("/api/rea/providers")
async def get_rea_providers_endpoint(request: Request) -> dict[str, Any]:
    """Report external reverse-engineering binary availability, paths, and versions."""
    adapter = getattr(request.app.state, "adapter", None)
    ctx = adapter.context if adapter else None
    service = resolve_rea_toolkit(ctx)
    prov_map = service.providers()
    return {
        "status": "ok",
        "providers": {k: v.to_dict() for k, v in prov_map.items()},
    }


@router.get("/api/rea/tools")
async def get_rea_tools_endpoint(artifact_type: str | None = None) -> dict[str, Any]:
    """List REA tools grouped by artifact kind."""
    filter_kind = artifact_type.lower() if artifact_type else None
    matched = {k: v for k, v in ARTIFACT_KIND_TOOLS.items() if not filter_kind or k == filter_kind}
    return {
        "status": "ok",
        "tools_by_kind": matched,
        "total_aliases": 28,
    }


@router.post("/api/rea/inspect")
async def inspect_artifact_endpoint(payload: InspectRequest, request: Request) -> dict[str, Any]:
    """Inspect and dissect an artifact into a DissectionEnvelope."""
    adapter = getattr(request.app.state, "adapter", None)
    ctx = adapter.context if adapter else None
    service = resolve_rea_toolkit(ctx)
    try:
        envelope = service.dissect(payload.target_path, artifact_type=payload.artifact_type)
        return {
            "status": "ok",
            "envelope": envelope.to_dict(),
        }
    except Exception as exc:
        logger.warning("rea_inspect_endpoint_failed", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))

