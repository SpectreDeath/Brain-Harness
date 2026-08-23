---
name: survival-analysis
description: Estimate survival curves, evaluate right-censoring, fit Cox proportional hazards regression models, diagnose Schoenfeld residuals, and resolve non-proportional hazards using stratification or time-varying covariates. Use when the user asks to analyze time-to-event data, compute Kaplan-Meier curves, calculate hazard ratios, test proportional hazards assumptions, or run survival diagnostics.
---

# Survival Analysis & Cox Proportional Hazards Engine

The `survival-analysis` engine operationalizes rigorous time-to-event statistical methodology. It prevents common regression fallacies on censored datasets by enforcing nonparametric exploration (Kaplan-Meier), semiparametric risk modeling (Cox PH), and mandatory residual diagnostics (Schoenfeld tests) before reporting hazard ratios.

Every survival analysis workflow executes through this strict five-stage progression:

```
[1. Data Audit & Censoring Schema] → [2. Nonparametric Survival Estimation] → [3. Semiparametric Hazard Modeling] → [4. Proportionality Diagnostics & Remediation] → [5. Visual Brief & Checkpoint]
```

See [CARD.md](CARD.md) for the quick-reference cheat sheet, hazard ratio interpretation matrix, and invariant checklist.
Consult `/crafting-skills` for the foundational craft pillars and `/writing-for-agents` for cognitive hierarchy principles.

---

## Stage 1: Data Audit & Censoring Schema

Audit the dataset to ensure correct representation of time-to-event dynamics without dropping censored observations:

1. **Verify Target Tuples**: Extract two mandatory columns for every subject:
   - **Duration ($T$)**: Elapsed observation time until the event or study termination (e.g., `week`, `days`, `months`). Must be positive ($T > 0$).
   - **Event Indicator ($E$)**: Binary indicator where `1` = event occurred (re-arrest, death, failure, churn), `0` = censored (study ended, lost to follow-up, event not observed).
2. **Quantify Censoring Rate**: Calculate the censoring percentage ($1 - \frac{\sum E}{N}$). Reject any proposal to drop censored rows or impute fixed failure times for survivors.
3. **Inspect Covariate Matrix**: Standardize numerical features and encode categorical variables. Flag zero-variance columns or extreme collinearity.

> **Completion criterion**: Tabular dataset validated with positive duration column, binary event indicator, and computed baseline censoring rate.

---

## Stage 2: Nonparametric Survival Estimation (Kaplan-Meier & Log-Rank)

Estimate the empirical survival function $S(t) = P(T > t)$ without parametric shape assumptions before introducing covariates:

1. **Fit Kaplan-Meier Estimator**: Step forward through event times $t_i$, computing product-limit survival probabilities:
   ```python
   from lifelines import KaplanMeierFitter

   kmf = KaplanMeierFitter()
   kmf.fit(durations=df["duration"], event_observed=df["event"], label="Overall Cohort")
   ```
2. **Stratified Group Comparison**: Fit separate curves for key categorical factors (e.g., treatment vs. control):
   ```python
   for val, label in [(0, "Control"), (1, "Treatment")]:
       mask = df["treatment"] == val
       kmf.fit(df.loc[mask, "duration"], df.loc[mask, "event"], label=label)
   ```
3. **Execute Log-Rank Test**: Test the null hypothesis of equal survival curves between groups:
   ```python
   from lifelines.statistics import logrank_test

   res = logrank_test(
       durations_A=df.loc[df["treatment"] == 1, "duration"],
       durations_B=df.loc[df["treatment"] == 0, "duration"],
       event_observed_A=df.loc[df["treatment"] == 1, "event"],
       event_observed_B=df.loc[df["treatment"] == 0, "event"],
   )
   p_value = res.p_value
   ```

> **Completion criterion**: Kaplan-Meier survival curves plotted with 95% confidence bands; two-sample log-rank test statistic and p-value computed.

---

## Stage 3: Semiparametric Hazard Modeling (Cox PH & Hazard Ratios)

Model covariate effects on the instantaneous hazard rate $h(t | x) = h_0(t) \exp(\beta^T x)$ using partial likelihood without parameterizing the baseline hazard $h_0(t)$:

1. **Fit Cox Proportional Hazards Model**:
   ```python
   from lifelines import CoxPHFitter

   cph = CoxPHFitter()
   cph.fit(df, duration_col="duration", event_col="event")
   ```
2. **Ties Handling**: Utilize Efron's method (standard default) for tied event times.
3. **Extract & Interpret Hazard Ratios**:
   - Convert coefficients $\beta$ to hazard ratios $\text{HR} = \exp(\beta)$.
   - $\text{HR} < 1$: Protective factor (reduces hazard rate by $(1 - \text{HR}) \times 100\%$).
   - $\text{HR} > 1$: Risk factor (multiplies hazard rate by $\text{HR}$).
   - $\text{HR} = 1$: No effect ($\beta = 0$).
