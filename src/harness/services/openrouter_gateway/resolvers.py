"""Single-seam IoC resolution functions for OpenRouter Gateway subsystem per Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.services.openrouter_gateway.protocols import (
    OPENROUTER_GATEWAY_KEY,
    OpenRouterGatewayServiceProtocol,
)
from harness.services.openrouter_gateway.service import OpenRouterGatewayService

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext

_DEFAULT_GATEWAY = OpenRouterGatewayService()


def resolve_openrouter_gateway_service(
    context: ServiceContext | None = None,
) -> OpenRouterGatewayServiceProtocol:
    """Resolve the OpenRouter Gateway service instance from context or fallback to default singleton."""
    if context is not None and context.has(OPENROUTER_GATEWAY_KEY):
        return context.require(OPENROUTER_GATEWAY_KEY)
    return _DEFAULT_GATEWAY
