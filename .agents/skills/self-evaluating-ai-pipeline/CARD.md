┌─────────────────────────────────────────────────────────────┐
│ SKILL: self-evaluating-ai-pipeline                          │
├─────────────────────────────────────────────────────────────┤
│ DESCRIPTION: 3-Layer LLM evaluation, anchored judges, human │
│ calibration, golden regression suites, & statistical gating │
└─────────────────────────────────────────────────────────────┘

## Stage Progression Matrix

| Stage | Focus Area | Core Mechanism | Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Deterministic** | Rule-Based Checks | JSON validity, length, URLs, refusal | <1ms latency, $0 cost, 100% pass |
| **2. LLM Judge** | Semantic Quality | Anchored 1-5 rubric, JSON, consensus | Temp=0.0, 3-judge median score |
| **3. Human Loop** | Calibration & Drift | Terminal JSONL annotation, Cohen's K | Kappa > 0.6, judge drift < 0.5 pts |
| **4. Regression** | Golden Dataset | 50-100 edge cases, category balance | Pass rate >= threshold, zero Layer 1 fail |
| **5. Statistical** | Deployment Gate | Paired Student's t-test (scipy.stats) | p-value < 0.05 AND mean diff > 0 |

---

## Three Pillars Cheat Sheet

### Pillar 1: Layer 1 Deterministic Sanity Guardrails
- **Cost & Speed**: 0 API tokens, executed in microseconds on every request.
- **Core Checks**: JSON loads parsing, length $[10, 5000]$ chars, URL regex scraping, canned refusal phrase detection.
- **Domain Extensions**: AST syntax validation, SQL linting, email header structure.

### Pillar 2: Layer 2 Anchored LLM-as-Judge
- **Anchor Invariant**: Score 1 (Irrelevant/Harmful), Score 2 (Major errors), Score 3 (Partially correct), Score 4 (Helpful/Minor issues), Score 5 (Comprehensive/Accurate).
- **Format Invariant**: Mandatory JSON response `{"score": <int>, "reasoning": "<str>"}`.
- **Consensus Invariant**: Run 3 independent evaluations and return median for CI/CD gates.

### Pillar 3: Layer 3 & Statistical Verification
- **Human Calibration**: Collect annotations in `annotations.jsonl`. Assert Cohen's Kappa $\kappa > 0.6$.
- **Golden Dataset**: Maintain 50-100 versioned edge cases; feed every production bug into the golden suite.
- **Statistical Gate**: Deploy only when paired $t$-test yields $p < 0.05$ with positive mean improvement.

---

## Verification Checklist

- [ ] Frontmatter description strictly bounded between 100 and 350 characters with action verbs and negative boundary.
- [ ] Layer 1 deterministic evaluator implemented with schema, length, link, and refusal checks.
- [ ] LLM judge prompt bakes concrete 1-5 observable anchor descriptions and temperature 0.0 into prompt.
- [ ] Judge response enforced as structured JSON with parsed integer score and explanation string.
- [ ] Cohen's Kappa calculation implemented for human annotators with $K > 0.6$ acceptance threshold.
- [ ] Golden dataset established with 50-100 balanced cases across difficulty tiers and categories.
- [ ] Paired Student's $t$-test gating blocks releases with $p \ge 0.05$ or non-positive mean difference.
- [ ] Companion `CARD.md` utilizes single-pipe borders (`│`) and exact `SKILL:` header.