4. **Evaluate Discriminative Power**: Record the Concordance Index (C-index), measuring the probability that the model correctly ranks pairs of subjects by failure time ($0.5 = \text{random chance}$, $1.0 = \text{perfect ranking}$).

> **Completion criterion**: Cox model fitted; summary table generated with coefficients, Hazard Ratios $\exp(\beta)$, 95% confidence intervals, p-values, and model C-index.

---

## Stage 4: Proportionality Diagnostics & Remediation

Test the foundational assumption that hazard ratios remain constant over time ($h_i(t) / h_j(t) = \text{const}$):

1. **Run Schoenfeld Residuals Test**: Test for correlation between scaled Schoenfeld residuals and time for each covariate (Grambsch & Therneau test):
   ```python
   cph.check_assumptions(df, p_value_threshold=0.05, show_plots=False)
   ```
2. **Identify Violations**: Any covariate with $p < 0.05$ exhibits time-varying hazard ratios, violating proportionality.
3. **Apply the 3-Tier Remediation Strategy**:
   - **Path A — Stratification (`strata`)**: When the violating covariate is a nuisance control variable rather than a primary treatment of interest:
     ```python
     cph_strat = CoxPHFitter()
     cph_strat.fit(df, duration_col="duration", event_col="event", strata=["violating_covariate"])
     ```
   - **Path B — Time-Varying Covariate Interaction ($\beta(t)$)**: When the trajectory of the effect over time is the primary scientific target:
     Use `CoxTimeVaryingFitter` with segmented interval episodes to model $\beta(t) = \beta_0 + \beta_1 \cdot f(t)$.
   - **Path C — Non-Linear Functional Form Correction**: Check whether the violation is caused by covariate misspecification by testing polynomial terms ($x^2$) or splines before resorting to time-varying models.

> **Completion criterion**: Schoenfeld residual test executed across all covariates; any detected non-proportionality resolved via stratification, time-interaction, or functional form refinement.

---

## Stage 5: The Visual Survival Brief & Mandatory Checkpoint

Synthesize model parameters, survival trajectories, and diagnostic tests into an interactive HTML visual brief before final pipeline deployment:

1. **Target Path**: Write to `%TEMP%\survival-analysis-review-<timestamp>.html` (Windows) or `/tmp/survival-analysis-review-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Load Tailwind CSS and Mermaid.js via CDN in a sleek dark theme (`#0d1117`).
   - **Mermaid Lineage & Remediation Topology**: Diagram data flow from raw durations through Kaplan-Meier, Cox PH, Schoenfeld tests, and stratification decisions.
   - **Hazard Ratio Forest Table**: Render interactive cards displaying Hazard Ratios $\exp(\beta)$, 95% CIs, p-values, and proportionality status flags (`PROPORTIONAL` vs. `STRATIFIED`).
3. **Mandatory Checkpoint**:
   - Surface the absolute clickable HTML file path to the user.
   - Set `RequestFeedback: true` in `implementation_plan.md` before applying survival pipelines to production datasets or making downstream decisions.

```html
<!-- Location: %TEMP%\survival-analysis-review-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Survival Analysis & Cox PH Diagnostics Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans">
  <header class="border-b border-[#30363d] pb-4 mb-6">
    <h1 class="text-2xl font-bold text-white">Survival Analysis & Cox PH Brief</h1>
    <p class="text-sm text-gray-400 mt-1">Kaplan-Meier Estimation • Hazard Ratios • Schoenfeld Proportionality Diagnostics</p>
  </header>
  <!-- Interactive Forest Table & Diagnostic Topology -->
</body>
</html>
```

> **Completion criterion**: Interactive dark-mode HTML visual brief written to `%TEMP%` and delivered to user with verified verification receipt.

---

## Anti-Patterns

- **Censoring Drop Bias** — Dropping subjects who did not experience the event by study termination, inducing severe survivor selection bias.
- **Linear Regression Imputation** — Applying Ordinary Least Squares (OLS) to duration data by setting arbitrary values for censored individuals.
- **Unchecked Proportionality** — Reporting Cox regression hazard ratios without running Schoenfeld residual tests, ignoring time-decaying effects.
- **Probability-Hazard Conflation** — Misinterpreting a Hazard Ratio ($0.68$) as a direct difference in survival probability (e.g., "$32\%$ more survivors") rather than an instantaneous failure rate multiplier.
- **Premature Nonparametric Blindness** — Fitting complex multivariable regression models without first inspecting Kaplan-Meier survival curves and log-rank baselines.
