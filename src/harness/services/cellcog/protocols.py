"""Typed protocols and ServiceKey definitions for the CellCog multimodal service."""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.cellcog.models import (
    DEFAULT_CHAT_MODE,
    DEFAULT_CHAT_TIER,
    DEFAULT_RESEARCH_TIMEOUT_SEC,
    DEFAULT_TIMEOUT_SEC,
    CellCogCapabilitiesResult,
    CellCogResearchResult,
    CellCogRunResult,
)


@runtime_checkable
class CellCogServiceProtocol(Protocol):
    """Runtime-checkable protocol defining the CellCog multimodal service contract."""

    def is_configured(self) -> bool:
        """Return True if an API key is available."""
        ...

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
        ...

    async def research(
        self,
        topic: str,
        attachments: Sequence[str] | None = None,
        chat_tier: str = DEFAULT_CHAT_TIER,
        timeout: int = DEFAULT_RESEARCH_TIMEOUT_SEC,
    ) -> CellCogResearchResult:
        """Execute deep multi-source research via CellCog team mode."""
        ...

    def list_capabilities(self) -> CellCogCapabilitiesResult:
        """Return the comprehensive static catalog of CellCog capabilities."""
        ...


CELLCOG_SERVICE_KEY: ServiceKey[Any] = ServiceKey("service.cellcog")
