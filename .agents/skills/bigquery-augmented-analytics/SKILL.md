---
name: bigquery-augmented-analytics
description: Execute in-database augmented analytics in Google BigQuery using Table-Valued Functions (TVFs) for automated metric anomaly detection, multi-dimensional root-cause attribution, and ARIMA_PLUS counterfactual causal inference. Do not use for generic SQL CRUD or external pandas exports.
---

# BigQuery Augmented Analytics: In-Database Anomaly, Attribution & Causal Engine

`bigquery-augmented-analytics` is the autonomous data investigation engine that executes in-database AI, ML, and statistical inference directly inside Google BigQuery via Table-Valued Functions (TVFs). Based on the Google Cloud framework authored by Jenny Ortiz and Haoming Chen, this skill empowers agents to diagnose *why* business metrics change, detect structural step-level shifts, isolate high-dimensional segment drivers via Apriori rules, and quantify true causal lift against synthetic counterfactual baselines—all without exporting a single row of raw data.

Rather than succumbing to the **"Data Egress Tax"** (pulling millions of rows into local memory for pandas or R), this skill chains compact, expressive BigQuery TVFs where computation is pushed down directly into the distributed columnar storage engine.

```
[1. Temporal Profiling] ➔ [2. Shift Isolation] ➔ [3. Combinatorial Attribution] ➔ [4. Causal Lift] ➔ [5. Executive Synthesis]
  ML.TREND / SEASONALITY    ML.DETECT_CHANGE_POINTS    AI.KEY_DRIVERS / CORRELATION     AI.CAUSAL_EFFECT     Root-Cause Brief
```

See [CARD.md](CARD.md) for the companion summary card, TVF reference table, and verification checklist.
Consult [data-management-architect](../data-management-architect/SKILL.md) for data contracts and [deterministic-validation-loop](../deterministic-validation-loop/SKILL.md) for structured observation validation.

---

## 1. Temporal Profiling & Noise Stripping

Before diagnosing metric changes, decompose raw time-series into underlying structural trajectories and predictable cyclical rhythms. This prevents treating regular seasonal variations as structural anomalies.

1. **Trend Decomposition via `ML.TREND`**:
   - Strips high-frequency noise and transient spikes from the underlying growth or decline trajectory.
   - Example BigQuery SQL:
     ```sql
     WITH daily_metrics AS (
       SELECT
         DATE(timestamp) AS metric_date,
         COUNT(*) AS total_events
       FROM `bigquery-public-data.austin_bikeshare.bikeshare_trips`
       GROUP BY metric_date
     )
     SELECT *
     FROM ML.TREND(
       TABLE daily_metrics,
       data_col => 'total_events',
       timestamp_col => 'metric_date'
     )
     ORDER BY metric_date;
     ```
2. **Cyclical Periodicity Discovery via `ML.SEASONALITY`**:
   - Identifies recurring daily, weekly, monthly, and quarterly patterns across metric values.
   - Example BigQuery SQL:
     ```sql
     SELECT *
     FROM ML.SEASONALITY(
       TABLE daily_metrics,
       data_col => 'total_events',
       timestamp_col => 'metric_date',
       seasonalities => ['WEEKLY', 'MONTHLY']
     )
     ORDER BY metric_date;
     ```

> **Completion criterion**: Underlying trend direction separated from short-term noise; dominant recurring cycles documented; raw variance normalized against expected seasonality.

---

## 2. Structural Shift & Change-Point Isolation

Isolate the exact historical dates or intervals where a metric experienced a statistically significant, persistent regime shift rather than a transitory fluctuation.

1. **Step-Change Detection via `ML.DETECT_CHANGE_POINTS`**:
   - Employs scalable Bayesian change-point algorithms capable of evaluating millions of distinct time series in seconds.
   - Example BigQuery SQL:
     ```sql
     WITH baseline_series AS (
       SELECT
         DATE(start_time) AS trip_date,
         COUNT(*) AS daily_trips
       FROM `bigquery-public-data.austin_bikeshare.bikeshare_trips`
       GROUP BY trip_date
     )
     SELECT
       start_time,
       end_time,
       mean,
       variance,
       change_point_prob
     FROM ML.DETECT_CHANGE_POINTS(
       TABLE baseline_series,
       data_col => 'daily_trips',
       timestamp_col => 'trip_date'
     )
     WHERE change_point_prob >= 0.95
     ORDER BY start_time DESC;
     ```
2. **Dynamic Boundary Parameterization**:
   - Extract the primary shift timestamp ($t_0$) with the highest change probability or longest duration.
   - Designate the pre-shift interval ($t < t_0$) as the **Reference Group** and the post-shift interval ($t \ge t_0$) as the **Interest Group** for downstream TVF chaining.

> **Completion criterion**: Statistically significant change-point timestamp $t_0$ isolated with probability $\ge 95\%$; time horizons parameterized for attribution.

---

## 3. Combinatorial Attribution & Multi-Dimensional Slicing

Scan high-dimensional categorical features across millions of rows to explain the exact drivers of the metric variance between the reference and interest cohorts.

