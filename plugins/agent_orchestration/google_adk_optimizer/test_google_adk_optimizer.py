"""Tests for Google ADK Optimizer Plugin."""

import pytest
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.google_adk_optimizer.main import (
    GOOGLE_ADK_OPTIMIZER_SERVICE_KEY,
    GoogleAdkOptimizerPlugin,
)

@pytest.mark.asyncio
async def test_google_adk_optimizer_tools():
    ctx = ServiceContext()
    p = GoogleAdkOptimizerPlugin()
    await p.enable(ctx)

    service = ctx.require(GOOGLE_ADK_OPTIMIZER_SERVICE_KEY)
    assert service is not None

    # Test GEPA optimization
    res = service.gepa_optimize_prompt("You are a helpful assistant.", iterations=2)
    assert res["status"] == "success"
    assert res["final_score"] > res["baseline_score"]
    assert len(res["trajectory"]) == 2

    # Test scenario evaluation
    eval_res = service.evaluate_agent("test_agent")
    assert eval_res["status"] == "success"
    assert eval_res["pass_rate"] == 1.0

    # Test trajectory metrics
    score = service.score_metrics([{"role": "user", "content": "hello"}])
    assert score["status"] == "success"
    assert score["composite_score"] >= 0.9

    await p.disable(ctx)
