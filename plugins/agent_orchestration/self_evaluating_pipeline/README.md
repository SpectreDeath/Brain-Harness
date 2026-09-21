# Self-Evaluating AI Pipeline Plugin

The `plugin.self_evaluating_pipeline` plugin implements an opinionated, production-grade 3-layer LLM quality evaluation funnel, golden regression suites, and paired Student's $t$-test statistical deployment gating based on Jude Otine's 2026 foundational literature (*How to Build a Self-Evaluating AI System*, freeCodeCamp).

## Architecture & Seams

- **Service Key**: `SELF_EVALUATING_PIPELINE_SERVICE_KEY` (`service.self_evaluating_pipeline`)
- **Protocol**: `SelfEvaluatingPipelineService` in `harness.services.self_evaluating_pipeline`
- **Domain Engine**: `SelfEvaluatingPipelineEngine` in `.agents/skills/self-evaluating-ai-pipeline/scripts/self_evaluating_pipeline_engine.py`

## Five-Stage Pipeline

```
[1. Deterministic Guardrails] -> [2. Anchored LLM Judge] -> [3. Human Calibration] -> [4. Golden Regression Suite] -> [5. Statistical Gate (Paired t-Test)]
```

1. **Layer 1: Deterministic Guardrails (<1ms, $0 cost)**:
   - Schema and syntax validation (JSON loads, XML).
   - Minimum and maximum length bounds ($[10, 5000]$ chars).
   - Unauthorized and hallucinated URL regex scraping.
   - Refusal phrase scanning (*"as an ai"*, *"i cannot"*).
   - Domain Python AST syntax parsing.
2. **Layer 2: Semantic LLM-as-Judge**:
   - Discrete 1-to-5 anchored rubric (1: Irrelevant/Harmful, 2: Major errors, 3: Partially correct, 4: Accurate/Helpful, 5: Comprehensive/Flawless).
   - 3-judge median consensus neutralizing single-run stochastic variance.
3. **Layer 3: Human Calibration Loop**:
   - Cohen's Kappa ($\kappa = \frac{P_o - P_e}{1 - P_e}$) inter-annotator agreement asserting $\kappa > 0.6$.
   - Monthly judge drift tracking asserting Mean Absolute Deviation $\le 0.5$ points.
4. **Layer 4: CI/CD Golden Regression Suite**:
   - Balanced 50-100 edge-case test suite across difficulty tiers.
   - Zero-drop incident ingestion converting production defects into permanent test cases.
5. **Layer 5: Paired Student's t-Test Deployment Gate**:
   - Compares pre-change and post-change scores on identical test cases.
   - Authorizes deployment if and only if $p < 0.05$ AND $\bar{X}_{\text{after}} - \bar{X}_{\text{before}} > 0$.
   - Blocks noisy or regressive releases.

## CLI Usage

```powershell
# Layer 1 deterministic pre-flight check
harness eval layer1 "{"answer": 42}" --schema json

# Layer 2 semantic judge evaluation
harness eval judge "Explain binary search" "Binary search runs in O(log n)..."

# Layer 3 human inter-annotator agreement
harness eval kappa annotations.json

# Layer 4 golden regression suite
harness eval regression --golden golden_dataset.json

# Stage 5 paired t-test release gate
harness eval gate --before scores_v1.json --after scores_v2.json --alpha 0.05
```
