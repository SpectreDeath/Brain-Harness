"""Comprehensive tests for deepened dynamic model router architecture.

Covers:
- Slotted frozen dataclass immutability (Rule 12 & Rule 43)
- Sub-5ms deterministic syntax & regex intent profiling benchmark
- Declarative routing matrix with Provider Diversity Invariant
- Resilient timeout encasement and automated failover execution
- Circuit breaker and fallback exhaustion guards
- Canonical schema normalization and zero vendor SDK object leakage
- IoC service key registration & resolution (Rule 2 & Rule 49)
- PluginValidator compliance (Rule 34 & Rule 38)
- Click CLI commands and CliRunner assertions (Rule 6, 10, 23)
- Standalone HTML visual brief generation
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "dynamic-model-router" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dynamic_model_router_engine import (
    ComplexityProfile,
    DynamicModelRouterEngine,
    ModelConfig,
    NormalizedResponse,
    RoutingResolution,
    TaskComplexity,
)

from harness.commands.model_router import model_router_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.dynamic_model_router import (
    DYNAMIC_MODEL_ROUTER_SERVICE_KEY,
    ComplexityProfileData,
    DynamicModelRouterService,
    ModelConfigData,
    NormalizedResponseData,
    RoutingResolutionData,
)
from plugins.agent_orchestration.dynamic_model_router.main import (
    DynamicModelRouterPlugin,
)
from plugins.agent_orchestration.dynamic_model_router.main import (
    plugin as router_plugin,
)


@pytest.fixture
def engine() -> DynamicModelRouterEngine:
    return DynamicModelRouterEngine()


@pytest.fixture
def service_context() -> ServiceContext:
    ctx = ServiceContext()
    ctx.provide(DYNAMIC_MODEL_ROUTER_SERVICE_KEY, router_plugin)
    return ctx


# --- 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43) ---


def test_frozen_dataclass_immutability():
    """Verify slotted & frozen dataclasses prevent attribute mutation (Rule 12 & Rule 43)."""
    prof = ComplexityProfile(
        tier=TaskComplexity.SIMPLE,
        complexity_score=0.1,
        token_count=10,
        word_count=5,
        has_code_blocks=False,
        matched_keywords=(),
    )
    with pytest.raises((AttributeError, TypeError)):
        prof.tier = TaskComplexity.COMPLEX  # type: ignore

    cfg = ModelConfig(provider="openai", model_name="gpt-4o-mini")
    with pytest.raises((AttributeError, TypeError)):
        cfg.model_name = "claude"  # type: ignore

    res = RoutingResolution(
        complexity=TaskComplexity.SIMPLE,
        primary=cfg,
        fallback=cfg,
    )
    with pytest.raises((AttributeError, TypeError)):
        res.primary = cfg  # type: ignore

    norm = NormalizedResponse(
        status="success",
        complexity_tier=TaskComplexity.SIMPLE,
        primary_model="gpt-4o-mini",
        executed_model="gpt-4o-mini",
        fallback_used=False,
        response="hello",
    )
    with pytest.raises((AttributeError, TypeError)):
        norm.status = "failed"  # type: ignore


# --- 2. Deterministic Sub-5ms Offline Profiling ---


def test_profiling_simple_prompt(engine: DynamicModelRouterEngine):
    """Verify short prompt with no code or keywords resolves to SIMPLE."""
    prompt = "Summarize the customer email in one polite sentence."
    prof = engine.profile_complexity(prompt)
    assert prof.tier == TaskComplexity.SIMPLE
    assert prof.complexity_score < 0.25
    assert prof.has_code_blocks is False
    assert prof.reasoning_depth_detected is False
    assert prof.duration_ms < 5.0


def test_profiling_medium_prompt(engine: DynamicModelRouterEngine):
    """Verify moderate-length prompt (80-300 words) resolves to MEDIUM."""
    prompt = " ".join(["word"] * 120)
    prof = engine.profile_complexity(prompt)
    assert prof.tier == TaskComplexity.MEDIUM
    assert prof.has_code_blocks is False


def test_profiling_complex_code_prompt(engine: DynamicModelRouterEngine):
    """Verify prompt containing markdown code blocks resolves to COMPLEX."""
    prompt = "Review this snippet:\n```python\ndef solve(): pass\n```"
    prof = engine.profile_complexity(prompt)
    assert prof.tier == TaskComplexity.COMPLEX
    assert prof.has_code_blocks is True


def test_profiling_complex_reasoning_prompt(engine: DynamicModelRouterEngine):
    """Verify prompt containing reasoning keywords resolves to COMPLEX."""
    prompt = "Refactor the kernel architecture and prove concurrency invariants."
    prof = engine.profile_complexity(prompt)
    assert prof.tier == TaskComplexity.COMPLEX
    assert prof.reasoning_depth_detected is True
    assert "refactor" in prof.matched_keywords or "architecture" in prof.matched_keywords


def test_profiling_sub_5ms_benchmark(engine: DynamicModelRouterEngine):
    """Assert 1,000 synthetic iterations achieve P99 latency < 5.0ms with zero network calls."""
    prompts = [
        "Simple FAQ lookup question about opening hours",
        "Refactor the data pipeline and optimize query performance",
        "```sql\nSELECT * FROM users WHERE active = 1\n```",
        " ".join(["test"] * 100),
    ]
    latencies = []
    for i in range(1000):
        t0 = time.perf_counter()
        engine.profile_complexity(prompts[i % len(prompts)])
        latencies.append((time.perf_counter() - t0) * 1000.0)

    latencies.sort()
    p99 = latencies[int(len(latencies) * 0.99)]
    assert p99 < 5.0, f"P99 latency ({p99:.3f}ms) exceeded 5.0ms threshold"


# --- 3. Declarative Routing Resolution & Provider Diversity Invariant ---


def test_provider_diversity_invariant(engine: DynamicModelRouterEngine):
    """Verify that primary and fallback models reside on distinct cloud providers across all tiers."""
    for tier in [TaskComplexity.SIMPLE, TaskComplexity.MEDIUM, TaskComplexity.COMPLEX]:
        routing = engine.resolve_route(tier)
        assert routing.primary.provider != routing.fallback.provider, (
            f"Provider diversity violated for {tier}: primary={routing.primary.provider}, "
            f"fallback={routing.fallback.provider}"
        )
        assert routing.provider_diversity_enforced is True


def test_routing_cost_ceiling_downgrade(engine: DynamicModelRouterEngine):
    """Verify that a restrictive cost ceiling gracefully downgrades tier."""
    routing = engine.resolve_route(TaskComplexity.COMPLEX, cost_ceiling=0.0005)
    assert routing.complexity == TaskComplexity.SIMPLE


# --- 4. Resilient Execution, Socket Timeout & Automated Failover ---


def test_execute_primary_success(engine: DynamicModelRouterEngine):
    """Verify primary model succeeds when no outages occur."""
    routing = engine.resolve_route(TaskComplexity.SIMPLE)
    res = engine.execute_with_fallback("Hello world", routing)
    assert res.status == "success"
    assert res.fallback_used is False
    assert res.attempts == 1
    assert res.executed_model == routing.primary.model_name
    assert "gpt-4o-mini" in res.response


def test_execute_primary_failure_activates_fallback(engine: DynamicModelRouterEngine):
    """Verify primary provider failure transparently activates secondary fallback."""
    routing = engine.resolve_route(TaskComplexity.SIMPLE)
    # Simulate primary provider outage
    res = engine.execute_with_fallback(
        "Hello world",
        routing,
        failing_providers={routing.primary.provider},
    )
    assert res.status == "fallback_success"
    assert res.fallback_used is True
    assert res.attempts == 2
    assert res.executed_model == routing.fallback.model_name
    assert "claude-3-5-haiku" in res.executed_model or "gemini" in res.executed_model
    assert len(res.trace) >= 2


def test_execute_all_providers_fail(engine: DynamicModelRouterEngine):
    """Verify all providers failing returns all_fallbacks_exhausted cleanly."""
    routing = engine.resolve_route(TaskComplexity.SIMPLE)
    all_providers = {routing.primary.provider, routing.fallback.provider} | {
        m.provider for m in routing.fallback_chain
    }
    res = engine.execute_with_fallback(
        "Hello world",
        routing,
        failing_providers=all_providers,
    )
    assert res.status == "all_fallbacks_exhausted"
    assert res.fallback_used is True
    assert res.error is not None


def test_execute_circuit_breaker(engine: DynamicModelRouterEngine):
    """Verify circuit breaker trips when retry ceiling is exceeded."""
    routing = engine.resolve_route(TaskComplexity.COMPLEX)
    all_providers = {routing.primary.provider, routing.fallback.provider}
    res = engine.execute_with_fallback(
        "Hello world",
        routing,
        failing_providers=all_providers,
        max_retries=1,
    )
    assert res.status == "circuit_breaker_open"
    assert "Circuit breaker opened" in (res.error or "")


def test_execute_with_callable(engine: DynamicModelRouterEngine):
    """Verify invocation of real/custom callable adapters."""
    routing = engine.resolve_route(TaskComplexity.SIMPLE)

    def mock_primary(prompt: str) -> str:
        raise TimeoutError("Socket timeout exceeded")

    def mock_fallback(prompt: str) -> str:
        return f"Fallback processed: {prompt}"

    res = engine.execute_with_fallback(
        "Test prompt",
        routing,
        primary_callable=mock_primary,
        fallback_callable=mock_fallback,
    )
    assert res.status == "fallback_success"
    assert res.fallback_used is True
    assert "Fallback processed" in res.response


# --- 5. Output Schema Normalization & Zero SDK Leak ---


def test_normalized_response_schema(engine: DynamicModelRouterEngine):
    """Verify NormalizedResponse schema normalizes all fields into clean strings."""
    res = engine.execute_with_fallback("Quick prompt")
    assert isinstance(res.status, str)
    assert isinstance(res.complexity_tier, TaskComplexity)
    assert isinstance(res.primary_model, str)
    assert isinstance(res.executed_model, str)
    assert isinstance(res.fallback_used, bool)
    assert isinstance(res.response, str)
    assert isinstance(res.attempts, int)
    assert isinstance(res.latency_ms, float)
    assert isinstance(res.trace, tuple)


# --- 6. Micro-Kernel IoC Service Key Resolution (Rule 2 & Rule 49) ---


def test_ioc_service_resolution(service_context: ServiceContext):
    """Verify dynamic model router is resolvable via ServiceKey from IoC container."""
    svc = service_context.require(DYNAMIC_MODEL_ROUTER_SERVICE_KEY)
    assert svc is not None
    assert isinstance(svc, DynamicModelRouterService)

    # Test profile through service
    prof = svc.profile_complexity("Prove Fermat's last theorem using algebra")
    assert prof.tier == "complex"
    assert prof.reasoning_depth_detected is True

    # Test route through service
    route = svc.resolve_route("complex")
    assert route.provider_diversity_enforced is True
    assert route.primary.provider != route.fallback.provider

    # Test simulate through service
    sim = svc.simulate_execution(
        "Refactor database and prove concurrency invariant",
        failing_providers=[route.primary.provider],
    )
    assert sim.status == "fallback_success"
    assert sim.fallback_used is True


# --- 7. Plugin Validator Compliance (Rule 34 & Rule 38) ---


def test_plugin_validation_sync():
    """Verify dynamic_model_router plugin passes PluginValidator checks (Rule 34 & Rule 38)."""
    plugin_dir = _ws_root / "plugins" / "agent_orchestration" / "dynamic_model_router"
    assert plugin_dir.exists()

    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"


@pytest.mark.asyncio
async def test_plugin_lifecycle():
    """Verify plugin on_load registers DYNAMIC_MODEL_ROUTER_SERVICE_KEY in context."""
    ctx = ServiceContext()
    p = DynamicModelRouterPlugin()
    assert DYNAMIC_MODEL_ROUTER_SERVICE_KEY in p.provides

    await p.on_load(ctx)
    resolved = ctx.require(DYNAMIC_MODEL_ROUTER_SERVICE_KEY)
    assert resolved is p

    # Test entrypoint tool methods
    prof_dict = p.profile_prompt("Refactor code")
    assert prof_dict["tier"] == "complex"

    route_dict = p.resolve_routing("simple")
    assert route_dict["provider_diversity_enforced"] is True

    exec_dict = p.route_and_execute("Hello world")
    assert exec_dict["status"] in ("success", "fallback_success")


# --- 8. Headless Click CLI Seams (Rule 6, 10, 23) ---


def test_cli_profile():
    """Test 'harness router profile' CLI command."""
    runner = CliRunner()
    result = runner.invoke(model_router_group, ["profile", "Summarize this memo"])
    assert result.exit_code == 0
    assert "Prompt Complexity Profile:" in result.output
    assert "SIMPLE" in result.output


def test_cli_profile_json():
    """Test 'harness router profile --json-output' CLI command."""
    runner = CliRunner()
    result = runner.invoke(
        model_router_group,
        ["profile", "Refactor kernel and verify invariant", "--json-output"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["tier"] == "complex"
    assert data["reasoning_depth_detected"] is True


def test_cli_route():
    """Test 'harness router route' CLI command."""
    runner = CliRunner()
    result = runner.invoke(model_router_group, ["route", "--complexity", "complex"])
    assert result.exit_code == 0
    assert "Routing Resolution for 'COMPLEX':" in result.output
    assert "Provider Diversity: PASS" in result.output


def test_cli_simulate_fallback():
    """Test 'harness router simulate --fail-primary' CLI command."""
    runner = CliRunner()
    result = runner.invoke(
        model_router_group,
        ["simulate", "Evaluate SQL indexing strategy", "--fail-primary"],
    )
    assert result.exit_code == 0
    assert "Execution Simulation Result:" in result.output
    assert "Fallback Used:   True" in result.output


def test_cli_brief():
    """Test 'harness router brief' CLI command."""
    runner = CliRunner()
    result = runner.invoke(model_router_group, ["brief"])
    assert result.exit_code == 0
    assert "Interactive Visual Brief generated:" in result.output


# --- 9. Visual Brief File Generation ---


def test_generate_visual_brief(engine: DynamicModelRouterEngine, tmp_path: Path):
    """Verify HTML visual brief generates cleanly and contains Mermaid diagram."""
    out_file = tmp_path / "router_brief.html"
    dest = engine.generate_visual_brief(output_path=out_file)
    assert dest.exists()
    content = dest.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "mermaid" in content
    assert "Dynamic Model Router Telemetry" in content
    assert "Provider Diversity" in content
