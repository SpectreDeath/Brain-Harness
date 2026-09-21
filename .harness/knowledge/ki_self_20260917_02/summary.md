# Knowledge Item: Three-Layer LLM Evaluation Architecture, Golden Regression Suites, and Paired T-Test Significance Gating

## Epistemic Distillation

### 1. The LLM Testing Breakdown & The Layered Paradigm
Traditional software verification relies on deterministic assertions (`assert output == expected`). Because Large Language Models generate non-deterministic surface text across invocations, exact equality assertions fail. Attempting to compensate with superficial fuzzy matching fails to catch subtle hallucinations, wrong answers phrased persuasively, or regressions in adjacent capabilities.

Production AI systems resolve this via a **cascading 3-layer evaluation funnel**:
1. **Layer 1: Deterministic Checks** — Instantaneous (<1ms), zero-token, rule-based sanity checks (JSON validation, bounds checking, URL extraction, refusal detection) executed on 100% of outputs.
2. **Layer 2: Semantic LLM-as-Judge** — Automated semantic scoring via an isolated evaluation model with concrete, observable 1-to-5 anchor descriptions, temperature 0.0, constrained JSON outputs, and optional 3-judge median consensus.
3. **Layer 3: Human Evaluation Loops** — Periodic ground-truth calibration using lightweight JSONL annotation interfaces to measure inter-annotator agreement (Cohen's Kappa $K > 0.6$) and audit automated judge drift.

---

### 2. Layer 1: Deterministic Sanity Guardrails
Layer 1 acts as a zero-cost pre-flight filter that catches approximately 30% of defective production outputs before wasting downstream compute tokens:
- **Structural Integrity**: Syntax validation for expected structured formats (JSON, YAML, XML, SQL).
- **Length Boundaries**: Enforcement of floor and ceiling token/character limits (e.g. $[10, 5000]$ chars) to catch truncated responses or infinite repetition loops.
- **Hallucinated URL Regex**: Extracting URLs (`https?://[^\s]+`) and flagging unauthorized or fabricated domain references.
- **Refusal String Scanning**: Detecting unnecessary safety refusals or canned model hedging (*"as an AI language model..."*).
- **Domain Linting**: Invoking syntax checkers or AST parsers for programming languages or tabular schemas.

---

### 3. Layer 2: LLM-as-Judge & The Anchored Rubric Invariant
Unanchored prompts asking a judge model to "rate this from 1 to 10" produce high-variance, drifting scores. Reliable automated semantic judging enforces three structural invariants:
1. **Observable Anchor Descriptions**: Every score level (1 through 5) must describe objective, observable criteria rather than subjective impressions:
   - **Score 1**: Irrelevant, completely incorrect, or harmful.
   - **Score 2**: On-topic but contains major factual errors or critical omissions.
   - **Score 3**: Partially correct with core facts present, but misses important nuances.
   - **Score 4**: Accurate, helpful, and directly addresses prompt with minor omissions.
   - **Score 5**: Comprehensive, fully accurate, structured, and directly responsive.
2. **Constrained JSON Protocol**: Judge prompts strictly mandate JSON responses (`{"score": <int>, "reasoning": "<str>"}`), parsed without regex heuristics.
3. **Multi-Judge Median Consensus**: For high-stakes regression gates in CI/CD, the evaluator executes 3 independent judge calls and computes the median score, neutralizing single-run stochastic variance.

---

### 4. Layer 3: Human Calibration & Inter-Annotator Agreement
Automated judges suffer from blindspots regarding tone, audience-appropriate technical jargon, and deceptive correctness. Layer 3 maintains calibration between automated scoring and real human judgment:
- **Lightweight Annotation**: Terminal or web annotation tools recording question, response, annotator ID, score (1-5), and qualitative notes to append-only JSONL files.
- **Cohen's Kappa Metric**: Measuring agreement between human raters corrected for chance:
  $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
  where $P_o$ is observed agreement and $P_e$ is expected chance agreement.
  - $\kappa > 0.8$: Near perfect agreement.
  - $0.6 < \kappa \le 0.8$: Substantial agreement (minimum production acceptance threshold).
  - $\kappa \le 0.6$: Inadequate rubric. Annotators disagree on definitions; rubric anchors must be iterated with concrete examples before resuming evaluation.
- **Judge Drift Audit**: Monthly re-evaluation of 20–30 human-scored benchmark cases. If the automated judge's average deviation from human scores exceeds 0.5 points, the judge prompt and rubric anchors require immediate recalibration.

---

### 5. Regression Testing Pipeline & Golden Datasets
To prevent prompt modifications or model version bumps from introducing silent regressions:
- **Curated Golden Dataset**: A version-controlled corpus of 50 to 100 representative examples distributed across categories and difficulty tiers ("easy", "medium", "hard").
- **Incident Ingestion Flywheel**: Every production defect, bug report, or edge-case failure is immediately converted into a permanent test case in the golden dataset.
- **Automated CI/CD Gate**: The regression pipeline executes Layer 1 and Layer 2 evaluations across the full golden suite, asserting zero deterministic failures and an average composite score above threshold (e.g. $\ge 3.5$).

---

### 6. Statistical Significance Gating (Paired Student's t-Test)
Marginal score increases (e.g. $3.8 \to 4.1$) frequently represent stochastic sampling noise rather than true architectural improvements. To guarantee deployment safety:
- Execute a **paired Student's $t$-test** (`scipy.stats.ttest_rel`) comparing pre-change scores ($X_{\text{before}}$) and post-change scores ($X_{\text{after}}$) on identical golden examples.
- **Gating Invariant**: A change is permitted to deploy **if and only if**:
  $$p < 0.05 \quad \text{AND} \quad (\bar{X}_{\text{after}} - \bar{X}_{\text{before}}) > 0$$
- If $p \ge 0.05$, the observed difference fails to reject the null hypothesis; deployment is blocked as statistically unverified noise.

---

### 7. Key Anti-Patterns & Defensive Invariants
- **Big-Bang Eval Trap**: Attempting to design complex human rating platforms before shipping Layer 1 deterministic filters. *Invariant: Ship deterministic checks on Day 1.*
- **Vibe-Based Judging**: Asking LLM judges for arbitrary scores without anchor definitions. *Invariant: Discrete 1-to-5 scale anchored to observable facts.*
- **Regression Blindness**: Fixing a prompt for a single user complaint without re-running the full golden dataset. *Invariant: Continuous CI/CD regression gating.*
- **Noise Chasing**: Deploying prompt changes based on small average score upticks. *Invariant: Gated paired $t$-test with $p < 0.05$.*