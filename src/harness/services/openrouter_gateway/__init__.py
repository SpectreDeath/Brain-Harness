"""OpenRouter Gateway Service — modular subpackage facade."""

from __future__ import annotations

from harness.services.openrouter_gateway.chat import execute_chat_completion
from harness.services.openrouter_gateway.client import format_context_epoch_messages
from harness.services.openrouter_gateway.headers import (
    DEFAULT_EDITOR_NAME,
    ENV_EDITOR_NAME,
    ENV_FEATURE,
    ENV_VERSION,
    HEADER_EDITOR_NAME,
    HEADER_FEATURE,
    HEADER_MACHINE_ID,
    HEADER_ORGANIZATION_ID,
    HEADER_PARENT_TASK_ID,
    HEADER_PROJECT_ID,
    HEADER_TASK_ID,
    HEADER_TESTER,
    TESTER_SUPPRESS_VALUE,
    USER_AGENT_BASE,
    build_kilo_headers,
    get_editor_name_header,
    get_feature_header,
    get_user_agent,
)
from harness.services.openrouter_gateway.jsonrpc import (
    execute_jsonrpc_dispatch,
    execute_jsonrpc_single,
)
from harness.services.openrouter_gateway.models import (
    DEFAULT_KILO_GATEWAY_URL,
    DEFAULT_OPENROUTER_BASE_URL,
    JSONRPCError,
    JSONRPCResponse,
    ModelMessage,
    OpenRouterChatResponse,
    OpenRouterModelInfo,
    ProviderPreferences,
    ReasoningConfig,
    RouteResolution,
)
from harness.services.openrouter_gateway.protocols import (
    OPENROUTER_GATEWAY_KEY,
    OpenRouterGatewayServiceProtocol,
)
from harness.services.openrouter_gateway.resolvers import (
    resolve_openrouter_gateway_service,
)
from harness.services.openrouter_gateway.routing import resolve_model_route
from harness.services.openrouter_gateway.service import OpenRouterGatewayService

__all__ = [
    "DEFAULT_EDITOR_NAME",
    "DEFAULT_KILO_GATEWAY_URL",
    "DEFAULT_OPENROUTER_BASE_URL",
    "ENV_EDITOR_NAME",
    "ENV_FEATURE",
    "ENV_VERSION",
    "HEADER_EDITOR_NAME",
    "HEADER_FEATURE",
    "HEADER_MACHINE_ID",
    "HEADER_ORGANIZATION_ID",
    "HEADER_PARENT_TASK_ID",
    "HEADER_PROJECT_ID",
    "HEADER_TASK_ID",
    "HEADER_TESTER",
    "JSONRPCError",
    "JSONRPCResponse",
    "ModelMessage",
    "OPENROUTER_GATEWAY_KEY",
    "OpenRouterChatResponse",
    "OpenRouterGatewayService",
    "OpenRouterGatewayServiceProtocol",
    "OpenRouterModelInfo",
    "ProviderPreferences",
    "ReasoningConfig",
    "RouteResolution",
    "TESTER_SUPPRESS_VALUE",
    "USER_AGENT_BASE",
    "build_kilo_headers",
    "execute_jsonrpc_dispatch",
    "execute_chat_completion",
    "execute_jsonrpc_single",
    "format_context_epoch_messages",
    "get_editor_name_header",
    "get_feature_header",
    "get_user_agent",
    "resolve_model_route",
    "resolve_openrouter_gateway_service",
]
