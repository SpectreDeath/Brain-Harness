"""Tests for Google Tunix Post-Training Plugin."""

import pytest
from harness.kernel.context import ServiceContext
from plugins.machine_learning.google_tunix_posttraining.main import (
    GOOGLE_TUNIX_POSTTRAINING_SERVICE_KEY,
    GoogleTunixPosttrainingPlugin,
)

@pytest.mark.asyncio
async def test_google_tunix_posttraining_tools():
    ctx = ServiceContext()
    p = GoogleTunixPosttrainingPlugin()
    await p.enable(ctx)

    service = ctx.require(GOOGLE_TUNIX_POSTTRAINING_SERVICE_KEY)
    assert service is not None

    # Test inspect_config for GRPO
    cfg = service.inspect_config("grpo")
    assert cfg["status"] == "success"
    assert "rl" in cfg["config"]
    assert cfg["config"]["rl"]["algorithm"] == "GRPO"

    # Test launch_grpo dry-run
    res = service.launch_grpo(cfg["config"], dry_run=True, num_steps=5)
    assert res["status"] == "success"
    assert res["metrics"]["final_policy_loss"] < res["metrics"]["initial_policy_loss"]

    # Test launch_peft
    peft_res = service.launch_peft(cfg["config"], lora_rank=16, dry_run=True)
    assert peft_res["status"] == "success"

    # Test math reward computation
    sample_text = "<thought>Solving 2+2=4</thought> Therefore the answer is \\boxed{4}."
    reward = service.compute_math_reward(sample_text, "4", format_check=True)
    assert reward["status"] == "success"
    assert reward["correct"] is True
    assert reward["total_reward"] == 1.0

    await p.disable(ctx)
