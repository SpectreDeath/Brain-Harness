"""Prompt Benchmark and Model Evaluation service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class TextSimilarityResult(BaseModel):
    """Result of computing BLEU and ROUGE text similarities."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    reference_tokens: int = Field(default=0, description="Token count of reference string")
    candidate_tokens: int = Field(default=0, description="Token count of candidate string")
    bleu_1: float = Field(default=0.0, description="BLEU-1 unigram precision")
    bleu_2: float = Field(default=0.0, description="BLEU-2 bigram precision")
    rouge_1_recall: float = Field(default=0.0, description="ROUGE-1 unigram recall")
    rouge_1_f1: float = Field(default=0.0, description="ROUGE-1 harmonic F1 score")
    error: str | None = Field(default=None, description="Error explanation if scoring failed")


class ModelOutputEvalResult(BaseModel):
    """Result of evaluating candidate model outputs against expected test assertions."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    total_test_cases: int = Field(default=0, description="Total test cases executed")
    passed_count: int = Field(default=0, description="Count of passed test cases")
    pass_rate: float = Field(default=1.0, description="Pass rate ratio between 0.0 and 1.0")
    evaluations: list[dict[str, Any]] = Field(default_factory=list, description="Per-case evaluation outcomes")
    error: str | None = Field(default=None, description="Error explanation if evaluation failed")


class RegressionMatrixResult(BaseModel):
    """Result of summarizing and ranking benchmark execution runs."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    total_runs: int = Field(default=0, description="Total benchmark runs evaluated")
    top_performer: dict[str, Any] | None = Field(default=None, description="Highest ranking model run")
    ranking: list[dict[str, Any]] = Field(default_factory=list, description="Ordered ranking of all runs")
    error: str | None = Field(default=None, description="Error explanation if generation failed")


@runtime_checkable
class PromptBenchmarkService(Protocol):
    """Protocol for prompt similarity benchmarking, model assertion testing, and regression matrices."""

    def score_text_similarity(
        self,
        reference: str,
        candidate: str,
    ) -> TextSimilarityResult:
        """Calculate BLEU-1, BLEU-2, and ROUGE-1 F1 scores between reference and candidate."""
        ...

    def evaluate_model_outputs(
        self,
        test_cases: list[dict[str, Any]],
    ) -> ModelOutputEvalResult:
        """Evaluate candidate outputs against test assertions (expected keywords / forbidden terms)."""
        ...

    def generate_regression_matrix(
        self,
        runs: list[dict[str, Any]],
    ) -> RegressionMatrixResult:
        """Summarize and rank benchmark runs based on pass rates and average latency."""
        ...


PROMPT_BENCHMARK_KEY: ServiceKey[PromptBenchmarkService] = ServiceKey("service.prompt_benchmark")
