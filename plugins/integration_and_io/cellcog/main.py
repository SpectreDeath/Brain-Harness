"""CellCog Multimodal Sub-Agent Plugin for Brain Harness."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any, Coroutine, Sequence, TypeVar
import structlog

from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.cellcog import (
    CELLCOG_CATALOG,
    CELLCOG_SERVICE_KEY,
    CellCogArtifact,
    CellCogCapabilitiesResult,
    CellCogResearchResult,
    CellCogRunResult,
    CellCogService,
    MultimodalCompilationResult,
    MultimodalProtocolCompiler,
    parse_generate_file_tags,
    parse_show_file_tags,
)

logger = structlog.get_logger(__name__)

# Global default service singleton
_global_service = CellCogService()

T = TypeVar("T")


def _run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Execute an async coroutine safely across event loops or sync execution threads."""
    try:
        asyncio.get_running_loop()
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)


class CellCogPlugin(HarnessPlugin):
    """Brain Harness plugin for CellCog any-to-any sub-agent delegation."""

    # External SDK plugin runs in subprocess sandbox by default per AGENTS.md Rule 5
    trusted = False

    def __init__(self, service: CellCogService | None = None) -> None:
        self.service = service or _global_service

    @property
    def name(self) -> str:
        return "plugin.cellcog"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Any-to-any multimodal sub-agent delegation via CellCog SDK — research, media, documents, code"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CELLCOG_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        """Register the CellCog service in the IoC container and link EventBus if available."""
        event_bus = ctx.event_bus or (ctx.require(EVENT_BUS_KEY) if ctx.has(EVENT_BUS_KEY) else None)
        if event_bus is not None:
            self.service.event_bus = event_bus
            logger.info("cellcog_plugin_event_bus_linked")

        logger.info(
            "cellcog_plugin_loading",
            configured=self.service.is_configured(),
            agent_provider=self.service.agent_provider,
        )
        ctx.provide(CELLCOG_SERVICE_KEY, self.service)

    async def on_enable(self) -> None:
        """Start CellCog plugin operations."""
        logger.info("cellcog_plugin_enabled")

    async def on_disable(self) -> None:
        """Pause CellCog plugin operations."""
        logger.info("cellcog_plugin_disabled")

    async def on_unload(self) -> None:
        """Clean up CellCog plugin resources."""
        logger.info("cellcog_plugin_unloaded")


# ---------------------------------------------------------------------------
# Module-level tool entrypoints callable by ToolRegistry or Subprocess RPC
# ---------------------------------------------------------------------------

def cellcog_run(
    prompt: str,
    chat_mode: str = "agent",
    chat_tier: str = "flash",
    timeout: int = 1800,
    task_label: str = "task",
) -> dict[str, Any]:
    """Execute an any-to-any multimodal task via CellCog."""
    res = _run_async(
        _global_service.execute(
            prompt=prompt,
            chat_mode=chat_mode,
            chat_tier=chat_tier,
            timeout=timeout,
            task_label=task_label,
        )
    )
    return {
        "success": res.success,
        "message": res.message,
        "chat_id": res.chat_id,
        "chat_mode": res.chat_mode,
        "chat_tier": res.chat_tier,
        "attached_files": list(res.attached_files),
        "generated_files": list(res.generated_files),
        "downloaded_files": list(res.downloaded_files),
        "artifacts": [
            {
                "path": art.path,
                "filename": art.filename,
                "mime_type": art.mime_type,
                "size_bytes": art.size_bytes,
                "checksum_sha256": art.checksum_sha256,
            }
            for art in res.artifacts
        ],
        "error": res.error,
    }


def cellcog_research(
    topic: str,
    attachments: list[str] | None = None,
    chat_tier: str = "flash",
    timeout: int = 3600,
) -> dict[str, Any]:
    """Execute deep multi-source research via CellCog team mode."""
    res = _run_async(
        _global_service.research(
            topic=topic,
            attachments=attachments,
            chat_tier=chat_tier,
            timeout=timeout,
        )
    )
    return {
        "success": res.success,
        "summary": res.summary,
        "sources_count": res.sources_count,
        "chat_id": res.chat_id,
        "chat_tier": res.chat_tier,
        "attached_files": list(res.attached_files),
        "generated_files": list(res.generated_files),
        "artifacts": [
            {
                "path": art.path,
                "filename": art.filename,
                "mime_type": art.mime_type,
                "size_bytes": art.size_bytes,
                "checksum_sha256": art.checksum_sha256,
            }
            for art in res.artifacts
        ],
        "findings": list(res.findings),
        "error": res.error,
    }


def cellcog_list_capabilities() -> dict[str, Any]:
    """List available CellCog modality capabilities and their categories."""
    catalog = _global_service.list_capabilities()
    return {
        "total_capabilities": catalog.total_capabilities,
        "categories": list(catalog.categories),
        "capabilities": [
            {
                "name": item.name,
                "category": item.category,
                "description": item.description,
                "recommended_mode": item.recommended_mode,
                "recommended_tier": item.recommended_tier,
            }
            for item in catalog.capabilities
        ],
    }