1. **Multi-Dimensional Driver Analysis via `AI.KEY_DRIVERS`**:
   - Uses Apriori association rule mining to identify combinations of dimensions (segments) that disproportionately explain the delta in metric volume.
   - Example BigQuery SQL:
     ```sql
     WITH cohort_partitioned AS (
       SELECT
         trip_id,
         subscriber_type,
         bike_type,
         start_station_name,
         end_station_name,
         (DATE(start_time) >= '2018-02-01') AS is_interest_period
       FROM `bigquery-public-data.austin_bikeshare.bikeshare_trips`
       WHERE DATE(start_time) BETWEEN '2017-09-01' AND '2018-06-30'
     )
     SELECT
       segment,
       metric_delta,
       percentage_change,
       segment_contribution
     FROM AI.KEY_DRIVERS(
       TABLE cohort_partitioned,
       metric_col => 'trip_id',
       dimension_cols => ['subscriber_type', 'bike_type', 'end_station_name'],
       interest_label_col => 'is_interest_period',
       min_apriori_support => 0.01,
       top_k => 20
     )
     ORDER BY segment_contribution DESC;
     ```
2. **Pairwise Metric Correlation via `ML.CORRELATION`**:
   - Evaluates directional strength between metric pairs across categorical dimensions to identify mediating mechanisms.
   - Example BigQuery SQL:
     ```sql
     SELECT
       segment,
       corr_col,
       correlation,
       segment_size
     FROM ML.CORRELATION(
       TABLE `bigquery-public-data.chicago_taxi_trips.taxi_trips`,
       target_col => 'trip_total',
       target_correlation_cols => ['trip_miles', 'trip_seconds'],
       dimension_cols => ['payment_type', 'company']
     )
     ORDER BY segment_size DESC;
     ```

> **Completion criterion**: Top contributing dimension segments identified; percentage lift and absolute contribution quantified; confounding sub-dimensions ranked.

---

## 4. Counterfactual Impact & Causal Lift Estimation

Differentiate between organic trajectory growth and the true return on investment (ROI) or causal impact of an intervention, policy change, or campaign launch.

1. **Synthetic Counterfactual Modeling via `AI.CAUSAL_EFFECT`**:
   - Builds an internal `ARIMA_PLUS` predictive model to project what the metric baseline would have been had the intervention never occurred.
   - Compares the observed trajectory against this synthetic control to isolate the true causal lift.
   - Example BigQuery SQL:
     ```sql
     WITH time_series_input AS (
       SELECT
         DATE(start_time) AS trip_date,
         COUNT(*) AS trip_count
       FROM `bigquery-public-data.austin_bikeshare.bikeshare_trips`
       WHERE DATE(start_time) BETWEEN '2017-01-01' AND '2018-12-31'
       GROUP BY trip_date
     )
     SELECT
       actual,
       counterfactual_baseline,
       absolute_effect,
       relative_effect,
       prob_causal_effect
     FROM AI.CAUSAL_EFFECT(
       TABLE time_series_input,
       data_col => 'trip_count',
       timestamp_col => 'trip_date',
       intervention_timestamp => '2018-02-01',
       output_time_series => FALSE
     );
     ```
2. **Time-Series Counterfactual Trajectory**:
   - When inspecting post-intervention divergence curves over time, set `output_time_series => TRUE` to extract daily confidence intervals (`lower_bound`, `upper_bound`).

> **Completion criterion**: True incremental lift and causal effect probability calculated; organic trend isolated from program impact.

---

## 5. Executive Diagnostic Synthesis & Delivery

Transform technical TVF outputs into actionable business diagnoses and decisions:

1. **Synthesize the 4-Point Diagnostic Narrative**:
   - **When**: Shift timestamp and persistence duration (from Stage 2).
   - **What**: Magnitude of change and decomposed trend slope (from Stage 1).
   - **Who/Where**: Disproportionate contributing segments and dimension combinations (from Stage 3).
   - **Impact**: True incremental causal lift over organic baseline (from Stage 4).
2. **Conversational Analytics Seam**:
   - Format results as deterministic Markdown tables and structured JSON observations for ReAct agent step consumption and conversational presentation.

> **Completion criterion**: Executive root-cause brief produced with verified TVF backing; recommendations grounded in causal evidence.

---

## Visual Brief Pillar

Before executing heavy or multi-stage TVF pipelines on large-scale datasets, agents must generate an interactive HTML Visual Brief to visually communicate query parameters, DAG execution sequences, and preliminary data topologies:

1. **Target File Location**:
   - Save to `%TEMP%\bigquery-augmented-analytics-<timestamp>.html` (Windows) or `/tmp/bigquery-augmented-analytics-<timestamp>.html` (Unix).
2. **Styling & Components**:
   - Dark theme (`#0d1117`) loading Tailwind CSS and Mermaid.js via CDN.
   - Render a **TVF Investigative Chaining DAG** showing the data flow from `ML.DETECT_CHANGE_POINTS` $\to$ `AI.KEY_DRIVERS` $\to$ `AI.CAUSAL_EFFECT`.
   - Render a **Cohort Partitioning Table** showing the reference vs interest definitions.
   - Render the **Diagnostic Evaluation Scorecard Table**.
