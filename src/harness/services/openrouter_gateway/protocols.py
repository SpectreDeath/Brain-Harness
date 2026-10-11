"""Typed protocols and ServiceKey definitions for the OpenRouter Gateway service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.openrouter_gateway.models import (
    ModelMessage,
    OpenRouterChatResponse,
    OpenRouterModelInfo,
    ReasoningConfig,
    RouteResolution,
)

if TYPE_CHECKING:
    from harness.services.openrouter_gateway.service import OpenRouterGatewayService


@runtime_checkable
class OpenRouterGatewayServiceProtocol(Protocol):
    """Protocol defining the OpenRouter Gateway Service interface."""

    @property
    def base_url(self) -> str:
        ...

    def format_context_epoch(
        self,
        baseline_system_prompt: str,
        messages: list[dict[str, Any]],
        mid_conversation_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        ...

    async def chat(
        self,
        messages: list[dict[str, Any]] | list[ModelMessage],
        model: str | None = None,
        reasoning: dict[str, Any] | ReasoningConfig | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        order: list[str] | None = None,
        allow_fallbacks: bool = True,
        api_key: str | None = None,
        task_id: str | None = None,
        feature: str | None = None,
    ) -> OpenRouterChatResponse:
        ...

    async def list_models(
        self,
        provider: str | None = None,
        modality: str | None = None,
        max_price: float | None = None,
        api_key: str | None = None,
        force_refresh: bool = False,
    ) -> list[OpenRouterModelInfo]:
        ...

    async def resolve_route(
        self,
        task_type: str,
        tier: str = "medium",
        budget: str = "standard",
    ) -> RouteResolution:
        ...

    async def jsonrpc_dispatch(
        self,
        payload: dict[str, Any],
        api_key: str | None = None,
    ) -> dict[str, Any]:
        ...


OPENROUTER_GATEWAY_KEY = ServiceKey[Any]("service.openrouter_gateway")
