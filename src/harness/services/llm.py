"""LLM service plugin — abstract LLM provider interface.

Provides a standard interface for language model inference that
other plugins can depend on. Ships with a litellm-based default
implementation that supports 100+ providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()

from harness.services.compute_assessor import (
    AssessmentTrace,
    ComplexityDimension,
    ComplexityVector,
    ComputeAssessment,
    ComputeRouter,
    ComputeVisualBriefGenerator,
    DimensionalScorer,
    ModelTier,
    ProviderReasoningAdapter,
    ThinkingBudget,
)

# Canonical service key for LLM providers
LLM_SERVICE_KEY: ServiceKey[LLMService] = ServiceKey("llm.provider")


@dataclass
class LLMMessage:
    """A single message in a conversation."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class LLMResponse:
    """Response from an LLM completion call."""

    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class LLMService(ABC):
    """Abstract LLM provider interface.

    Plugins that need LLM access resolve this service from the context::

        llm = ctx.require(LLM_SERVICE_KEY)
        response = await llm.complete([LLMMessage("user", "Hello")])
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        thinking_budget: ThinkingBudget | str | None = None,
        reasoning_effort: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion from the model.

        Args:
            messages: Conversation history.
            model: Model identifier (provider-specific).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            tools: Optional JSON Schema tool definitions.
            thinking_budget: Optional thinking budget level (High, Medium, Low, Off).
            reasoning_effort: Provider-specific reasoning effort parameter.
        """

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        thinking_budget: ThinkingBudget | str | None = None,
        reasoning_effort: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion from the model.

        Yields content chunks as they arrive.
        """
        yield ""  # pragma: no cover


class LiteLLMService(LLMService):
    """LLM service backed by litellm for multi-provider support.

    Requires the ``llm`` extra: ``pip install harness[llm]``
    """

    def __init__(self, default_model: str = "gpt-4o-mini") -> None:
        self._default_model = default_model

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
        thinking_budget: ThinkingBudget | str | None = None,
        reasoning_effort: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        try:
            import litellm
        except ImportError as e:
            raise RuntimeError(
                "litellm is required for LLM service. "
                "Install with: pip install harness[llm]"
            ) from e

        model = model or self._default_model
        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

        call_kwargs: dict[str, Any] = {
            "model": model,
            "messages": msg_dicts,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        if tools is not None:
            call_kwargs["tools"] = tools

        # Map thinking_budget / reasoning_effort using ProviderReasoningAdapter
        if thinking_budget:
            budget_enum = (
                thinking_budget
                if isinstance(thinking_budget, ThinkingBudget)
                else ThinkingBudget(str(thinking_budget).lower())
                if str(thinking_budget).lower() in [b.value for b in ThinkingBudget]
                else None
            )
            if budget_enum:
                budget_tokens = kwargs.pop(
                    "budget_tokens",
                    16384 if budget_enum == ThinkingBudget.HIGH else 4096 if budget_enum == ThinkingBudget.MEDIUM else 1024 if budget_enum == ThinkingBudget.LOW else 0,
                )
                provider_params = ProviderReasoningAdapter.get_provider_payload(
                    model,
                    budget_enum,
                    budget_tokens,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                for param_key in ("thinking_config", "thinking", "extra_body", "options", "reasoning_effort", "thinking_budget"):
                    if param_key in provider_params:
                        call_kwargs[param_key] = provider_params[param_key]
                if "max_tokens" in provider_params and not max_tokens:
                    call_kwargs["max_tokens"] = provider_params["max_tokens"]
        elif reasoning_effort:
            call_kwargs["reasoning_effort"] = reasoning_effort

        response = await litellm.acompletion(**call_kwargs)

        choice = response.choices[0]
        tool_calls: list[dict[str, Any]] = []
        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                if hasattr(tc, "model_dump"):
                    tool_calls.append(tc.model_dump())
                elif isinstance(tc, dict):
                    tool_calls.append(tc)

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model or model,
            usage=dict(response.usage) if response.usage else {},
            finish_reason=choice.finish_reason or "",
            raw=response.model_dump() if hasattr(response, "model_dump") else {},
            tool_calls=tool_calls,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        thinking_budget: ThinkingBudget | str | None = None,
        reasoning_effort: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        try:
            import litellm
        except ImportError as e:
            raise RuntimeError(
                "litellm is required for LLM service. "
                "Install with: pip install harness[llm]"
            ) from e

        model = model or self._default_model
        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]

        call_kwargs: dict[str, Any] = {
            "model": model,
            "messages": msg_dicts,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs,
        }
        if thinking_budget:
            budget_enum = (
                thinking_budget
                if isinstance(thinking_budget, ThinkingBudget)
                else ThinkingBudget(str(thinking_budget).lower())
                if str(thinking_budget).lower() in [b.value for b in ThinkingBudget]
                else None
            )
            if budget_enum:
                budget_tokens = kwargs.pop(
                    "budget_tokens",
                    16384 if budget_enum == ThinkingBudget.HIGH else 4096 if budget_enum == ThinkingBudget.MEDIUM else 1024 if budget_enum == ThinkingBudget.LOW else 0,
                )
                provider_params = ProviderReasoningAdapter.get_provider_payload(
                    model,
                    budget_enum,
                    budget_tokens,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                for param_key in ("thinking_config", "thinking", "extra_body", "options", "reasoning_effort", "thinking_budget"):
                    if param_key in provider_params:
                        call_kwargs[param_key] = provider_params[param_key]
                if "max_tokens" in provider_params and not max_tokens:
                    call_kwargs["max_tokens"] = provider_params["max_tokens"]
        elif reasoning_effort:
            call_kwargs["reasoning_effort"] = reasoning_effort

        response = await litellm.acompletion(**call_kwargs)

        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content


class LLMPlugin(HarnessPlugin):
    """Built-in plugin that provides the LLM service."""

    def __init__(self, default_model: str = "gpt-4o-mini") -> None:
        self._default_model = default_model
        self._service: LLMService | None = None

    @property
    def name(self) -> str:
        return "llm.provider"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "LLM provider service (litellm multi-provider)"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [LLM_SERVICE_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        self._service = LiteLLMService(default_model=self._default_model)
        ctx.provide(LLM_SERVICE_KEY, self._service, provider=self.name)
        logger.info("LLM service registered", model=self._default_model)

    async def on_unload(self) -> None:
        self._service = None


__all__ = [
    "ComputeAssessment",
    "ComputeRouter",
    "LLMMessage",
    "LLMPlugin",
    "LLMResponse",
    "LLMService",
    "LLM_SERVICE_KEY",
    "LiteLLMService",
    "ModelTier",
    "ThinkingBudget",
]