3. **Delivery**:
   - Present the absolute, clickable HTML file path to the user.

---

## Mandatory Checkpoint Gate

To prevent excessive BigQuery slot consumption, unintended partition scans, or misconfigured multi-stage queries, agents must enforce a mandatory human-in-the-loop review gate:

1. Prior to executing write-intensive TVF queries or multi-million-row scans, present an `implementation_plan.md` artifact detailing:
   - Target dataset and table identifiers.
   - Incurred byte scan estimates and partition filters.
   - Formulated TVF chain parameters (`data_col`, `dimension_cols`, `min_apriori_support`).
   - Planned post-intervention horizon and confidence level.
2. Set `RequestFeedback: true` in artifact metadata.
3. **STOP and wait** for explicit user approval before triggering production TVF jobs.

---

## Programmatic IoC Service Seam (Rule 49)

Autonomous ReAct agent step loops and swarm workers dynamically resolve the BigQuery Augmented Analytics engine directly in-memory via the typed micro-kernel key:

```python
from harness.kernel.context import ServiceContext
from harness.services.bigquery_augmented_analytics import (
    BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY,
    BigQueryAugmentedAnalyticsService,
)

async def run_investigation(context: ServiceContext) -> None:
    bq_service: BigQueryAugmentedAnalyticsService = context.require(
        BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY
    )
    result = bq_service.run_investigation(
        target_table="bigquery-public-data.austin_bikeshare.bikeshare_trips",
        metric_col="trip_id",
        timestamp_col="start_time",
        dimension_cols=["subscriber_type", "bike_type"],
    )
    print("When:", result.narrative.when)
    print("Impact:", result.narrative.impact)
```

---

## Domain-Partitioned Plugin Tools (Rule 18 & Rule 45)

The co-located plugin in `plugins/data_engineering/bigquery_augmented_analytics/` exposes modular tool actions for ReAct agent step dispatch:

- `bigquery_temporal_profile`: Decomposes trend slope and weekly/monthly seasonality cycles via `ML.TREND` and `ML.SEASONALITY`.
- `bigquery_detect_change_points`: Isolates persistent structural regime shifts ($t_0$) with probability $\ge 0.95$ via `ML.DETECT_CHANGE_POINTS`.
- `bigquery_attribute_drivers`: Identifies high-dimensional Apriori segment rules explaining cohort deltas via `AI.KEY_DRIVERS`.
- `bigquery_causal_lift`: Estimates true incremental impact against synthetic counterfactual control via `AI.CAUSAL_EFFECT`.
- `bigquery_augmented_pipeline`: Orchestrates the complete 5-stage investigation end-to-end.
- `bigquery_visual_brief`: Renders a dark-theme interactive HTML visual brief with Tailwind CSS and Mermaid DAG topology.

---

## Headless Click CLI Seam (Rule 10 & Rule 6)

Developers, CI/CD verification runners, and headless agents can inspect and dry-run TVF compilation without cloud credentials via `harness bq` or `harness bigquery`:

```bash
# Compile and dry-run Stage 1 Temporal Profiling TVF SQL
harness bq profile --table austin_bikeshare.trips --data-col trip_id --timestamp-col start_time --dry-run

# Isolate structural regime shifts (probability >= 95%)
harness bq change-points --table austin_bikeshare.trips --data-col trip_id --timestamp-col start_time --min-prob 0.95

# Scan combinatorial Apriori driver segments
harness bq drivers --table austin_bikeshare.trips --metric-col trip_id --dims subscriber_type,bike_type --interest-cond "DATE(start_time) >= '2026-02-15'" --min-support 0.01

# Model synthetic counterfactual causal lift
harness bq causal --table austin_bikeshare.trips --data-col trip_id --timestamp-col start_time --intervention 2026-02-15

# Execute end-to-end 5-stage pipeline and generate visual brief
harness bq pipeline --table austin_bikeshare.trips --metric-col trip_id --timestamp-col start_time --dims subscriber_type,bike_type --dry-run --brief report.html
```

---

## Anti-Patterns

- **The Data Egress Tax** — Exporting millions of rows from BigQuery to local pandas or R memory instead of executing in-engine SQL TVFs.
- **Fluctuation Hallucination** — Mistaking recurring cyclical seasonality or random noise for structural change points without verifying via ML.TREND and ML.SEASONALITY.
- **Naive Pre/Post Attribution** — Attributing 100% of post-intervention delta to an event without estimating the ARIMA_PLUS counterfactual baseline.
- **Unparameterized Date Hardcoding** — Hardcoding arbitrary date cuts in AI.KEY_DRIVERS instead of chaining dynamic timestamps from ML.DETECT_CHANGE_POINTS.
- **Micro-Segment Noise Flooding** — Setting min_apriori_support to zero without pruning, leading to thousands of statistically insignificant micro-cohorts.
