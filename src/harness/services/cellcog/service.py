"""CellCog Multimodal Sub-Agent Service implementation."""

from __future__ import annotations

import os
from typing import Any, Sequence

import structlog

from harness.services.cellcog.catalog import CELLCOG_CATALOG
from harness.services.cellcog.client import create_cellcog_client, emit_cellcog_telemetry
from harness.services.cellcog.execution import execute_cellcog_research, execute_cellcog_task
from harness.services.cellcog.models import (
    DEFAULT_AGENT_PROVIDER,
    DEFAULT_CHAT_MODE,
    DEFAULT_CHAT_TIER,
    DEFAULT_RESEARCH_TIMEOUT_SEC,
    DEFAULT_TIMEOUT_SEC,
    ENV_CELLCOG_API_KEY,
    CellCogCapabilitiesResult,
    CellCogResearchResult,
    CellCogRunResult,
)

logger = structlog.get_logger(__name__)


class CellCogService:
    """Service interface for interacting with CellCog any-to-any sub-agent runtime."""

    def __init__(
        self,
        api_key: str | None = None,
        agent_provider: str = DEFAULT_AGENT_PROVIDER,
        event_bus: Any = None,
    ) -> None:
        self.api_key = api_key or os.getenv(ENV_CELLCOG_API_KEY)
        self.agent_provider = agent_provider
        self.event_bus = event_bus
        self._client: Any = None

    def is_configured(self) -> bool:
        """Return True if an API key is available."""
        return bool(self.api_key)

    def _get_or_create_client(self) -> Any:
        """Instantiate or return the underlying CellCogClient."""
        if self._client is not None:
            return self._client
        self._client = create_cellcog_client(self.api_key, self.agent_provider)
        return self._client

    async def _emit_telemetry(self, event_type_name: str, payload: dict[str, Any]) -> None:
        """Emit telemetry event if EventBus is available."""
        await emit_cellcog_telemetry(self.event_bus, event_type_name, payload)

    async def execute(
        self,
        prompt: str,
        chat_mode: str = DEFAULT_CHAT_MODE,
        chat_tier: str = DEFAULT_CHAT_TIER,
        timeout: int = DEFAULT_TIMEOUT_SEC,
        task_label: str = "task",
        check_disk: bool = False,
    ) -> CellCogRunResult:
        """Execute an any-to-any multimodal task via CellCog."""
        client = self._get_or_create_client() if self.is_configured() else None
        return await execute_cellcog_task(
            client=client,
            is_configured=self.is_configured(),
            prompt=prompt,
            chat_mode=chat_mode,
            chat_tier=chat_tier,
            timeout=timeout,
            task_label=task_label,
            check_disk=check_disk,
            emit_telemetry=self._emit_telemetry,
        )

    async def research(
        self,
        topic: str,
        attachments: Sequence[str] | None = None,
        chat_tier: str = DEFAULT_CHAT_TIER,
        timeout: int = DEFAULT_RESEARCH_TIMEOUT_SEC,
    ) -> CellCogResearchResult:
        """Execute deep multi-source research via CellCog team mode."""
        return await execute_cellcog_research(
            execute_fn=self.execute,
            topic=topic,
            attachments=attachments,
            chat_tier=chat_tier,
            timeout=timeout,
        )

    def list_capabilities(self) -> CellCogCapabilitiesResult:
        """Return the comprehensive static catalog of CellCog capabilities."""
        categories = tuple(sorted({item.category for item in CELLCOG_CATALOG}))
        return CellCogCapabilitiesResult(
            total_capabilities=len(CELLCOG_CATALOG),
            categories=categories,
            capabilities=CELLCOG_CATALOG,
        )
