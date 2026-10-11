"""OpenRouter Gateway Service coordinator implementation."""

from __future__ import annotations

import os
from typing import Any

from harness.services.openrouter_gateway.chat import execute_chat_completion
from harness.services.openrouter_gateway.client import (
    async_http_get,
    async_http_post,
    format_context_epoch_messages,
)
from harness.services.openrouter_gateway.jsonrpc import execute_jsonrpc_dispatch
from harness.services.openrouter_gateway.models import (
    DEFAULT_OPENROUTER_BASE_URL,
    ModelMessage,
    OpenRouterChatResponse,
    OpenRouterModelInfo,
    ReasoningConfig,
    RouteResolution,
)
from harness.services.openrouter_gateway.routing import resolve_model_route


class OpenRouterGatewayService:
    """Async OpenRouter gateway client, router, and JSON-RPC 2.0 protocol engine."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = "anthropic/claude-3.7-sonnet",
        organization_id: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("KILO_API_KEY")
        self._base_url = (
            base_url
            or os.getenv("OPENROUTER_BASE_URL")
            or os.getenv("KILO_OPENROUTER_BASE_URL")
            or DEFAULT_OPENROUTER_BASE_URL
        ).rstrip("/")
        self._default_model = default_model
        self._organization_id = organization_id or os.getenv("KILOCODE_ORGANIZATIONID")
        self._model_cache: list[OpenRouterModelInfo] | None = None

    @property
    def base_url(self) -> str:
        return self._base_url

    def _resolve_api_key(self, override_key: str | None = None) -> str | None:
        return override_key or self._api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("KILO_API_KEY")

    def format_context_epoch(
        self,
        baseline_system_prompt: str,
        messages: list[dict[str, Any]],
        mid_conversation_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Format messages to preserve KV-cache prefix under Kilo Context Epoch heuristics (KI-KILO-01)."""
        return format_context_epoch_messages(
            baseline_system_prompt, messages, mid_conversation_updates
        )

    async def _async_http_post(
        self,
        endpoint_path: str,
        payload: dict[str, Any],
        api_key: str | None = None,
        task_id: str | None = None,
        feature: str | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        resolved_key = self._resolve_api_key(api_key)
        return await async_http_post(
            base_url=self._base_url,
            endpoint_path=endpoint_path,
            payload=payload,
            api_key=resolved_key,
            organization_id=self._organization_id,
            task_id=task_id,
            feature=feature,
            timeout=timeout,
        )

    async def _async_http_get(
        self,
        endpoint_path: str,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        resolved_key = self._resolve_api_key(api_key)
        return await async_http_get(
            base_url=self._base_url,
            endpoint_path=endpoint_path,
            api_key=resolved_key,
            organization_id=self._organization_id,
            timeout=timeout,
        )

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
        """Execute chat completion via OpenRouter / Kilo Gateway with provider routing."""
        return await execute_chat_completion(
            post_fn=self._async_http_post,
            default_model=self._default_model,
            messages=messages,
            model=model,
            reasoning=reasoning,
            temperature=temperature,
            max_tokens=max_tokens,
            order=order,
            allow_fallbacks=allow_fallbacks,
            api_key=api_key,
            task_id=task_id,
            feature=feature,
        )

    async def list_models(
        self,
        provider: str | None = None,
        modality: str | None = None,
        max_price: float | None = None,
        api_key: str | None = None,
        force_refresh: bool = False,
    ) -> list[OpenRouterModelInfo]:
        """Fetch and filter available models from OpenRouter catalogue."""
        if self._model_cache is None or force_refresh:
            data = await self._async_http_get("models", api_key=api_key)
            models_raw = data.get("data", [])
            parsed_models: list[OpenRouterModelInfo] = []
            for item in models_raw:
                parsed_models.append(
                    OpenRouterModelInfo(
                        id=item.get("id", ""),
                        name=item.get("name", item.get("id", "")),
                        description=item.get("description", ""),
                        context_length=item.get("context_length", 4096),
                        pricing=item.get("pricing", {}),
                        architecture=item.get("architecture", {}),
                        top_provider=item.get("top_provider", {}),
                    )
                )
            self._model_cache = parsed_models

        filtered = self._model_cache or []
        if provider:
            filtered = [m for m in filtered if provider.lower() in m.id.lower()]
        if modality:
            filtered = [m for m in filtered if modality.lower() in m.architecture.get("modality", "").lower()]
        if max_price is not None:
            filtered = [m for m in filtered if float(m.pricing.get("prompt", 0)) <= max_price]

        return filtered

    async def resolve_route(
        self,
        task_type: str,
        tier: str = "medium",
        budget: str = "standard",
    ) -> RouteResolution:
        """Intelligently match task complexity and tier to optimal OpenRouter models."""
        return resolve_model_route(task_type, tier=tier, budget=budget)

    async def jsonrpc_dispatch(
        self,
        payload: dict[str, Any] | list[dict[str, Any]],
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Dispatch JSON-RPC 2.0 request or batch request."""
        return await execute_jsonrpc_dispatch(self, payload, api_key=api_key)
