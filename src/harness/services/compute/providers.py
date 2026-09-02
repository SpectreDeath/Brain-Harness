"""Pluggable provider reasoning transformers and payload synthesis adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from harness.services.compute.types import ThinkingBudget


class BaseProviderAdapter(ABC):
    """Abstract base adapter for vendor-specific reasoning and model parameter transforms."""

    @abstractmethod
    def can_handle(self, model_name: str) -> bool:
        """Return True if this adapter supports the specified model name."""

    @abstractmethod
    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Synthesize provider-specific payload parameters."""


class GeminiProviderAdapter(BaseProviderAdapter):
    """Transformer for Google Gemini reasoning and thinking configurations."""

    def can_handle(self, model_name: str) -> bool:
        return "gemini" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if max_tokens:
            payload["max_tokens"] = max_tokens

        if thinking_level == ThinkingBudget.OFF:
            payload["thinking_config"] = {"thinking_budget": 0}
        elif thinking_level == ThinkingBudget.LOW:
            payload["thinking_config"] = {"thinking_budget": 1024}
        elif thinking_level == ThinkingBudget.MEDIUM:
            payload["thinking_config"] = {"thinking_budget": max(4096, budget_tokens)}
        elif thinking_level == ThinkingBudget.HIGH:
            payload["thinking_config"] = {"thinking_budget": max(16384, budget_tokens)}

        payload["thinking_budget"] = thinking_level.value
        payload["reasoning_effort"] = thinking_level.value
        return payload


class ClaudeProviderAdapter(BaseProviderAdapter):
    """Transformer for Anthropic Claude extended thinking parameters."""

    def can_handle(self, model_name: str) -> bool:
        return "claude" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if thinking_level != ThinkingBudget.OFF and budget_tokens > 0:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget_tokens,
            }
            if not max_tokens or max_tokens <= budget_tokens:
                payload["max_tokens"] = budget_tokens + 4096
            else:
                payload["max_tokens"] = max_tokens
        else:
            payload["thinking"] = {"type": "disabled"}
            if max_tokens:
                payload["max_tokens"] = max_tokens

        payload["reasoning_effort"] = thinking_level.value
        return payload


class OpenAIProviderAdapter(BaseProviderAdapter):
    """Transformer for OpenAI o1 / o3-mini and GPT-4o reasoning models."""

    def can_handle(self, model_name: str) -> bool:
        m = model_name.lower()
        return "o1" in m or "o3" in m or "gpt-4" in m or "openai" in m

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model_name, "temperature": temperature}
        if max_tokens:
            payload["max_tokens"] = max_tokens

        effort_map = {
            ThinkingBudget.HIGH: "high",
            ThinkingBudget.MEDIUM: "medium",
            ThinkingBudget.LOW: "low",
            ThinkingBudget.OFF: "low",
        }
        payload["reasoning_effort"] = effort_map.get(thinking_level, "medium")
        return payload


class DeepSeekProviderAdapter(BaseProviderAdapter):
    """Transformer for DeepSeek-R1 / DeepSeek-V3 reasoning configurations."""

    def can_handle(self, model_name: str) -> bool:
        return "deepseek" in model_name.lower() or "r1" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "extra_body": {"reasoning_effort": thinking_level.value},
            "budget_tokens": budget_tokens,
            "reasoning_effort": thinking_level.value,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload


class OllamaProviderAdapter(BaseProviderAdapter):
    """Transformer for Ollama and local LLM reasoning runtimes."""

    def can_handle(self, model_name: str) -> bool:
        return "ollama" in model_name.lower() or "qwen" in model_name.lower() or "llama" in model_name.lower()

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "options": {"num_predict": max_tokens or (budget_tokens + 2048)},
            "reasoning_effort": thinking_level.value,
        }
        return payload


class FallbackLiteLLMAdapter(BaseProviderAdapter):
    """Fallback transformer for generic LiteLLM and OpenRouter models."""

    def can_handle(self, model_name: str) -> bool:
        return True

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "reasoning_effort": thinking_level.value,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload


class ProviderReasoningRegistry:
    """Authoritative registry of pluggable provider reasoning transformers."""

    def __init__(self) -> None:
        self._adapters: list[BaseProviderAdapter] = [
            GeminiProviderAdapter(),
            ClaudeProviderAdapter(),
            OpenAIProviderAdapter(),
            DeepSeekProviderAdapter(),
            OllamaProviderAdapter(),
            FallbackLiteLLMAdapter(),
        ]

    def register(self, adapter: BaseProviderAdapter, insert_front: bool = True) -> None:
        """Register a new custom provider adapter."""
        if insert_front:
            self._adapters.insert(0, adapter)
        else:
            self._adapters.insert(len(self._adapters) - 1, adapter)

    def get_adapter(self, model_name: str) -> BaseProviderAdapter:
        """Resolve the matching provider adapter for model name."""
        for adapter in self._adapters:
            if adapter.can_handle(model_name):
                return adapter
        return self._adapters[-1]

    def transform(
        self,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Synthesize target provider payload via matched adapter."""
        adapter = self.get_adapter(model_name)
        return adapter.transform(
            model_name,
            thinking_level,
            budget_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
        )


# Global authoritative provider registry
_GLOBAL_PROVIDER_REGISTRY = ProviderReasoningRegistry()


class ProviderReasoningAdapter:
    """Facade for provider payload synthesis delegating to pluggable registry."""

    @classmethod
    def get_provider_payload(
        cls,
        model_name: str,
        thinking_level: ThinkingBudget,
        budget_tokens: int,
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Synthesize exact API request dictionary for target provider model."""
        return _GLOBAL_PROVIDER_REGISTRY.transform(
            model_name,
            thinking_level,
            budget_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @classmethod
    def register_adapter(cls, adapter: BaseProviderAdapter, insert_front: bool = True) -> None:
        """Register a custom provider adapter into the global registry."""
        _GLOBAL_PROVIDER_REGISTRY.register(adapter, insert_front=insert_front)
