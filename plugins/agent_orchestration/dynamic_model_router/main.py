"""Dynamic Model Router Plugin — 3-Tier Model Switching & Failover Engine.

Synthesized from Chidiebere Njoku (freeCodeCamp, 2026) and grounded in
Knowledge Item ki_njoku_dynamic_model_routing.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dynamically ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "dynamic-model-router" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dynamic_model_router_engine import (  # type: ignore
    ComplexityProfile,
    DynamicModelRouterEngine,
    ModelConfig,
    NormalizedResponse,
    RoutingResolution,
    TaskComplexity,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.dynamic_model_router import (
    DYNAMIC_MODEL_ROUTER_SERVICE_KEY,
    ComplexityProfileData,
    DynamicModelRouterService,
    ModelConfigData,
    NormalizedResponseData,
    RoutingResolutionData,
)

logger = structlog.get_logger(__name__)


class DynamicModelRouterPlugin(HarnessPlugin, DynamicModelRouterService):
    """Plugin providing 3-tier dynamic model switching, intent profiling, and failovers."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        config_path = _PLUGIN_DIR / "config.default.yaml"
        self._engine = DynamicModelRouterEngine(
            config_path=config_path if config_path.exists() else None
        )

    @property
    def name(self) -> str:
        return "plugin.dynamic_model_router"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "3-tier dynamic model switching and resilient failover engine "
            "with sub-5ms profiling and provider diversity enforcement"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DYNAMIC_MODEL_ROUTER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container."""
        context.provide(DYNAMIC_MODEL_ROUTER_SERVICE_KEY, self)
        logger.info(
            "dynamic_model_router_plugin_loaded",
            provides=[k.name for k in self.provides],
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Cleanup upon unload."""
        logger.info("dynamic_model_router_plugin_unloaded")

    # --- DynamicModelRouterService Protocol Implementation ---

    def profile_complexity(
        self, prompt: str, candidate_tools: Sequence[str] | None = None
    ) -> ComplexityProfileData:
        """Deterministic syntactic and token complexity evaluation in < 5ms."""
        profile: ComplexityProfile = self._engine.profile_complexity(
            prompt, candidate_tools
        )
        return ComplexityProfileData(
            tier=profile.tier.value,
            complexity_score=profile.complexity_score,
            token_count=profile.token_count,
            word_count=profile.word_count,
            has_code_blocks=profile.has_code_blocks,
            matched_keywords=list(profile.matched_keywords),
            duration_ms=profile.duration_ms,
            reasoning_depth_detected=profile.reasoning_depth_detected,
            tool_interaction_count=profile.tool_interaction_count,
            intent_tag=profile.intent_tag,
        )

    def resolve_route(
        self, complexity: str, cost_ceiling: float | None = None
    ) -> RoutingResolutionData:
        """Resolve primary and fallback models asserting provider diversity."""
        res: RoutingResolution = self._engine.resolve_route(
            complexity, cost_ceiling
        )
        return RoutingResolutionData(
            complexity=res.complexity.value,
            primary=ModelConfigData(
                provider=res.primary.provider,
                model_name=res.primary.model_name,
                cost_per_1k_tokens=res.primary.cost_per_1k_tokens,
                reasoning_budget=res.primary.reasoning_budget,
                timeout_seconds=res.primary.timeout_seconds,
            ),
            fallback=ModelConfigData(
                provider=res.fallback.provider,
                model_name=res.fallback.model_name,
                cost_per_1k_tokens=res.fallback.cost_per_1k_tokens,
                reasoning_budget=res.fallback.reasoning_budget,
                timeout_seconds=res.fallback.timeout_seconds,
            ),
            fallback_chain=[
                ModelConfigData(
                    provider=m.provider,
                    model_name=m.model_name,
                    cost_per_1k_tokens=m.cost_per_1k_tokens,
                    reasoning_budget=m.reasoning_budget,
                    timeout_seconds=m.timeout_seconds,
                )
                for m in res.fallback_chain
            ],
            provider_diversity_enforced=res.provider_diversity_enforced,
            estimated_cost_per_1k=res.estimated_cost_per_1k,
            reasoning_budget=res.reasoning_budget,
        )

    def execute_request(
        self, prompt: str, override_complexity: str | None = None
    ) -> NormalizedResponseData:
        """Execute request through dynamic routing pipeline with fallback encasement."""
        tier = (
            TaskComplexity.from_str(override_complexity)
            if override_complexity
            else self._engine.profile_complexity(prompt).tier
        )
        routing = self._engine.resolve_route(tier)
        res: NormalizedResponse = self._engine.execute_with_fallback(
            prompt, routing
        )
        return NormalizedResponseData(
            status=res.status,
            complexity_tier=res.complexity_tier.value,
            primary_model=res.primary_model,
            executed_model=res.executed_model,
            fallback_used=res.fallback_used,
            response=res.response,
            attempts=res.attempts,
            latency_ms=res.latency_ms,
            trace=list(res.trace),
            error=res.error,
        )

    def simulate_execution(
        self, prompt: str, failing_providers: list[str] | None = None
    ) -> NormalizedResponseData:
        """Simulate dynamic routing execution with injected provider failures."""
        tier = self._engine.profile_complexity(prompt).tier
        routing = self._engine.resolve_route(tier)
        failures = set(failing_providers or [])
        res: NormalizedResponse = self._engine.execute_with_fallback(
            prompt, routing, failing_providers=failures
        )
        return NormalizedResponseData(
            status=res.status,
            complexity_tier=res.complexity_tier.value,
            primary_model=res.primary_model,
            executed_model=res.executed_model,
            fallback_used=res.fallback_used,
            response=res.response,
            attempts=res.attempts,
            latency_ms=res.latency_ms,
            trace=list(res.trace),
            error=res.error,
        )

    def generate_visual_brief(
        self, output_path: str | Path | None = None
    ) -> Path:
        """Generate interactive HTML visual brief with telemetry and topology."""
        return self._engine.generate_visual_brief(output_path=output_path)

    # --- Tool Entrypoints for External / Plugin Execution ---

    def profile_prompt(self, prompt: str) -> dict[str, Any]:
        """Tool entrypoint for profiling prompt complexity."""
        return self.profile_complexity(prompt).model_dump()

    def resolve_routing(
        self, complexity: str, cost_ceiling: float | None = None
    ) -> dict[str, Any]:
        """Tool entrypoint for resolving model routing."""
        return self.resolve_route(complexity, cost_ceiling).model_dump()

    def route_and_execute(
        self, prompt: str, override_complexity: str | None = None
    ) -> dict[str, Any]:
        """Tool entrypoint for end-to-end execution."""
        return self.execute_request(prompt, override_complexity).model_dump()

    def model_router_visual_brief(self, output_path: str | None = None) -> str:
        """Tool entrypoint for generating visual brief."""
        brief_path = self.generate_visual_brief(output_path)
        return str(brief_path)


# Rule 45: Plugin Module Singleton & IoC Provider Invariant
plugin = DynamicModelRouterPlugin()
