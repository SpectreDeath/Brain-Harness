"""Tests for Domain 3: Prompt Benchmark plugin."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.prompt_benchmark import (
    PROMPT_BENCHMARK_KEY,
    ModelOutputEvalResult,
    PromptBenchmarkService,
    RegressionMatrixResult,
    TextSimilarityResult,
)
from plugins.memory_and_epistemics.prompt_benchmark.main import (
    PromptBenchmarkPlugin,
    evaluate_model_outputs,
    generate_regression_matrix,
    score_text_similarity_bleu_rouge,
)


@pytest.mark.unit
class TestPromptBenchmarkPlugin:
    def test_score_text_similarity_bleu_rouge(self) -> None:
        ref = "The quick brown fox jumps over the lazy dog"
        cand = "The fast brown fox jumps over a lazy dog"
        res = score_text_similarity_bleu_rouge(ref, cand)
        assert res["status"] == "ok"
        assert res["bleu_1"] > 0.6
        assert res["rouge_1_f1"] > 0.6

    def test_evaluate_model_outputs(self) -> None:
        test_cases = [
            {"id": 1, "output": "API Key created successfully", "expected_contains": ["API Key", "success"]},
            {"id": 2, "output": "System error 500", "expected_contains": ["success"], "must_not_contain": ["error"]},
        ]
        res = evaluate_model_outputs(test_cases)
        assert res["status"] == "ok"
        assert res["total_test_cases"] == 2
        assert res["passed_count"] == 1
        assert res["pass_rate"] == 0.5

    def test_generate_regression_matrix(self) -> None:
        runs = [
            {"model": "v1", "pass_rate": 0.80, "avg_latency": 1.5},
            {"model": "v2", "pass_rate": 0.95, "avg_latency": 0.9},
        ]
        res = generate_regression_matrix(runs)
        assert res["status"] == "ok"
        assert res["top_performer"]["model"] == "v2"

    @pytest.mark.asyncio
    async def test_prompt_benchmark_plugin_ioc_lifecycle(self) -> None:
        plugin = PromptBenchmarkPlugin()
        assert plugin.name == "plugin.prompt_benchmark"
        assert PROMPT_BENCHMARK_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(PROMPT_BENCHMARK_KEY)
        assert isinstance(service, PromptBenchmarkService)

        sim_res = service.score_text_similarity("Ground truth answer", "Candidate model answer")
        assert isinstance(sim_res, TextSimilarityResult)
        assert sim_res.status == "ok"
        assert sim_res.reference_tokens > 0

        eval_res = service.evaluate_model_outputs([{"output": "All green", "expected_contains": ["green"]}])
        assert isinstance(eval_res, ModelOutputEvalResult)
        assert eval_res.passed_count == 1

        reg_res = service.generate_regression_matrix([{"model": "gpt-4o", "pass_rate": 1.0, "avg_latency": 0.5}])
        assert isinstance(reg_res, RegressionMatrixResult)
        assert reg_res.total_runs == 1

        await plugin.on_disable()
        await plugin.on_unload()
