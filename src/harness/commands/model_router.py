"""Dynamic Model Router CLI commands.

Provides headless Click CLI introspection for 3-tier dynamic model switching,
offline prompt complexity profiling, routing matrix resolution, resilient failover simulation,
and visual HTML briefs.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
from harness.services.dynamic_model_router import (
    DYNAMIC_MODEL_ROUTER_SERVICE_KEY,
    ComplexityProfileData,
    DynamicModelRouterService,
    NormalizedResponseData,
    RoutingResolutionData,
)

logger = structlog.get_logger(__name__)


def get_model_router_service(
    context: ServiceContext | None = None,
) -> DynamicModelRouterService:
    """Resolve DynamicModelRouterService from context or fall back to plugin singleton / engine."""
    if context is not None:
        svc = context.optional(DYNAMIC_MODEL_ROUTER_SERVICE_KEY)
        if svc is not None:
            return svc

    # Fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.dynamic_model_router.main import (
            plugin as router_plugin,
        )

        return router_plugin
    except Exception as exc:
        logger.warning(
            "dynamic_model_router_plugin_fallback_failed", error=str(exc)
        )
        skill_scripts = (
            _ws_root
            / ".agents"
            / "skills"
            / "dynamic-model-router"
            / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from dynamic_model_router_engine import (  # type: ignore
            DynamicModelRouterEngine,
            TaskComplexity,
        )

        class _EngineAdapter(DynamicModelRouterService):
            def __init__(self) -> None:
                self._eng = DynamicModelRouterEngine()

            def profile_complexity(
                self, prompt: str, candidate_tools: Any = None
            ) -> ComplexityProfileData:
                prof = self._eng.profile_complexity(prompt, candidate_tools)
                return ComplexityProfileData(
                    tier=prof.tier.value,
                    complexity_score=prof.complexity_score,
                    token_count=prof.token_count,
                    word_count=prof.word_count,
                    has_code_blocks=prof.has_code_blocks,
                    matched_keywords=list(prof.matched_keywords),
                    duration_ms=prof.duration_ms,
                    reasoning_depth_detected=prof.reasoning_depth_detected,
                    tool_interaction_count=prof.tool_interaction_count,
                    intent_tag=prof.intent_tag,
                )

            def resolve_route(
                self, complexity: str, cost_ceiling: float | None = None
            ) -> RoutingResolutionData:
                res = self._eng.resolve_route(complexity, cost_ceiling)
                from harness.services.dynamic_model_router import ModelConfigData

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
                tier = (
                    TaskComplexity.from_str(override_complexity)
                    if override_complexity
                    else self._eng.profile_complexity(prompt).tier
                )
                routing = self._eng.resolve_route(tier)
                res = self._eng.execute_with_fallback(prompt, routing)
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
                tier = self._eng.profile_complexity(prompt).tier
                routing = self._eng.resolve_route(tier)
                res = self._eng.execute_with_fallback(
                    prompt, routing, failing_providers=set(failing_providers or [])
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
                return self._eng.generate_visual_brief(output_path=output_path)

        return _EngineAdapter()


@click.group("router")
def model_router_group() -> None:
    """Dynamic Model Router CLI — 3-tier switching & resilient failover commands."""
    pass


@model_router_group.command("profile")
@click.argument("prompt", type=str)
@click.option(
    "--tools",
    type=str,
    default="",
    help="Comma-separated candidate tool names (e.g. bash,grep,sql)",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def profile_cmd(prompt: str, tools: str, json_output: bool) -> None:
    """Deterministically profile prompt complexity (<5ms, zero-LLM)."""
    tool_list = [t.strip() for t in tools.split(",") if t.strip()] if tools else None
    svc = get_model_router_service()
    prof = svc.profile_complexity(prompt, tool_list)

    if json_output:
        click.echo(_json.dumps(prof.model_dump(), indent=2))
        return

    click.echo(f"Prompt Complexity Profile:")
    click.echo(f"  Tier:             {prof.tier.upper()}")
    click.echo(f"  Score:            {prof.complexity_score}")
    click.echo(f"  Words / Tokens:   {prof.word_count} words / ~{prof.token_count} tokens")
    click.echo(f"  Has Code Blocks:  {prof.has_code_blocks}")
    click.echo(f"  Matched Keywords: {', '.join(prof.matched_keywords) or 'None'}")
    click.echo(f"  Reasoning Depth:  {prof.reasoning_depth_detected}")
    click.echo(f"  Intent:           {prof.intent_tag}")
    click.echo(f"  Profiling Latency: {prof.duration_ms} ms (< 5ms SLA)")


@model_router_group.command("route")
@click.option(
    "--complexity",
    "-c",
    type=click.Choice(["simple", "medium", "complex", "low", "high"], case_sensitive=False),
    default="simple",
    help="Target complexity tier",
)
@click.option(
    "--cost-ceiling",
    type=float,
    default=None,
    help="Optional cost budget ceiling per 1k tokens",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def route_cmd(complexity: str, cost_ceiling: float | None, json_output: bool) -> None:
    """Resolve primary and fallback models asserting provider diversity."""
    svc = get_model_router_service()
    res = svc.resolve_route(complexity, cost_ceiling)

    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"Routing Resolution for '{res.complexity.upper()}':")
    click.echo(f"  Primary Model:    {res.primary.provider} / {res.primary.model_name}")
    click.echo(f"  Fallback Model:   {res.fallback.provider} / {res.fallback.model_name}")
    click.echo(f"  Provider Diversity: {'PASS (Decoupled Cloud)' if res.provider_diversity_enforced else 'FAIL'}")
    click.echo(f"  Est. Cost / 1k:   ${res.estimated_cost_per_1k:.5f}")
    click.echo(f"  Reasoning Budget: {res.reasoning_budget}")


@model_router_group.command("simulate")
@click.argument("prompt", type=str)
@click.option(
    "--fail-primary",
    is_flag=True,
    help="Simulate primary provider outage (HTTP 429/503/timeout)",
)
@click.option(
    "--fail-all",
    is_flag=True,
    help="Simulate complete provider outage across all candidates",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def simulate_cmd(
    prompt: str, fail_primary: bool, fail_all: bool, json_output: bool
) -> None:
    """Simulate end-to-end routing execution with automated failover."""
    svc = get_model_router_service()
    prof = svc.profile_complexity(prompt)
    routing = svc.resolve_route(prof.tier)

    failing: list[str] = []
    if fail_all:
        failing = [
            routing.primary.provider,
            routing.primary.model_name,
            routing.fallback.provider,
            routing.fallback.model_name,
        ] + [m.provider for m in routing.fallback_chain]
    elif fail_primary:
        failing = [routing.primary.provider, routing.primary.model_name]

    res = svc.simulate_execution(prompt, failing)

    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"Execution Simulation Result:")
    click.echo(f"  Status:          {res.status}")
    click.echo(f"  Tier:            {res.complexity_tier.upper()}")
    click.echo(f"  Primary Model:   {res.primary_model}")
    click.echo(f"  Executed Model:  {res.executed_model or 'None'}")
    click.echo(f"  Fallback Used:   {res.fallback_used}")
    click.echo(f"  Attempts:        {res.attempts}")
    click.echo(f"  Latency:         {res.latency_ms} ms")
    click.echo("  Execution Trace:")
    for step in res.trace:
        click.echo(f"    - {step}")
    if res.error:
        click.echo(f"  Error:           {res.error}")


@model_router_group.command("brief")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Destination file path for HTML brief",
)
def brief_cmd(output: Path | None) -> None:
    """Generate interactive HTML visual brief with routing telemetry."""
    svc = get_model_router_service()
    brief_path = svc.generate_visual_brief(output)
    click.echo(f"Interactive Visual Brief generated: {brief_path}")
