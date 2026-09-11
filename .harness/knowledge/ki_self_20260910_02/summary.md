## Dual-Tier Skill Prompt Budgeting & Zero-Fork Configuration Governance

### Problem
In large-scale agent catalogs (40+ skills):
1. **Catalog Prompt Bloat**: Lengthy narrative frontmatter descriptions injected into Tier 1 agent system prompts waste context tokens on every planning step.
2. **Missing Negative Boundaries**: Without explicit negative routing constraints ("Do not use for..."), agent routers misroute ambiguous user queries to tangential skills.
3. **Hardcoded Operational Budgets**: Specifying timeouts, max retries, or token ceilings inside Python code causes brittle forks when deploying across different environments (local dev vs. CI vs. production).

### Solution Pattern
1. **Dual-Tier Description Calibration**: Bound skill descriptions between 100 and 350 characters (calibrated to ~200–250 characters) with front-loaded active verbs and explicit negative boundaries ("Do not use for...").
2. **Zero-Fork Baseline Budgets**: Co-locate a `config.default.yaml` alongside each skill/plugin defining baseline execution timeouts, token budgets, and retry limits.
3. **Continuous Evaluation Verification**: Run Google 2x2 continuous evals (`eval_uplift_calculator.py`) to empirically verify accuracy uplift and token savings (achieving `DOMINANT_UPLIFT`).

### Architectural Rules Enforced
- **Rule 11**: Agent instruction file hygiene and negative boundaries.
- **Rule 44**: Dual-tier catalog budget and zero-fork configuration invariant.
