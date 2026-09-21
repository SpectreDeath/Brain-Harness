---
name: self-evaluating-ai-pipeline
description: Architect, implement, and automate 3-layer LLM evaluation pipelines (deterministic checks, anchored LLM-as-judge scoring, and human calibration) with golden regression suites and paired t-test statistical significance gating. Do not use for deterministic pure-function unit tests or ungrounded single-turn prompt drafting.
---

# Self-Evaluating AI Pipeline: Automated LLM Quality Architecture

The `self-evaluating-ai-pipeline` skill provides the definitive engineering framework for evaluating non-deterministic Large Language Model applications. Traditional software unit tests (`assert output == expected`) fail because LLM outputs vary across runs. This skill implements an opinionated, production-grade 3-layer evaluation funnel, regression suites with golden datasets, and statistical significance testing.

Synthesized from Jude Otine's foundational literature (*How to Build a Self-Evaluating AI System*, freeCodeCamp, 2026), this pipeline enforces the **Shu-Ha-Ri framework principle**: moving from rigid deterministic checks to calibrated semantic judges, golden regression suites, visual briefing, and rigorous statistical deployment gating.

```
[1. Deterministic Guardrails] -> [2. Anchored LLM Judge] -> [3. Human Calibration] -> [4. Golden Regression Suite] -> [5. The Visual Brief & Mandatory Checkpoint Gate]
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage reference matrix, and quality checklist.
Consult [agent-harness-architect](../agent-harness-architect/SKILL.md) for runtime loop containment and [crafting-skills](../crafting-skills/SKILL.md) for skill authoring standards.

---

## 1. Deterministic Guardrail Configuration (Layer 1)

Deploy zero-cost, sub-millisecond rule-based sanity checks on 100% of LLM outputs before calling downstream evaluators or users. Layer 1 catches approximately 30% of defective outputs for $0 in API costs.

1. **Schema & Syntax Validation**:
   - Verify output validity when structured output is expected (e.g. `json.loads()`, YAML, XML, SQL).
   - If invalid, immediately trigger in-flight self-repair or return a structural failure.
2. **Length Boundary Verification**:
   - Enforce minimum and maximum character/token bounds (e.g., $[10, 5000]$ chars).
   - Catch truncated generations, infinite token loops, or blank/whitespace responses.
3. **Hallucinated Link Detection**:
   - Extract URLs using regex (`https?://[^\s)[\]{}"'<>]+`).
   - Match extracted URLs against an authorized domain whitelist or verify DNS resolution. Flag unverified links as hallucinations.
4. **Refusal Phrase Detection**:
   - Scan for canned refusal strings (*"as an ai"*, *"i cannot"*, *"i'm unable to"*, *"i don't have access"*).
   - Flag unprompted refusals on benign operational tasks.
5. **Domain-Specific Linters**:
   - Attach fast domain linters (e.g. Python AST syntax check, SQL query syntax parsing, email greeting/signature verification).

> **Completion criterion**: `DeterministicEvaluator` deployed with schema, length, link, refusal, and domain checks running synchronously in <1ms with zero LLM API calls.

---

## 2. Anchored Rubric & LLM Judge Synthesis (Layer 2)

Automate semantic evaluation using an isolated LLM judge (e.g. `gpt-4o-mini`, `gemini-1.5-flash`) scoring responses against concrete, observable rubrics.

1. **Concrete Observable Anchor Rubrics**:
   - Never ask a judge to "rate this 1 to 10" without definitions.
   - Anchor each integer on a 1-to-5 scale to observable structural facts:
     - **Score 1**: Completely irrelevant, incorrect, harmful, or unresponsive.
     - **Score 2**: On-topic but contains major factual errors, hallucinated concepts, or critical omissions.
     - **Score 3**: Partially correct; core points present but misses important nuances or structure.
     - **Score 4**: Fully accurate and helpful; directly answers prompt with only minor aesthetic issues.
     - **Score 5**: Comprehensive, flawless accuracy, well-structured, and directly addresses the user's intent.
2. **Constrained JSON Judge Protocol**:
   - Set temperature to 0.0 to eliminate judge creativity.
   - Mandate strict JSON schema output: `{"score": <int 1-5>, "reasoning": "<2-3 sentences>"}`.
   - Bake the complete rubric text directly into the system prompt for every evaluation call.
3. **Multi-Judge Median Consensus**:
   - For sensitive regression gates or high-variance prompts, execute 3 independent judge calls.
   - Take the median score (`int(np.median(scores))`) to neutralize stochastic outlier runs.

> **Completion criterion**: `LLMJudge` configured with observable 1-5 anchors, temperature 0.0, strict JSON schema output, and optional 3-judge median consensus.

---

## 3. Ground Truth Human Calibration (Layer 3)

Automated LLM judges have blind spots around tone, domain jargon, and superficial correctness. Layer 3 maintains alignment between automated scoring and human judgment.

