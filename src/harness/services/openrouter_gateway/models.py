"""Domain schemas and response models for OpenRouter and JSON-RPC 2.0 communication."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_KILO_GATEWAY_URL = "https://api.kilo.ai/api/openrouter"


class ModelMessage(BaseModel):
    """Chat message schema."""

    role: Literal["system", "user", "assistant", "tool"] = "user"
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class ReasoningConfig(BaseModel):
    """Reasoning effort and thinking budget parameters."""

    effort: Literal["high", "medium", "low", "off"] | None = None
    max_thinking_tokens: int | None = None


class ProviderPreferences(BaseModel):
    """OpenRouter provider routing preferences."""

    order: list[str] = Field(default_factory=list)
    allow_fallbacks: bool = True
    data_collection: Literal["allow", "deny"] = "deny"
    require_parameters: bool = False


class OpenRouterChatResponse(BaseModel):
    """Normalized chat completion response."""

    id: str | None = None
    model: str
    content: str
    finish_reason: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class OpenRouterModelInfo(BaseModel):
    """Model information from OpenRouter catalogue."""

    id: str
    name: str
    description: str = ""
    context_length: int = 4096
    pricing: dict[str, Any] = Field(default_factory=dict)
    architecture: dict[str, Any] = Field(default_factory=dict)
    top_provider: dict[str, Any] = Field(default_factory=dict)


class RouteResolution(BaseModel):
    """Intelligent route recommendation."""

    selected_model: str
    fallback_models: list[str] = Field(default_factory=list)
    reasoning_budget: str = "off"
    rationale: str


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 Error Object."""

    code: int
    message: str
    data: Any | None = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response Object."""

    jsonrpc: str = "2.0"
    result: Any | None = None
    error: JSONRPCError | None = None
    id: str | int | None = None
