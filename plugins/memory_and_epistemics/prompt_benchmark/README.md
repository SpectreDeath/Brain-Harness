# plugin.prompt_benchmark (v1.0.0)

LLM output evaluation, BLEU/ROUGE ngram similarity scoring, and regression benchmark suite

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/prompt_benchmark` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.prompt_benchmark` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `score_text_similarity_bleu_rouge` | `(reference, candidate)` | Compute token precision (BLEU-1, BLEU-2) and recall/F1 (ROUGE-1, ROUGE-L) between reference and candidate text |
| `evaluate_model_outputs` | `(test_cases)` | Run automated evaluation over a batch of prompt test cases against criteria (exact match, contains keywords, regex, length) |
| `generate_regression_matrix` | `(runs)` | Compare benchmark scores across multiple prompt versions or model runs |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Prompt benchmark, BLEU/ROUGE ngram similarity, and model evaluation plugin.

#### Classes

- `class PromptBenchmarkPlugin` — Harness Plugin providing prompt evaluation, similarity benchmarking, and model regression testing.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def score_text_similarity(reference, candidate) -> TextSimilarityResult`
  - `def evaluate_model_outputs(test_cases) -> ModelOutputEvalResult`
  - `def generate_regression_matrix(runs) -> RegressionMatrixResult`


#### Functions

- `def score_text_similarity_bleu_rouge(reference, candidate) -> dict[str, Any]` — Calculate BLEU-1, BLEU-2, and ROUGE-1 F1 scores.
- `def evaluate_model_outputs(test_cases) -> dict[str, Any]` — Evaluate candidate outputs against test assertions.
- `def generate_regression_matrix(runs) -> dict[str, Any]` — Summarize and rank benchmark runs.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.prompt_benchmark.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
