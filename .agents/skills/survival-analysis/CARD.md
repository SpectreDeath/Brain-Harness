# Skill Summary Card: `survival-analysis`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        survival-analysis                         │
│ Category:    statistics / time-to-event                │
│ Invocation:  /survival-analysis                        │
│ Trigger:     "survival analysis", "kaplan meier",      │
│              "cox proportional hazards", "hazard ratio"│
│              "schoenfeld residuals", "log-rank test"   │
│ Version:     1.0.0                                     │
│ Requires:    "crafting-skills"                         │
│ Provides:    "survival_modeling"                       │
├────────────────────────────────────────────────────────┤
│ Target:      Estimate survival curves, fit Cox PH,     │
│              diagnose Schoenfeld proportionality tests,│
│              and remediate with stratification/splines.│
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Survival Analysis Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Data Audit** | Validate $(T, E)$ tuple and quantify right-censoring rate | Duration $T > 0$, Event $E \in \{0, 1\}$ | Censoring rate computed; zero row drops |
| **2. Nonparametric S(t)** | Fit Kaplan-Meier curves & run log-rank tests | $S(t)$ plot with 95% CIs | Log-rank p-value evaluated across groups |
| **3. Cox PH Modeling** | Fit semiparametric Cox regression via partial likelihood | Hazard Ratios $\exp(\beta)$, C-index | Table with $\text{HR}$, 95% CI, and C-index |
| **4. Proportionality Diagnostics** | Test scaled Schoenfeld residuals for slope trends | Grambsch-Therneau p-values | Violating covariates stratified / modeled |
| **5. Visual Brief & Checkpoint** | Generate interactive HTML brief and confirm plan | `%TEMP%\survival-analysis-*.html` | Dark-mode HTML delivered; checkpoint signed |

---

## Hazard Ratio & Diagnostic Interpretation Matrix

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                             HAZARD RATIO & DIAGNOSTICS                                   │
├─────────────────────────┬──────────────────────┬─────────────────────────────────────────┤
│ Metric / Test           │ Value / Condition    │ Scientific Interpretation & Action      │
├─────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Hazard Ratio exp(β)     │ HR < 1.0 (e.g. 0.68) │ Protective factor (32% hazard reduction)│
│                         │ HR > 1.0 (e.g. 1.10) │ Risk factor (10% higher instantaneous rate)│
│                         │ HR = 1.0             │ Null effect (β = 0)                     │
├─────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Concordance (C-index)   │ 0.50                 │ Random ranking equivalent (no skill)    │
│                         │ 0.60 – 0.75          │ Moderate discriminative power           │
│                         │ > 0.80               │ Strong discriminative ranking power     │
├─────────────────────────┼──────────────────────┼─────────────────────────────────────────┤
│ Schoenfeld Residuals    │ p ≥ 0.05             │ Proportionality assumption holds        │
│ (Grambsch & Therneau)   │ p < 0.05             │ Violation! Apply 3-tier remediation     │
└─────────────────────────┴──────────────────────┴─────────────────────────────────────────┘
```

---

## The 3-Tier Remediation Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SCHOENFELD VIOLATION REMEDIATION                     │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Stratification (`strata=["col"]`)                                    │
│    Use when covariate is a nuisance confounder and not the primary HR.  │
├─────────────────────────────────────────────────────────────────────────┤
│ 2. Functional Form Check (`col^2`, splines)                             │
│    Use when non-linearity in a continuous predictor mimics PH violation.│
├─────────────────────────────────────────────────────────────────────────┤
│ 3. Time-Varying Covariates (`CoxTimeVaryingFitter`, `β(t) = β0 + β1*t`) │
│    Use when the time trajectory of the effect is the target of inquiry. │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Anti-Patterns Cheat Sheet

- **Censoring Drop Bias**: Dropping non-event subjects from training matrices.
- **Linear Imputation**: Treating $(T, E)$ as single continuous regression target.
- **Unchecked Proportionality**: Quoting hazard ratios without Schoenfeld residual tests.
- **Probability-Hazard Conflation**: Treating instantaneous rate multiplier as cumulative probability difference.
- **Premature Parametrization**: Jumping directly to complex models without baseline Kaplan-Meier curves.

---

## Invariants & Guardrails

- [ ] **No Censored Rows Dropped**: All subjects with $E=0$ preserved in risk set.
- [ ] **Two-Column Target Present**: Target validated as $(T > 0, E \in \{0, 1\})$.
- [ ] **Kaplan-Meier Baseline First**: Nonparametric baseline established prior to Cox PH.
- [ ] **Schoenfeld Test Mandatory**: `check_assumptions()` executed on every fitted Cox model.
- [ ] **Visual Brief Written**: Self-contained HTML report generated in `%TEMP%`.
