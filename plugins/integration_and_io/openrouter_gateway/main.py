"""OpenRouter Gateway Plugin for Brain Harness.

Provides OpenRouter endpoint routing, JSON-RPC 2.0 protocol dispatching,
and Context Epoch KV-cache optimization extracted from Kilo Code.
"""

from __future__ import annotations

import asyncio
from typing import Any, Coroutine, TypeVar
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.openrouter_gateway import (
    OPENROUTER_GATEWAY_KEY,
    OpenRouterGatewayService,
    ReasoningConfig,
)

logger = structlog.get_logger(__name__)

# Global default service singleton for tool invocations
_global_service = OpenRouterGatewayService()

T = TypeVar("T")


def _run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Execute an async coroutine safely whether or not an event loop is already running."""
    try:
        asyncio.get_running_loop()
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)


class OpenRouterGatewayPlugin(HarnessPlugin):
    """Brain Harness plugin for OpenRouter model routing and JSON-RPC 2.0 dispatch."""

    trusted = True

    def __init__(self, service: OpenRouterGatewayService | None = None) -> None:
        self._service = service or _global_service

    @property
    def name(self) -> str:
        return "plugin.openrouter_gateway"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "OpenRouter Gateway routing, JSON-RPC 2.0 protocol engine, and Context Epoch prompt optimizer"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OPENROUTER_GATEWAY_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        """Register the typed service instance in the IoC container."""
        ctx.provide(OPENROUTER_GATEWAY_KEY, self._service, provider=self.name)
        logger.info("Provided OpenRouterGatewayService to context", key=OPENROUTER_GATEWAY_KEY.name)

    async def on_enable(self) -> None:
        """Lifecycle hook when plugin is enabled."""
        logger.info("Enabled OpenRouterGatewayPlugin")

    async def on_disable(self) -> None:
        """Lifecycle hook when plugin is disabled."""
        logger.info("Disabled OpenRouterGatewayPlugin")

    async def on_unload(self) -> None:
        """Clean up resources on unload."""
        logger.info("Unloaded OpenRouterGatewayPlugin")


# ============================================================================
# Exported Tool Functions (Direct ToolRegistry and CLI entrypoints)
# ============================================================================


def openrouter_chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    reasoning: dict[str, Any] | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    order: list[str] | None = None,
    allow_fallbacks: bool = True,
    api_key: str | None = None,
    task_id: str | None = None,
    feature: str | None = None,
) -> dict[str, Any]:
    """Execute chat completion via OpenRouter / Kilo Gateway with model routing."""
    try:
        coro = _global_service.chat(
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
        res = _run_async(coro)
        return {"status": "ok", "response": res.model_dump()}
    except Exception as e:
        logger.error("openrouter_chat tool error", error=str(e))
        return {"status": "error", "error": str(e)}


def openrouter_list_models(
    provider: str | None = None,
    modality: str | None = None,
    max_price: float | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Fetch and filter available models from OpenRouter catalogue."""
    try:
        coro = _global_service.list_models(
            provider=provider,
            modality=modality,
            max_price=max_price,
            api_key=api_key,
        )
        models = _run_async(coro)
        return {
            "status": "ok",
            "count": len(models),
            "models": [m.model_dump() for m in models],
        }
    except Exception as e:
        logger.error("openrouter_list_models tool error", error=str(e))
        return {"status": "error", "error": str(e)}


def openrouter_resolve_route(
    task_type: str,
    tier: str = "medium",
    budget: str = "standard",
) -> dict[str, Any]:
    """Intelligently match task complexity and tier to optimal OpenRouter model routes."""
    try:
        coro = _global_service.resolve_route(task_type, tier=tier, budget=budget)
        route = _run_async(coro)
        return {"status": "ok", "route": route.model_dump()}
    except Exception as e:
        logger.error("openrouter_resolve_route tool error", error=str(e))
        return {"status": "error", "error": str(e)}


def openrouter_jsonrpc_call(
    request_payload: dict[str, Any],
    api_key: str | None = None,
) -> dict[str, Any]:
    """Execute direct JSON-RPC 2.0 protocol request against OpenRouter Gateway."""
    try:
        coro = _global_service.jsonrpc_dispatch(request_payload, api_key=api_key)
        res = _run_async(coro)
        return {"status": "ok", "jsonrpc_response": res}
    except Exception as e:
        logger.error("openrouter_jsonrpc_call tool error", error=str(e))
        return {"status": "error", "error": str(e)}
