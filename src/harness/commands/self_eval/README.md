# Self-Evaluating Pipeline CLI Commands

The `harness.commands.self_eval` package provides headless Click CLI inspection and orchestration commands for the 3-layer self-evaluating AI evaluation pipeline (`self-evaluating-ai-pipeline`).

---

## Architectural Invariants

- **Click Group Consolidation (`Rule 6`)**: The command group (`eval_group`) is declared in a single consolidated block to prevent command collision and test regressions.
- **Headless Introspection Seams (`Rule 10`)**: All evaluation commands provide machine-readable output flags (`--json`) for automated CI/CD release gating.
- **3-Tier Continuous Evaluation**: Supports Layer 1 deterministic assertions, Layer 2 anchored LLM-as-judge scoring, and Layer 3 Cohen's Kappa agreement and judge drift tracking.

---

## Module & Symbol Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`group.py`](group.py) | `eval_group` | Master Click group consolidating the self-evaluation CLI suite. |
| [`layer1.py`](layer1.py) | `layer1_cmd` | Layer 1 deterministic validation CLI command checking regex, schema, and length. |
| [`judge.py`](judge.py) | `judge_cmd` | Layer 2 anchored rubric-based judge command scoring outputs with reasoning. |
| [`agreement.py`](agreement.py) | `kappa_cmd`, `drift_cmd` | Layer 3 inter-annotator Cohen's Kappa agreement and historical judge drift audits. |
| [`regression.py`](regression.py) | `regression_cmd`, `gate_cmd` | Layer 4 golden regression harness and Layer 5 paired t-test statistical significance gate. |
| [`brief.py`](brief.py) | `brief_cmd` | Visual HTML brief generation command rendering evaluation distribution charts. |
| [`brief_adapter.py`](brief_adapter.py) | `generate_visual_brief_via_engine` | Helper adapter transforming raw evaluation datasets into visual diagram schemas. |
| [`engine_adapter.py`](engine_adapter.py) | `SelfEvaluatingPipelineEngineAdapter` | Protocol implementation adapter bridging CLI commands to evaluation engines. |
| [`resolver.py`](resolver.py) | `get_self_eval_service` | IoC container single-seam resolver locating active evaluation services. |

---

## CLI Command Usage

### Layer 1 Deterministic Sanity Checks
```bash
python -m harness.cli eval layer1 --input response.json --schema-file schema.json --json
```

### Layer 2 Anchored Semantic Judging
```bash
python -m harness.cli eval judge --prompt "Explain photosynthesis" --response response.txt --rubric rubric.yaml --json
```

### Layer 3 Inter-Rater Agreement Audit
```bash
python -m harness.cli eval kappa --annotations-file annotations.json --min-kappa 0.70 --json
```

