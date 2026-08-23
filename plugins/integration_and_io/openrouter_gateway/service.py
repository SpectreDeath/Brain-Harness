"""OpenRouter Gateway Service — typed async service, routing engine, and JSON-RPC 2.0 protocol shim."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from typing import Any, Literal
import structlog
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey
from .headers import build_kilo_headers

logger = structlog.get_logger()

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
        """Format messages to preserve KV-cache prefix under Kilo Context Epoch heuristics (KI-KILO-01).

        The baseline system prompt remains immutable at index 0.
        Chronological environment / state updates are appended as mid-conversation system updates.
        """
        formatted: list[dict[str, Any]] = [
            {"role": "system", "content": baseline_system_prompt}
        ]

        for msg in messages:
            if msg.get("role") == "system":
                continue
            formatted.append(msg)

        if mid_conversation_updates:
            combined_updates = "\n\n".join(mid_conversation_updates)
            formatted.append({
                "role": "system",
                "content": f"[Context Update]\n{combined_updates}",
            })

        return formatted

    async def _async_http_post(
        self,
        endpoint_path: str,
        payload: dict[str, Any],
        api_key: str | None = None,
        task_id: str | None = None,
        feature: str | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Perform asynchronous HTTP POST request to OpenRouter / Kilo Gateway."""
        resolved_key = self._resolve_api_key(api_key)
        url = f"{self._base_url}/{endpoint_path.lstrip('/')}"

        headers = build_kilo_headers(
            task_id=task_id,
            organization_id=self._organization_id,
            feature=feature,
        )
        if resolved_key:
            headers["Authorization"] = f"Bearer {resolved_key}"

        def _do_request() -> dict[str, Any]:
            body_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_data = resp.read().decode("utf-8")
                    return json.loads(resp_data)
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                try:
                    parsed_err = json.loads(err_body)
                except Exception:
                    parsed_err = {"error": err_body}
                raise RuntimeError(f"OpenRouter HTTP {e.code}: {parsed_err}") from e
            except Exception as e:
                raise RuntimeError(f"OpenRouter network error: {e}") from e

        return await asyncio.to_thread(_do_request)

    async def _async_http_get(
        self,
        endpoint_path: str,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Perform asynchronous HTTP GET request."""
        resolved_key = self._resolve_api_key(api_key)
        url = f"{self._base_url}/{endpoint_path.lstrip('/')}"
        headers = build_kilo_headers(organization_id=self._organization_id)
        if resolved_key:
            headers["Authorization"] = f"Bearer {resolved_key}"

        def _do_request() -> dict[str, Any]:
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_data = resp.read().decode("utf-8")
                    return json.loads(resp_data)
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"OpenRouter HTTP {e.code}: {err_body}") from e
            except Exception as e:
                raise RuntimeError(f"OpenRouter network error: {e}") from e

        return await asyncio.to_thread(_do_request)

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
        target_model = model or self._default_model
        raw_messages = [
            m.model_dump() if isinstance(m, ModelMessage) else m for m in messages
        ]

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": raw_messages,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        # Provider routing / fallbacks
        provider_opts: dict[str, Any] = {"allow_fallbacks": allow_fallbacks}
        if order:
            provider_opts["order"] = order
        payload["provider"] = provider_opts

        # Reasoning configuration
        if reasoning:
            reasoning_dict = reasoning.model_dump() if isinstance(reasoning, ReasoningConfig) else reasoning
            payload["reasoning"] = reasoning_dict

        data = await self._async_http_post(
            "chat/completions",
            payload=payload,
            api_key=api_key,
            task_id=task_id,
            feature=feature,
        )

        choices = data.get("choices", [])
        content = ""
        finish_reason = None
        if choices:
            message_obj = choices[0].get("message", {})
            content = message_obj.get("content", "")
            finish_reason = choices[0].get("finish_reason")

        return OpenRouterChatResponse(
            id=data.get("id"),
            model=data.get("model", target_model),
            content=content,
            finish_reason=finish_reason,
            usage=data.get("usage", {}),
            raw_response=data,
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
            filtered = [
                m for m in filtered
                if modality.lower() in m.architecture.get("modality", "").lower()
            ]
        if max_price is not None:
            filtered = [
                m for m in filtered
                if float(m.pricing.get("prompt", 0)) <= max_price
            ]

        return filtered

    async def resolve_route(
        self,
        task_type: str,
        tier: str = "medium",
        budget: str = "standard",
    ) -> RouteResolution:
        """Intelligently match task complexity and tier to optimal OpenRouter models."""
        task = task_type.lower()
        tier_clean = tier.lower()

        if "reason" in task or "architecture" in task or "complex" in task or tier_clean == "high":
            return RouteResolution(
                selected_model="anthropic/claude-3.7-sonnet",
                fallback_models=[
                    "openai/gpt-4.5-preview",
                    "deepseek/deepseek-r1",
                    "google/gemini-2.0-flash-thinking-exp:free",
                ],
                reasoning_budget="high",
                rationale="High complexity / architectural task requiring deep reasoning and extended thinking budget.",
            )

        if "code" in task or "refactor" in task or "edit" in task:
            return RouteResolution(
                selected_model="anthropic/claude-3.7-sonnet",
                fallback_models=[
                    "openai/gpt-4o",
                    "deepseek/deepseek-chat",
                    "qwen/qwen-2.5-coder-32b-instruct",
                ],
                reasoning_budget="medium",
                rationale="Code editing and synthesis task requiring high precision and syntax fidelity.",
            )

        if "quick" in task or "format" in task or "summary" in task or budget == "low":
            return RouteResolution(
                selected_model="google/gemini-2.0-flash-001",
                fallback_models=[
                    "meta-llama/llama-3.3-70b-instruct",
                    "mistralai/mistral-small-24b-instruct-2501",
                ],
                reasoning_budget="off",
                rationale="Lightweight or high-speed summarization task optimized for low latency and zero unnecessary tokens.",
            )

        return RouteResolution(
            selected_model="anthropic/claude-3.7-sonnet",
            fallback_models=["google/gemini-2.0-flash-001", "openai/gpt-4o"],
            reasoning_budget="low",
            rationale="Standard general-purpose autonomous agent turn.",
        )

    async def jsonrpc_dispatch(self, payload: dict[str, Any], api_key: str | None = None) -> dict[str, Any]:
        """Dispatch JSON-RPC 2.0 request or batch request."""
        if isinstance(payload, list):
            # Batch request
            results = [await self._jsonrpc_single(req, api_key=api_key) for req in payload]
            return {"batch": results}
        return await self._jsonrpc_single(payload, api_key=api_key)

    async def _jsonrpc_single(self, request: dict[str, Any], api_key: str | None = None) -> dict[str, Any]:
        """Process a single JSON-RPC 2.0 request object."""
        req_id = request.get("id")
        if request.get("jsonrpc") != "2.0":
            return JSONRPCResponse(
                id=req_id,
                error=JSONRPCError(code=-32600, message="Invalid Request: jsonrpc must be '2.0'"),
            ).model_dump()

        method = request.get("method", "")
        params = request.get("params", {}) or {}

        try:
            if method == "openrouter.chat":
                messages = params.get("messages", [])
                model = params.get("model")
                reasoning = params.get("reasoning")
                temp = params.get("temperature")
                max_tokens = params.get("max_tokens")
                order = params.get("order")
                allow_fallbacks = params.get("allow_fallbacks", True)

                resp = await self.chat(
                    messages=messages,
                    model=model,
                    reasoning=reasoning,
                    temperature=temp,
                    max_tokens=max_tokens,
                    order=order,
                    allow_fallbacks=allow_fallbacks,
                    api_key=api_key,
                )
                return JSONRPCResponse(id=req_id, result=resp.model_dump()).model_dump()

            elif method == "openrouter.models":
                provider = params.get("provider")
                modality = params.get("modality")
                max_price = params.get("max_price")
                models = await self.list_models(
                    provider=provider,
                    modality=modality,
                    max_price=max_price,
                    api_key=api_key,
                )
                return JSONRPCResponse(
                    id=req_id,
                    result=[m.model_dump() for m in models],
                ).model_dump()

            elif method == "openrouter.route":
                task_type = params.get("task_type", "general")
                tier = params.get("tier", "medium")
                budget = params.get("budget", "standard")
                route = await self.resolve_route(task_type, tier=tier, budget=budget)
                return JSONRPCResponse(id=req_id, result=route.model_dump()).model_dump()

            else:
                return JSONRPCResponse(
                    id=req_id,
                    error=JSONRPCError(code=-32601, message=f"Method not found: {method}"),
                ).model_dump()

        except Exception as e:
            logger.error("JSON-RPC execution error", method=method, error=str(e))
            return JSONRPCResponse(
                id=req_id,
                error=JSONRPCError(code=-32000, message=str(e)),
            ).model_dump()


OPENROUTER_GATEWAY_KEY = ServiceKey[OpenRouterGatewayService]("service.openrouter_gateway")
