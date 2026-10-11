"""Chat completion execution engine for OpenRouter gateway."""

from __future__ import annotations

from typing import Any, Callable, Coroutine

from harness.services.openrouter_gateway.models import (
    ModelMessage,
    OpenRouterChatResponse,
    ReasoningConfig,
)


async def execute_chat_completion(
    post_fn: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
    default_model: str,
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
    target_model = model or default_model
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

    provider_opts: dict[str, Any] = {"allow_fallbacks": allow_fallbacks}
    if order:
        provider_opts["order"] = order
    payload["provider"] = provider_opts

    if reasoning:
        reasoning_dict = reasoning.model_dump() if isinstance(reasoning, ReasoningConfig) else reasoning
        payload["reasoning"] = reasoning_dict

    data = await post_fn(
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
