# Uncertainty-Aware Pipeline CLI Commands

The `harness.commands.uncertainty` package provides headless Click CLI inspection and execution commands for the 3-layer Uncertainty-Aware AI and RAG pipeline (`uncertainty-aware-ai-architect`).

---

## Architectural Invariants

- **Click Group Consolidation (`Rule 6`)**: Command groups (`uncertainty_group`) are consolidated in a single co-located declaration block to prevent subcommand shadowing.
- **Headless Introspection Seams (`Rule 10`)**: All pipeline stages emit deterministic JSON payloads (`--json`) alongside human-readable terminal output.
- **3-Layer Deterministic Boundaries**: Evaluates Layer 1 semantic domain gating, Layer 2 retrieval relevance scoring, and Layer 3 logprob entropy calculations.

---

## Module & Symbol Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`group.py`](group.py) | `uncertainty_group` | Top-level Click group consolidating all uncertainty CLI commands. |
| [`gate.py`](gate.py) | `gate_cmd` | Layer 1 semantic domain gating CLI command checking input boundaries. |
| [`retrieval.py`](retrieval.py) | `retrieval_cmd` | Layer 2 retrieval quality scoring command auditing RAG document context. |
| [`logprobs.py`](logprobs.py) | `logprobs_cmd` | Layer 3 token logprob and perplexity entropy analysis command. |
| [`pipeline.py`](pipeline.py) | `pipeline_cmd` | End-to-end 3-layer request interception pipeline execution command. |
| [`calibrate.py`](calibrate.py) | `calibrate_cmd` | Empirical threshold calibration and documentation debt cluster mining command. |
| [`brief.py`](brief.py) | `brief_cmd` | Standalone interactive HTML visual brief generation command. |
| [`resolver.py`](resolver.py) | `get_uncertainty_service`, `resolve_uncertainty_service` | IoC container single-seam resolution helpers for `UncertaintyGuardService`. |
| [`adapter.py`](adapter.py) | `UncertaintyEngineAdapter` | Fallback engine adapter bridging CLI invocations to underlying domain algorithms. |
| [`converters.py`](converters.py) | `to_boundary_report`, `to_retrieval_report`, `to_logprob_report` | Conversion routines formatting engine diagnostics into standardized report schemas. |

---

## CLI Command Usage

### Layer 1 Semantic Domain Gate
```bash
python -m harness.cli uncertainty gate --query "Explain the cell mitosis stages" --domain "biology" --json
```

### Layer 2 Retrieval Relevance Scoring
```bash
python -m harness.cli uncertainty retrieval --query "RNA polymerase" --context-file context.txt --min-relevance 0.75 --json
```

### End-to-End Pipeline Evaluation
```bash
python -m harness.cli uncertainty pipeline --query "Analyze genome sequencing results" --json
```