1. **Lightweight Annotation Collector**:
   - Deploy a minimalist CLI or web annotation tool presenting input question and model response to human evaluators.
   - Record score (1-5), annotator ID, and optional qualitative feedback to append-only JSONL files (`annotations.jsonl`).
2. **Inter-Annotator Agreement (Cohen's Kappa)**:
   - Measure statistical agreement between human reviewers corrected for chance:
     $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   - **Gating Threshold**: Assert $\kappa > 0.6$. If $\kappa \le 0.6$, the rubric definitions are ambiguous; halt evaluation and refine rubric anchors with concrete examples.
3. **Automated Judge Drift Audit**:
   - Maintain a benchmark calibration set of 20-30 human-annotated examples.
   - Re-run the automated LLM judge monthly against this set.
   - If mean absolute deviation between judge scores and human scores exceeds 0.5 points, trigger rubric recalibration.

> **Completion criterion**: Human annotation collection active in JSONL format, Cohen's Kappa verified $> 0.6$, and monthly judge drift tracking established.

---

## 4. Golden Dataset & CI/CD Regression Suite

Prevent prompt changes, model updates, or retrieval modifications from introducing silent regressions across previously working edge cases.

1. **Curate Representative Golden Dataset**:
   - Build a version-controlled dataset of 50 to 100 realistic test examples (`golden_dataset.json`).
   - Balance across domain categories and difficulty tiers ("easy", "medium", "hard").
   - Include edge cases that previously triggered production failures.
2. **Incident Ingestion Flywheel**:
   - Establish a zero-drop rule: every production incident or user bug report must be converted into a permanent golden test case.
3. **Automated Regression Pipeline**:
   - Execute Layer 1 deterministic checks and Layer 2 LLM judge across all golden examples.
   - Assert zero Layer 1 failures and average composite score above threshold (e.g. $\ge 3.5$).
   - Record run metadata (run ID, timestamp, model version, prompt hash, pass rate, failure details) in versioned audit logs.

> **Completion criterion**: Golden dataset populated with 50-100 balanced cases, CI/CD regression pipeline executing on every prompt/model change, and incident ingestion active.

---

## 5. The Visual Brief & Mandatory Checkpoint Gate

Synthesize evaluation results into an interactive visual dashboard and enforce an unyielding statistical release gate before deploying prompt modifications, model migrations, or retrieval changes to production.

### The Visual Brief

Generate a standalone interactive HTML visual brief in `%TEMP%/self-eval-brief-<timestamp>.html` summarizing the regression run:
1. **Visual Telemetry**:
   - Render a dark-themed (`#0d1117`) dashboard loading Tailwind CSS and Mermaid.js via CDN.
   - Embed a **Score Distribution & Regression Delta** chart comparing pre-change vs post-change scores across all golden categories.
   - Render a **Layer 1 Failure Analysis Matrix** detailing any deterministic catches.
   - Display the **Judge Reasoning Transcript** for all examples scoring below threshold ($< 3.5$).
2. **Delivery**:
   - Output the clickable absolute file path to the user/operator for rapid visual inspection.

### Mandatory Checkpoint Gate

Enforce an automated approval gate with `RequestFeedback: true` in CI/CD before any production deployment:
1. **Statistical Significance Testing (Paired Student's t-Test)**:
   - Compute paired $t$-test statistic and $p$-value using `scipy.stats.ttest_rel(scores_after, scores_before)` on identical golden test cases.
   - **Gating Invariant**:
     $$p < 0.05 \quad \text{AND} \quad (\bar{X}_{\text{after}} - \bar{X}_{\text{before}}) > 0$$
2. **Gating Decision Rule**:
   - **PASS**: $p < 0.05$ and Mean Difference $> 0 \implies$ Release approved.
   - **BLOCK (Noise)**: $p \ge 0.05 \implies$ Release blocked; improvement is indistinguishable from random noise.
   - **BLOCK (Regression)**: Mean Difference $\le 0 \implies$ Release blocked; system has regressed.

> **Completion criterion**: Interactive HTML visual brief generated in `%TEMP%`, and deployment blocked until statistical significance ($p < 0.05$) passes the Mandatory Checkpoint Gate.

---

## Anti-Patterns

- **Big-Bang Eval Syndrome** — Delaying evaluation until complex multi-judge and human rating platforms are built instead of deploying Layer 1 deterministic checks on Day 1.
- **Vibe-Based Judging** — Asking an LLM judge to "rate this from 1 to 10" without discrete, observable anchor definitions for each score.
- **Fragile Output Parsing** — Allowing judge models to return free-form prose and attempting regex scraping rather than mandating strict JSON schema output.
- **The Expert Blindspot** — Relying exclusively on automated LLM judges without human calibration loops, missing toxic tone, domain jargon, or superficial correctness.
- **Regression Blindness** — Tweaking a prompt to resolve one visible user defect without re-running the complete golden dataset to verify adjacent capabilities.
- **Noise Chasing** — Deploying prompt modifications or temperature adjustments based on small average score increases without paired $t$-test statistical significance ($p < 0.05$).