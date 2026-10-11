"""Intelligent model routing and task complexity resolution."""

from __future__ import annotations

from harness.services.openrouter_gateway.models import RouteResolution


def resolve_model_route(
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
